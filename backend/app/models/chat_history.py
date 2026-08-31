from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class ChatHistory(Base):

    __tablename__ = "chat_history"


    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # =====================================================
    # USER
    # =====================================================

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )


    # =====================================================
    # USER MESSAGE
    # =====================================================

    message = Column(
        Text,
        nullable=False
    )


    # =====================================================
    # AI RESPONSE
    # =====================================================

    response = Column(
        Text,
        nullable=False
    )


    # =====================================================
    # CHAT TYPE
    # =====================================================

    type = Column(
        Text,
        nullable=False
    )


    # =====================================================
    # CREATED TIME
    # =====================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


    # =====================================================
    # USER RELATIONSHIP
    # =====================================================

    user = relationship(
        "User",
        back_populates="chat_history"
    )