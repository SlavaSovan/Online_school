from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from typing import Any, List, Optional
from app.utils.enums import CodeLanguage


class CodeTaskCreateSchema(BaseModel):
    language: CodeLanguage


class CodeTaskUpdateSchema(BaseModel):
    language: Optional[CodeLanguage] = None


class CodeTaskResponseSchema(BaseModel):
    id: int
    task_id: UUID
    language: CodeLanguage

    class Config:
        from_attributes = True


class CodeRunRequestSchema(BaseModel):
    """Схема для запроса на выполнение кода"""
    code: str = Field(..., max_length=10000)


class CodeRunResponseSchema(BaseModel):
    """Схема для ответа на выполнение кода"""

    success: bool
    output: str = Field(..., description="Вывод программы")
    error: Optional[str] = Field(None, description="Ошибка выполнения")
