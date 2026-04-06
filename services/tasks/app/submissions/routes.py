from uuid import UUID
from fastapi import APIRouter, Depends, File, Request, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.tasks.services import TaskService
from app.utils.cache_decorator import invalidate_cache
from app.utils.course_dependencies import (
    CheckUserEnrolledInCourse,
    GetCourseInfoByLessonId,
)
from app.utils.permission_checker import IsAuthenticated

from app.submissions.schemas import (
    FileDownloadResponse,
    SubmissionResponseSchema,
    SubmissionTaskStateSchema,
)
from app.submissions.services import SubmissionService
from app.submissions.schemas_payload import (
    SandboxSubmissionPayload,
    TestSubmissionPayload,
)


router = APIRouter(prefix="", tags=["Submissions"])


@router.post(
    "/tasks/{task_id}/submit/test",
    response_model=SubmissionResponseSchema,
    dependencies=[Depends(IsAuthenticated())],
)
@invalidate_cache(
    keys=["submissions:user:{user_id}:task:{task_id}", "submissions:*"],
    extract_user_from_request=True,
)
async def submit_test_task(
    task_id: UUID,
    payload: TestSubmissionPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Создание отправки для ТЕСТОВОГО задания.

    Ожидается payload:
    {
        "answers": {
            "1": ["option_id_1"],
            "2": ["answer_text"]
        }
    }
    """
    task = await TaskService.get_by_id(db, task_id)

    # Проверка прав доступа
    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data

    return await SubmissionService.create_test_submission(
        db=db,
        user_id=user["id"],
        task_id=task_id,
        payload=payload,
    )


@router.post(
    "/tasks/{task_id}/submit/sandbox",
    response_model=SubmissionResponseSchema,
    dependencies=[Depends(IsAuthenticated())],
)
@invalidate_cache(
    keys=["submissions:user:{user_id}:task:{task_id}", "submissions:*"],
    extract_user_from_request=True,
)
async def submit_sandbox_task(
    task_id: UUID,
    payload: SandboxSubmissionPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Создание отправки для ЗАДАНИЯ С КОДОМ.
    """
    task = await TaskService.get_by_id(db, task_id)
    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data

    return await SubmissionService.create_sandbox_submission(
        db=db,
        user_id=user["id"],
        task_id=task_id,
        payload=payload,
    )


@router.post(
    "/tasks/{task_id}/submit/file",
    response_model=SubmissionResponseSchema,
    dependencies=[Depends(IsAuthenticated())],
)
@invalidate_cache(
    keys=["submissions:user:{user_id}:task:{task_id}", "submissions:*"],
    extract_user_from_request=True,
)
async def submit_file_task(
    task_id: UUID,
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Создание отправки для файлового задания.
    Загружает файл в S3 и создаёт отправку.
    """
    task = await TaskService.get_by_id(db, task_id)

    # Проверка прав доступа
    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data

    return await SubmissionService.create_file_submission(
        db=db,
        user_id=user["id"],
        task_id=task_id,
        file=file,
    )


@router.get(
    "/tasks/{task_id}/submissions/{submission_id}/download",
    response_model=FileDownloadResponse,
    dependencies=[Depends(IsAuthenticated())],
)
async def download_submission_file(
    task_id: UUID,
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Получение временной ссылки для скачивания файла"""
    # Проверяем доступ к задаче
    task = await TaskService.get_by_id(db, task_id)
    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data

    return await SubmissionService.get_download_url(
        db=db,
        submission_id=submission_id,
        user_id=user["id"],
        is_admin=False,
    )


@router.delete(
    "/tasks/{task_id}/submissions/{submission_id}",
    dependencies=[Depends(IsAuthenticated())],
)
@invalidate_cache(
    keys=["submission:{submission_id}", "submissions:user:*:task:{task_id}"],
    before_call=True,
)
async def delete_submission(
    task_id: UUID,
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Удаление отправки (только для необработанных файловых отправок)
    """
    task = await TaskService.get_by_id(db, task_id)

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data

    # Проверяем, что отправка принадлежит пользователю
    submission = await SubmissionService.get_by_id_and_task_id(
        db, submission_id, task_id
    )
    if submission.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    await SubmissionService.delete_file_submission(db, submission)
    return {"status": "deleted"}


@router.get(
    "/tasks/{task_id}/state",
    response_model=SubmissionTaskStateSchema,
    dependencies=[Depends(IsAuthenticated())],
)
async def get_task_state(
    task_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Получение состояния задачи для текущего пользователя"""
    task = await TaskService.get_by_id(db, task_id)

    # Проверка прав доступа
    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data

    return await SubmissionService.get_task_state(
        db=db,
        user_id=user["id"],
        task_id=task_id,
    )


@router.get(
    "/tasks/{task_id}/submissions",
    response_model=list[SubmissionResponseSchema],
    dependencies=[Depends(IsAuthenticated())],
)
async def get_user_submissions(
    task_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Получение всех отправок пользователя для задачи"""
    task = await TaskService.get_by_id(db, task_id)

    # Проверка прав доступа
    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data

    return await SubmissionService.get_user_submissions_for_task(
        db=db,
        user_id=user["id"],
        task_id=task_id,
    )
