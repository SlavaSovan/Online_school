import uuid
from sqlalchemy import JSON, Enum, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.enums import QuestionType


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )

    text: Mapped[str] = mapped_column(String)
    order: Mapped[int] = mapped_column(Integer, default=0, index=True)

    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType))

    correct_answers: Mapped[list] = mapped_column(JSON, default=list)

    task = relationship("Task", back_populates="questions")
    options = relationship(
        "AnswerOption", back_populates="question", cascade="all, delete"
    )

    def to_dict(self, include_options: bool = True) -> dict:
        """Конвертация объекта в словарь"""
        data = {
            "id": self.id,
            "task_id": str(self.task_id),
            "text": self.text,
            "order": self.order,
            "question_type": self.question_type.value if self.question_type else None,
            "correct_answers": self.correct_answers,
        }

        if include_options and hasattr(self, "options"):
            data["options"] = (
                [opt.to_dict() for opt in self.options] if self.options else []
            )

        return data


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
    )

    text: Mapped[str] = mapped_column(String)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    question = relationship("Question", back_populates="options")

    def to_dict(self) -> dict:
        """Конвертация объекта в словарь"""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "text": self.text,
            "is_correct": self.is_correct,
        }
