from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.tasks.services import TaskService
from app.utils.course_dependencies import (
    CheckMentorCourseAccess,
    CheckUserEnrolledInCourse,
    GetCourseInfoByLessonId,
)
from app.utils.enums import TaskType
from app.utils.permission_checker import IsAuthenticated
from app.sandbox.services import SandboxService
from app.sandbox.schemas import (
    CodeRunRequestSchema,
    CodeRunResponseSchema,
)

router = APIRouter(
    prefix="/tasks/{task_id}/sandbox",
    tags=["Sandbox"],
    dependencies=[Depends(IsAuthenticated())],
)


@router.post(
    "/run",
    response_model=CodeRunResponseSchema,
)
async def run_code(
    task_id: UUID,
    payload: CodeRunRequestSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Запуск кода для проверки (без сохранения).
    """
    task = await TaskService.get_by_id(db, task_id, as_orm=True)

    if task.task_type != TaskType.SANDBOX:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not a SANDBOX task.",
        )

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)

    user = request.state.user_data
    user_id = user["id"]
    user_role = user.get("role", {}).get("name")

    if user_role == "mentor":
        await CheckMentorCourseAccess(course_slug=course_info["slug"])(request)
    else:
        await CheckUserEnrolledInCourse(course_slug=course_info["slug"])(request)

    from app.submissions.services import SubmissionService

    task_state = await SubmissionService.get_task_state(
        db=db,
        user_id=user_id,
        task_id=task_id,
    )

    if task_state.last_submission and task_state.last_submission.status == "passed":
        raise HTTPException(
            status_code=403,
            detail="Task already passed. Cannot run code.",
        )

    code_task = await SandboxService.get_code_task(db, task_id)

    return await SandboxService.execute_code(
        code=payload.code,
        language=code_task.language,
    )
