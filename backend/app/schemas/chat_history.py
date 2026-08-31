from datetime import datetime
from pydantic import BaseModel


class ChatHistoryResponse(BaseModel):

    id: int
    message: str
    response: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True