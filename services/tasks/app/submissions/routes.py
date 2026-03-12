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
    SubmissionCreateSchema,
    SubmissionResponseSchema,
)
from app.submissions.services import SubmissionService
from app.submissions.file_service import submission_file_service


router = APIRouter(prefix="", tags=["Submissions"])


@router.post(
    "/tasks/{task_id}/submit/file/",
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
    """Создание отправки с файлом"""

    task = await TaskService.get_by_id(db, task_id)

    if task.task_type != "FILE":
        raise HTTPException(
            status_code=400, detail="File upload is only allowed for FILE tasks"
        )

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data

    submission = await submission_file_service.create_submission_with_file(
        db=db, user_id=user["id"], task_id=task_id, file=file
    )
    return submission


@router.get(
    "/tasks/{task_id}/submissions/{submission_id}/download/",
    response_model=FileDownloadResponse,
    dependencies=[Depends(IsAuthenticated())],
)
async def download_submission_file(
    submission_id: int,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Получение временной ссылки для скачивания файла"""

    user = request.state.user_data

    download_info = await submission_file_service.get_download_url(
        submission_id=submission_id, db=db, user_id=user["id"], is_admin=False
    )

    return download_info


@router.delete(
    "/tasks/{task_id}/submissions/{submission_id}/file/",
    dependencies=[Depends(IsAuthenticated())],
)
@invalidate_cache(
    keys=["submission:{submission_id}", "submissions:user:*:task:{task_id}"],
    before_call=True,
)
async def delete_file_submission(
    task_id: UUID,
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):

    task = await TaskService.get_by_id(db, task_id)

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data

    submission = await SubmissionService.get_by_id_and_task_id(
        db, submission_id, task_id
    )

    if submission.user_id != user["id"]:
        HTTPException(status_code=404, detail="Submission not found")

    await SubmissionService.delete_file_submission(db, submission)
    return {"status": "deleted"}


@router.post(
    "/tasks/{task_id}/submit/",
    response_model=SubmissionResponseSchema,
    dependencies=[Depends(IsAuthenticated())],
)
@invalidate_cache(
    keys=["submissions:user:{user_id}:task:{task_id}", "submissions:*"],
    extract_user_from_request=True,
)
async def submit_task(
    task_id: UUID,
    payload: SubmissionCreateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):

    task = await TaskService.get_by_id(db, task_id)

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    await CheckUserEnrolledInCourse(course_slug=course_info["course_slug"])(request)

    user = request.state.user_data
    return await SubmissionService.create(
        db=db,
        user_id=user["id"],
        task_id=task_id,
        payload=payload.payload,
    )
