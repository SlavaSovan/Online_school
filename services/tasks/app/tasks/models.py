import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Boolean, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import TaskType


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lesson_id: Mapped[int] = mapped_column(index=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)

    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType))
    order: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    max_attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=5)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    questions = relationship(
        "Question",
        back_populates="task",
        cascade="all, delete",
    )
    submissions = relationship(
        "Submission",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    code_task = relationship(
        "CodeTask",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        """Конвертация объекта в словарь"""
        return {
            "id": str(self.id),
            "lesson_id": self.lesson_id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.value if self.task_type else None,
            "order": self.order,
            "is_active": self.is_active,
            "max_attempts": self.max_attempts,
            "max_score": self.max_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
