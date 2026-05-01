from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)

    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, index=True
    )

    mentor_id: Mapped[int] = mapped_column(index=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    score: Mapped[int] = mapped_column(Integer)

    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    submission = relationship("Submission", back_populates="review")

    def to_dict(self) -> dict:
        """Конвертация объекта в словарь"""
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "mentor_id": self.mentor_id,
            "score": self.score,
            "comment": self.comment,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
