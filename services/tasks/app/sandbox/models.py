from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import CodeLanguage


class CodeTask(Base):
    __tablename__ = "code_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), unique=True
    )

    language: Mapped[CodeLanguage] = mapped_column(String(20))
    template_code: Mapped[str] = mapped_column(String)
    tests_definition: Mapped[str] = mapped_column(String)

    time_limit: Mapped[int] = mapped_column(default=2)      # seconds
    memory_limit: Mapped[int] = mapped_column(default=256)  # MB

    task = relationship("Task", back_populates="code_task")