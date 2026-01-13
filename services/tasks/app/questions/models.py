from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))

    text: Mapped[str] = mapped_column(String)
    order: Mapped[int] = mapped_column(Integer, default=0)

    task = relationship("Task", back_populates="questions")
    options = relationship(
        "AnswerOption", back_populates="question", cascade="all, delete"
    )


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )

    text: Mapped[str] = mapped_column(String)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    question = relationship("Question", back_populates="options")
