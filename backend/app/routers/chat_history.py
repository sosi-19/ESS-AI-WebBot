from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.chat_history import ChatHistory
from app.schemas.chat_history import ChatHistoryResponse


router = APIRouter(
    prefix="/chat",
    tags=["Chat History"]
)


@router.get(
    "/history",
    response_model=list[ChatHistoryResponse]
)
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    history = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == current_user.id
        )
        .order_by(
            ChatHistory.created_at.desc()
        )
        .all()
    )

    return history