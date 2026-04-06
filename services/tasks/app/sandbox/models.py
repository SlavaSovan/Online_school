from uuid import UUID
from sqlalchemy import JSON, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import CodeLanguage


class CodeTask(Base):
    __tablename__ = "code_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), unique=True, index=True
    )
    language: Mapped[CodeLanguage] = mapped_column(String(20))

    task = relationship("Task", back_populates="code_task")