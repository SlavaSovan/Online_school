from datetime import datetime
from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
from app.utils.enums import TaskType, CodeLanguage


class TaskCreateSchema(BaseModel):
    title: str
    description: str
    order: int = 0


class TestTaskCreateSchema(TaskCreateSchema):
    max_attempts: int = 0
    max_score: int = 5

    @field_validator("max_attempts")
    @classmethod
    def validate_max_attempts(cls, v: int) -> int:
        """max_attempts не может быть отрицательным"""
        if v < 0:
            raise ValueError("max_attempts cannot be negative")
        return v

    @field_validator("max_score")
    @classmethod
    def validate_max_score(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_score must be greater than 0")
        return v


class SandboxTaskCreateSchema(TaskCreateSchema):
    max_attempts: int = 0
    max_score: int = 5
    language: str

    @field_validator("max_attempts")
    @classmethod
    def validate_max_attempts(cls, v: int) -> int:
        if v < 0:
            raise ValueError("max_attempts cannot be negative")
        return v

    @field_validator("max_score")
    @classmethod
    def validate_max_score(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_score must be greater than 0")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        supported = [lang.value for lang in CodeLanguage]
        if v.lower() not in supported:
            raise ValueError(f"Language {v} not supported.")
        return v.lower()


class FileTaskCreateSchema(TaskCreateSchema):
    max_attempts: int = 0
    max_score: int = 5

    @field_validator("max_attempts")
    @classmethod
    def validate_max_attempts(cls, v: int) -> int:
        if v < 0:
            raise ValueError("max_attempts cannot be negative")
        return v

    @field_validator("max_score")
    @classmethod
    def validate_max_score(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_score must be greater than 0")
        return v


class TestTaskCreateByAdminSchema(TestTaskCreateSchema):
    lesson_id: int


class SandboxTaskCreateByAdminSchema(SandboxTaskCreateSchema):
    lesson_id: int


class FileTaskCreateByAdminSchema(FileTaskCreateSchema):
    lesson_id: int


class TaskUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None
    max_attempts: Optional[int] = None
    max_score: Optional[int] = None

    @field_validator("max_attempts")
    @classmethod
    def validate_max_attempts(cls, v: Optional[int], info) -> Optional[int]:
        """Валидация количества попыток при обновлении"""
        if v is not None and v < 0:
            raise ValueError("max_attempts cannot be negative")
        return v

    @field_validator("max_score")
    @classmethod
    def validate_max_score(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("max_score must be greater than 0")
        return v


class TaskResponseSchema(BaseModel):
    id: UUID
    lesson_id: int
    title: str
    description: str
    task_type: TaskType
    order: int
    is_active: bool
    max_attempts: int
    max_score: int

    class Config:
        from_attributes = True


class TaskReadSchema(BaseModel):
    id: UUID
    lesson_id: int
    title: str
    description: str
    task_type: TaskType
    order: int
    is_active: bool
    max_attempts: int
    max_score: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
