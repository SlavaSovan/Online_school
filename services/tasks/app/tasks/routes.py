from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.tasks.schemas import (
    FileTaskCreateSchema,
    SandboxTaskCreateSchema,
    TaskUpdateSchema,
    TaskResponseSchema,
    TestTaskCreateSchema,
)
from app.tasks.services import TaskService

from app.utils.cache_decorator import invalidate_cache
from app.utils.permission_checker import (
    IsAuthenticated,
    IsMentor,
)

from app.utils.course_dependencies import (
    CheckMentorIsOwner,
    GetCourseInfoByLessonId,
    CheckUserEnrolledInCourse,
    GetLessonDetail,
    CheckMentorCourseAccess,
)

router = APIRouter(prefix="", tags=["Tasks"])


@router.get(
    "/courses/{course_slug}/modules/{module_slug}/lessons/{lesson_slug}/tasks",
    response_model=list[TaskResponseSchema],
    dependencies=[Depends(IsAuthenticated())],
)
async def get_tasks_by_lesson_id(
    course_slug: str,
    module_slug: str,
    lesson_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.user_data
    user_role = user.get("role", {}).get("name")

    if user_role == "mentor":
        await CheckMentorCourseAccess(course_slug=course_slug)(request)
    else:
        await CheckUserEnrolledInCourse(course_slug=course_slug)(request)

    lesson_detail = await GetLessonDetail(course_slug, module_slug, lesson_slug)(
        request
    )

    tasks = await TaskService.get_by_lesson_id(db, lesson_detail["id"])

    return tasks


@router.post(
    "/courses/{course_slug}/modules/{module_slug}/lessons/{lesson_slug}/tasks/test",
    response_model=TaskResponseSchema,
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=["task:{id}", "tasks:lesson:{lesson_id}"],
    extract_from_result=["id", "lesson_id"],
)
async def create_test_task(
    payload: TestTaskCreateSchema,
    request: Request,
    course_slug: str,
    module_slug: str,
    lesson_slug: str,
    db: AsyncSession = Depends(get_db),
):
    await CheckMentorIsOwner(course_slug=course_slug)(request)
    lesson_detail = await GetLessonDetail(course_slug, module_slug, lesson_slug)(
        request
    )

    return await TaskService.create_test_task(db, payload, lesson_detail["id"])


@router.post(
    "/courses/{course_slug}/modules/{module_slug}/lessons/{lesson_slug}/tasks/sandbox",
    response_model=TaskResponseSchema,
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=["task:{id}", "tasks:lesson:{lesson_id}"],
    extract_from_result=["id", "lesson_id"],
)
async def create_sandbox_task(
    payload: SandboxTaskCreateSchema,
    request: Request,
    course_slug: str,
    module_slug: str,
    lesson_slug: str,
    db: AsyncSession = Depends(get_db),
):
    await CheckMentorIsOwner(course_slug=course_slug)(request)
    lesson_detail = await GetLessonDetail(course_slug, module_slug, lesson_slug)(
        request
    )

    return await TaskService.create_sandbox_task(db, payload, lesson_detail["id"])


@router.post(
    "/courses/{course_slug}/modules/{module_slug}/lessons/{lesson_slug}/tasks/file",
    response_model=TaskResponseSchema,
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=["task:{id}", "tasks:lesson:{lesson_id}"],
    extract_from_result=["id", "lesson_id"],
)
async def create_file_task(
    payload: FileTaskCreateSchema,
    request: Request,
    course_slug: str,
    module_slug: str,
    lesson_slug: str,
    db: AsyncSession = Depends(get_db),
):
    await CheckMentorIsOwner(course_slug=course_slug)(request)
    lesson_detail = await GetLessonDetail(course_slug, module_slug, lesson_slug)(
        request
    )

    return await TaskService.create_file_task(db, payload, lesson_detail["id"])


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponseSchema,
    dependencies=[Depends(IsAuthenticated())],
)
async def get_task(
    task_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    task = await TaskService.get_by_id(db, task_id)

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["slug"])(request)
    return task


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponseSchema,
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=["task:{id}", "tasks:lesson:{lesson_id}"],
    extract_from_result=["id", "lesson_id"],
)
async def update_task(
    task_id: UUID,
    payload: TaskUpdateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    task = await TaskService.get_by_id(db, task_id)

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckMentorIsOwner(course_slug=course_info["slug"])(request)

    return await TaskService.update(db, task_id, payload)


@router.delete(
    "/tasks/{task_id}",
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=["task:{task_id}"],
    before_call=True,
)
async def delete_task(
    task_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    task = await TaskService.get_by_id(db, task_id)

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckMentorIsOwner(course_slug=course_info["slug"])(request)

    await TaskService.delete(db, task_id)

    return {"status": "deleted"}
