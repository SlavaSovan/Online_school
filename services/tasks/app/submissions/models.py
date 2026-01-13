from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import SubmissionStatus


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[int] = mapped_column(index=True)

    answer_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    answer_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus), default=SubmissionStatus.PENDING
    )

    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    task = relationship("Task", back_populates="submissions")
    review = relationship("Review", uselist=False, back_populates="submission")
