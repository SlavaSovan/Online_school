from uuid import UUID
from pydantic import BaseModel, model_validator
from typing import List, Optional
from app.utils.enums import QuestionType
from app.questions.models import Question


class AnswerOptionCreateSchema(BaseModel):
    text: str
    is_correct: bool = False


class AnswerOptionResponseSchema(BaseModel):
    id: int
    text: str
    is_correct: bool

    class Config:
        from_attributes = True


class AnswerOptionStudentSchema(BaseModel):
    """Схема для ответа с вариантом ответа (для студента, без правильных ответов)"""

    id: int
    text: str

    class Config:
        from_attributes = True


class QuestionCreateSchema(BaseModel):
    text: str
    order: int = 0
    question_type: QuestionType
    options: Optional[List[AnswerOptionCreateSchema]] = None
    correct_answers: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_question_data(self) -> "QuestionCreateSchema":
        """
        Валидация данных вопроса после создания объекта.
        Проверяет наличие опций для вопросов с выбором ответа
        и наличие правильных ответов для текстовых вопросов.
        """
        # Валидация для вопросов с выбором ответа (SINGLE_CHOICE, MULTIPLE_CHOICE)
        if self.question_type in [
            QuestionType.SINGLE_CHOICE,
            QuestionType.MULTIPLE_CHOICE,
        ]:
            if not self.options or len(self.options) == 0:
                raise ValueError(
                    f"Options are required for {self.question_type.value} questions"
                )

            # Дополнительная валидация для SINGLE_CHOICE
            if self.question_type == QuestionType.SINGLE_CHOICE:
                correct_count = sum(1 for opt in self.options if opt.is_correct)
                if correct_count != 1:
                    raise ValueError(
                        "SINGLE_CHOICE questions must have exactly one correct option"
                    )

        # Валидация для текстовых ответов (SHORT_ANSWER)
        if self.question_type == QuestionType.SHORT_ANSWER:
            if not self.correct_answers or len(self.correct_answers) == 0:
                raise ValueError(
                    "Correct answers are required for SHORT_ANSWER type questions"
                )

        return self


class QuestionCreateByAdminSchema(QuestionCreateSchema):
    task_id: UUID


class QuestionUpdateSchema(BaseModel):
    text: Optional[str] = None
    order: Optional[int] = None
    options: Optional[List[AnswerOptionCreateSchema]] = None
    correct_answers: Optional[List[str]] = None


class QuestionResponseSchema(BaseModel):
    id: int
    task_id: UUID
    text: str
    order: int
    question_type: QuestionType

    options: Optional[List[AnswerOptionResponseSchema]]
    correct_answers: Optional[List[str]]

    class Config:
        from_attributes = True


class QuestionStudentSchema(BaseModel):
    """Схема для ответа с вопросом (для студента, без правильных ответов)"""

    id: int
    text: str
    order: int
    question_type: QuestionType
    options: Optional[List[AnswerOptionStudentSchema]] = None
    # correct_answers скрыт для студента
    # is_correct в options скрыт для студента

    class Config:
        from_attributes = True

    @classmethod
    def from_question(cls, question: Question) -> "QuestionStudentSchema":
        """Создание студенческой схемы из ORM объекта"""
        options = None
        if hasattr(question, "options") and question.options:
            # Убираем поле is_correct для студента
            options = [
                AnswerOptionStudentSchema(id=opt.id, text=opt.text)
                for opt in question.options
            ]

        return cls(
            id=question.id,
            text=question.text,
            order=question.order,
            question_type=question.question_type,
            options=options,
        )
