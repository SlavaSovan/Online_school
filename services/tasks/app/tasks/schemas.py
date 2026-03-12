from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from app.utils.enums import TaskType


class TaskCreateSchema(BaseModel):
    title: str
    description: str
    task_type: TaskType
    order: int = 0
    max_attempts: int = 1


class TaskCreateByAdminSchema(TaskCreateSchema):
    lesson_id: int


class TaskUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None
    max_attempts: Optional[int] = None


class TaskResponseSchema(BaseModel):
    id: UUID
    lesson_id: int
    title: str
    description: str
    task_type: TaskType
    order: int
    is_active: bool
    max_attempts: int

    class Config:
        from_attributes = True
