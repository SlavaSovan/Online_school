from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, Integer, Boolean, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import TaskType


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(index=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)

    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType))
    order: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    questions = relationship("Question", back_populates="task", cascade="all, delete")
    submissions = relationship("Submission", back_populates="task")
    code_task = relationship("CodeTask", uselist=False, back_populates="task")
    auto_check_rule = relationship(
        "AutoCheckRule", uselist=False, back_populates="task"
    )


class AutoCheckRule(Base):
    __tablename__ = "auto_check_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), unique=True
    )

    expected_answer: Mapped[str] = mapped_column(String)
    comparison_type: Mapped[str] = mapped_column(String(20))  # exact / contains / regex

    task = relationship("Task", back_populates="auto_check_rule")
