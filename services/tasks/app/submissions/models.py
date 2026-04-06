from datetime import datetime
import uuid
from sqlalchemy import JSON, DateTime, ForeignKey, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import SubmissionStatus


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(index=True, nullable=False)
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attempt: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus),
        default=SubmissionStatus.NEEDS_REVIEW,
        nullable=False,
        index=True,
    )

    score: Mapped[int] = mapped_column(nullable=True)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    feedback: Mapped[dict] = mapped_column(JSON, nullable=True)

    s3_file_key: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    task = relationship("Task", back_populates="submissions")
    review = relationship("Review", uselist=False, back_populates="submission")

    def to_dict(self) -> dict:
        """Конвертация объекта в словарь"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": str(self.task_id),
            "attempt": self.attempt,
            "status": self.status.value if self.status else None,
            "score": self.score,
            "max_score": self.max_score,
            "payload": self.payload,
            "feedback": self.feedback,
            "s3_file_key": self.s3_file_key,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if hasattr(self, "review") and self.review:
            data["review"] = self.review.to_dict()

        return data
