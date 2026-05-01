from uuid import UUID
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.tasks.services import TaskService
from app.submissions.services import SubmissionService
from app.reviews.services import ReviewService
from app.reviews.schemas import (
    ReviewCreateSchema,
    ReviewResponseSchema,
    ReviewUpdateSchema,
)
from app.utils.cache_decorator import invalidate_cache
from app.utils.permission_checker import IsAuthenticated, IsMentor
from app.utils.course_dependencies import (
    CheckMentorCourseAccess,
    CheckUserEnrolledInCourse,
    GetCourseInfoByLessonId,
)


router = APIRouter(tags=["Reviews"])


async def validate_review_access(
    db: AsyncSession,
    task_id: UUID,
    submission_id: int,
    request: Request,
    check_mentor: bool = True,
):
    """Общая функция для проверки доступа к отзыву"""
    task = await TaskService.get_by_id(db, task_id)
    await SubmissionService.get_by_id_and_task_id(
        db, submission_id=submission_id, task_id=task_id
    )

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    course_slug = course_info["slug"]

    if check_mentor:
        await CheckMentorCourseAccess(course_slug=course_slug)(request)
    else:
        await CheckUserEnrolledInCourse(course_slug=course_slug)(request)


@router.post(
    "/tasks/{task_id}/submissions/{submission_id}/review",
    response_model=ReviewResponseSchema,
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=[
        "review:submission:{submission_id}",
        "submission:{submission_id}",
        "submissions:task:{task_id}",
        "submissions:task:{task_id}:user:{user_id}",
    ],
    extract_user_from_request=True,
)
async def mentor_create_review(
    task_id: UUID,
    submission_id: int,
    payload: ReviewCreateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await validate_review_access(db, task_id, submission_id, request, check_mentor=True)
    mentor_id = request.state.user_data["id"]

    return await ReviewService.create(
        db=db,
        submission_id=submission_id,
        mentor_id=mentor_id,
        payload=payload,
    )


@router.get(
    "/tasks/{task_id}/submissions/{submission_id}/review",
    response_model=ReviewResponseSchema,
    dependencies=[Depends(IsAuthenticated())],
)
async def get_review(
    task_id: UUID,
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await validate_review_access(
        db, task_id, submission_id, request, check_mentor=False
    )
    return await ReviewService.get_by_submission_id(db, submission_id)


@router.patch(
    "/tasks/{task_id}/submissions/{submission_id}/review",
    response_model=ReviewResponseSchema,
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=[
        "review:submission:{submission_id}",
        "submission:{submission_id}",
        "submissions:task:{task_id}",
        "submissions:task:{task_id}:user:{user_id}",
    ],
    extract_user_from_request=True,
)
async def mentor_update_review(
    task_id: UUID,
    submission_id: int,
    payload: ReviewUpdateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await validate_review_access(db, task_id, submission_id, request, check_mentor=True)

    review = await ReviewService.get_by_submission_id(db, submission_id)
    mentor_id = request.state.user_data["id"]

    return await ReviewService.update_by_mentor(
        db, review_id=review.id, mentor_id=mentor_id, payload=payload
    )


@router.delete(
    "/tasks/{task_id}/submissions/{submission_id}/review",
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=[
        "review:submission:{submission_id}",
        "submission:{submission_id}",
        "submissions:task:{task_id}",
        "submissions:task:{task_id}:user:{user_id}",
    ],
    before_call=True,
    extract_user_from_request=True,
)
async def mentor_delete_review(
    task_id: UUID,
    submission_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await validate_review_access(db, task_id, submission_id, request, check_mentor=True)

    review = await ReviewService.get_by_submission_id(db, submission_id)
    mentor_id = request.state.user_data["id"]

    await ReviewService.delete_by_mentor(db, review.id, mentor_id)
    return {"status": "deleted"}
