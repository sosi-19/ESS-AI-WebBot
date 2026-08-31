from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class User(Base):

    __tablename__ = "users"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    full_name = Column(
        String(100),
        nullable=False
    )


    email = Column(
        String(100),
        unique=True,
        nullable=False
    )


    # store encrypted password hash, not the real password
    hashed_password = Column(
        String(255),
        nullable=False
    )


    role = Column(
        String(20),
        default="user"
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


    chat_history = relationship(
        "ChatHistory",
        back_populates="user",
        cascade="all, delete"
    )