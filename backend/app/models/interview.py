from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List

from app.models.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_name: Mapped[str] = mapped_column(
        String(100)
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    messages: Mapped[List["InterviewMessage"]] = relationship(
        "InterviewMessage",
        back_populates="session",
        cascade="all, delete-orphan"
    )


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interview_sessions.id")
    )

    role: Mapped[str] = mapped_column(
        String(20)  # "assistant" or "user"
    )

    content: Mapped[str] = mapped_column(
        String
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession",
        back_populates="messages"
    )