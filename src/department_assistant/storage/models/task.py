from sqlalchemy import Integer, Text, String, DateTime, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .base import Base

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assignees: Mapped[str] = mapped_column(Text, nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_completed: Mapped[bool] = mapped_column(default=False)
    # Меняем тип на BigInteger
    chat_id: Mapped[int] = mapped_column(BigInteger)