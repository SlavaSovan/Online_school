from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.tasks.models import Task
from app.tasks.services import TaskService

from app.utils.course_dependencies import CheckMentorIsOwner, GetCourseInfoByLessonId
from app.utils.enums import TaskType
from app.utils.permission_checker import IsMentor

from app.sandbox.schemas import (
    CodeTaskCreateSchema,
    CodeTaskUpdateSchema,
    CodeTaskResponseSchema,
)
from app.sandbox.models import CodeTask
from app.sandbox.services import SandboxService

router = APIRouter(
    prefix="/tasks/{task_id}/sandbox",
    tags=["Sandbox"],
    dependencies=[Depends(IsMentor())],
)


async def validate_sandbox_task_access(
    db: AsyncSession,
    task_id: UUID,
    request: Request,
) -> Task:
    """Проверка доступа к задаче типа SANDBOX"""

    task = await TaskService.get_by_id(db, task_id)

    if task.task_type != TaskType.SANDBOX:
        raise HTTPException(status_code=400, detail="Task is not a SANDBOX task")

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckMentorIsOwner(course_slug=course_info["course_slug"])(request)

    return task


@router.post("/code-tasks/", response_model=CodeTaskResponseSchema)
async def create_code_task(
    task_id: UUID,
    payload: CodeTaskCreateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await validate_sandbox_task_access(db, task_id, request)

    return await SandboxService.create_code_task(
        db=db,
        task_id=task_id,
        language=payload.language,
        template_code=payload.template_code,
        tests_definition=payload.tests_definition.model_dump(),
        time_limit=payload.time_limit,
        memory_limit=payload.memory_limit,
    )


@router.patch("/code-tasks/{code_task_id}/", response_model=CodeTaskResponseSchema)
async def update_code_task(
    task_id: UUID,
    code_task_id: int,
    payload: CodeTaskUpdateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await validate_sandbox_task_access(db, task_id, request)

    data = payload.model_dump(exclude_unset=True)
    return await SandboxService.update_code_task(db, code_task_id, task_id, data)


@router.delete("/code-tasks/{code_task_id}/", response_model=CodeTaskResponseSchema)
async def update_code_task(
    task_id: UUID,
    code_task_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await validate_sandbox_task_access(db, task_id, request)

    await SandboxService.delete_code_task(db, code_task_id, task_id)
    return {"status": "deleted"}
