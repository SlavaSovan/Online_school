from uuid import UUID
from pydantic import BaseModel, Field
from typing import Any, List, Optional
from app.utils.enums import CodeLanguage


class TestCaseSchema(BaseModel):
    input: List[Any]
    expected: Any


class TestsDefinitionSchema(BaseModel):
    function_name: str = Field(..., min_length=1, max_length=50)
    tests: List[TestCaseSchema] = Field(..., min_items=1, max_items=50)


class CodeTaskCreateSchema(BaseModel):
    task_id: UUID
    language: CodeLanguage
    template_code: str = Field(..., max_length=10000)
    tests_definition: TestsDefinitionSchema
    time_limit: int = Field(2, ge=1, le=30)
    memory_limit: int = Field(256, ge=64, le=1024)


class CodeTaskUpdateSchema(BaseModel):
    template_code: Optional[str] = Field(None, max_length=10000)
    tests_definition: Optional[TestsDefinitionSchema] = None
    time_limit: Optional[int] = Field(None, ge=1, le=30)
    memory_limit: Optional[int] = Field(None, ge=64, le=1024)


class CodeTaskResponseSchema(BaseModel):
    id: int
    task_id: UUID
    language: CodeLanguage
    template_code: str
    time_limit: int
    memory_limit: int

    class Config:
        from_attributes = True
