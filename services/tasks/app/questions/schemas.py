from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from app.utils.enums import QuestionType


class AnswerOptionCreateSchema(BaseModel):
    text: str
    is_correct: bool = False


class AnswerOptionResponseSchema(BaseModel):
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

    @field_validator("options")
    def validate_options_by_type(cls, v, values):
        if "question_type" in values:
            question_type = values["question_type"]
            if question_type in [
                QuestionType.SINGLE_CHOICE,
                QuestionType.MULTIPLE_CHOICE,
            ]:
                if not v or len(v) == 0:
                    raise ValueError(f"Options are required for {question_type}")
        return v

    @field_validator("correct_answers")
    def validate_correct_answers_by_type(cls, v, values):
        if "question_type" in values:
            question_type = values["question_type"]
            if question_type == QuestionType.SHORT_ANSWER and (not v or len(v) == 0):
                raise ValueError("Correct answers are required for SHORT_ANSWER type")
        return v


class QuestionCreateByAdminSchema(QuestionCreateSchema):
    task_id: str


class QuestionUpdateSchema(BaseModel):
    text: Optional[str] = None
    order: Optional[int] = None
    options: Optional[List[AnswerOptionCreateSchema]] = None
    correct_answers: Optional[List[str]] = None


class QuestionResponseSchema(BaseModel):
    id: int
    text: str
    order: int
    question_type: QuestionType

    options: Optional[List[AnswerOptionResponseSchema]]
    correct_answers: Optional[List[str]]

    class Config:
        from_attributes = True
