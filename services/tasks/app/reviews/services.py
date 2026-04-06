from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.core.redis import RedisCacheClient
from app.tasks.models import Task
from app.submissions.models import Submission
from app.reviews.models import Review
from app.reviews.schemas import (
    ReviewCreateSchema,
    ReviewResponseSchema,
    ReviewUpdateSchema,
)
from app.utils.enums import SubmissionStatus, TaskType


class ReviewService:

    @staticmethod
    async def _get_review_orm(db: AsyncSession, review_id: int) -> Review:
        """Внутренний метод для получения ORM объекта отзыва."""
        result = await db.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        return review

    @staticmethod
    async def _get_submission_with_task(
        db: AsyncSession, submission_id: int
    ) -> tuple[Submission, Task]:
        """Получение отправки и связанного с ней задания."""
        result = await db.execute(
            select(Submission, Task)
            .join(Task, Submission.task_id == Task.id)
            .where(Submission.id == submission_id)
        )
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Submission not found")
        return row.Submission, row.Task

    @staticmethod
    async def _validate_review(
        submission: Submission,
        task: Task,
        score: Optional[int] = None,
        check_status: bool = True,
    ) -> None:
        """Общая валидация для создания и обновления отзыва."""
        if task.task_type not in [TaskType.FILE_UPLOAD, TaskType.SANDBOX]:
            raise HTTPException(
                status_code=400,
                detail="Only FILE and SANDBOX tasks require manual review",
            )

        if check_status and submission.status != SubmissionStatus.NEEDS_REVIEW:
            raise HTTPException(
                status_code=400,
                detail="Submission does not require manual review",
            )

        if score is not None:
            if score < 0:
                raise HTTPException(
                    status_code=400, detail="Score must be non-negative"
                )
            if score > task.max_score:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score cannot exceed max_score ({task.max_score})",
                )

    @staticmethod
    async def _update_submission_score(submission: Submission, score: int) -> None:
        """Обновление балла и статуса отправки."""
        submission.score = score
        submission.status = (
            SubmissionStatus.PASSED if score > 0 else SubmissionStatus.FAILED
        )

        if submission.feedback is None:
            submission.feedback = {}

    @staticmethod
    async def _cache_review(schema: ReviewResponseSchema) -> None:
        """Кэширование отзыва."""
        await RedisCacheClient.set(
            f"review:{schema.id}",
            schema.model_dump(mode="json"),
            ttl_seconds=300,
        )
        await RedisCacheClient.set(
            f"review:submission:{schema.submission_id}",
            schema.model_dump(mode="json"),
            ttl_seconds=300,
        )

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        submission_id: int,
        mentor_id: int,
        payload: ReviewCreateSchema,
    ) -> ReviewResponseSchema:
        submission, task = await ReviewService._get_submission_with_task(
            db, submission_id
        )

        existing = await db.execute(
            select(Review).where(Review.submission_id == submission_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Review already exists")

        await ReviewService._validate_review(submission, task, payload.score)

        review = Review(
            submission_id=submission_id,
            mentor_id=mentor_id,
            score=payload.score,
            comment=payload.comment,
        )

        await ReviewService._update_submission_score(submission, payload.score)

        submission.feedback["review"] = {
            "mentor_id": mentor_id,
            "comment": payload.comment,
            "reviewed_at": (
                review.reviewed_at.isoformat() if review.reviewed_at else None
            ),
            "task_max_score": task.max_score,
        }

        db.add(review)

        try:
            await db.commit()
            await db.refresh(review)
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Database error")

        schema = ReviewResponseSchema.model_validate(review)
        await ReviewService._cache_review(schema)

        return schema

    @staticmethod
    async def get_by_id(db: AsyncSession, review_id: int) -> ReviewResponseSchema:
        cache_key = f"review:{review_id}"
        cached = await RedisCacheClient.get(cache_key)

        if cached:
            return ReviewResponseSchema(**cached)

        review = await ReviewService._get_review_orm(db, review_id)
        schema = ReviewResponseSchema.model_validate(review)

        await RedisCacheClient.set(
            cache_key,
            schema.model_dump(mode="json"),
            ttl_seconds=300,
        )

        return schema

    @staticmethod
    async def get_by_submission_id(
        db: AsyncSession, submission_id: int
    ) -> ReviewResponseSchema:
        """Получение отзыва по ID отправки с кэшированием"""
        cache_key = f"review:submission:{submission_id}"
        cached = await RedisCacheClient.get(cache_key)

        if cached:
            return ReviewResponseSchema(**cached)

        result = await db.execute(
            select(Review).where(Review.submission_id == submission_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        schema = ReviewResponseSchema.model_validate(review)
        await RedisCacheClient.set(
            cache_key,
            schema.model_dump(mode="json"),
            ttl_seconds=300,
        )

        return schema

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        review_id: int,
        payload: ReviewUpdateSchema,
    ) -> ReviewResponseSchema:
        review = await ReviewService._get_review_orm(db, review_id)
        submission, task = await ReviewService._get_submission_with_task(
            db, review.submission_id
        )

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return ReviewResponseSchema.model_validate(review)

        update_data = payload.model_dump(exclude_unset=True)

        if "score" in update_data:
            await ReviewService._validate_review(
                submission=submission,
                task=task,
                score=update_data["score"],
                check_status=False,
            )
            review.score = update_data["score"]
            await ReviewService._update_submission_score(
                submission=submission,
                score=update_data["score"],
                task_max_score=task.max_score,
            )

        if "comment" in update_data:
            review.comment = update_data["comment"]

        if submission.feedback and "review" in submission.feedback:
            if "comment" in update_data:
                submission.feedback["review"]["comment"] = review.comment
            submission.feedback["review"]["updated_at"] = review.reviewed_at.isoformat()

        try:
            await db.commit()
            await db.refresh(review)
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Database error")

        schema = ReviewResponseSchema.model_validate(review)
        await ReviewService._cache_review(schema)

        return schema

    @staticmethod
    async def update_by_mentor(
        db: AsyncSession,
        *,
        review_id: int,
        mentor_id: int,
        payload: ReviewUpdateSchema,
    ) -> ReviewResponseSchema:
        """Изменение отзыва с проверкой прав ментора"""
        review = await ReviewService._get_review_orm(db, review_id)

        if review.mentor_id != mentor_id:
            raise HTTPException(
                status_code=403,
                detail="You can delete only your own review",
            )

        return await ReviewService.update(db, review_id=review_id, payload=payload)

    @staticmethod
    async def delete(db: AsyncSession, review_id: int) -> None:
        review = await ReviewService._get_review_orm(db, review_id)
        submission, _ = await ReviewService._get_submission_with_task(
            db, review.submission_id
        )

        submission.status = SubmissionStatus.NEEDS_REVIEW
        submission.score = None
        submission.feedback = None

        await db.delete(review)

        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Database error")

    @staticmethod
    async def delete_by_mentor(
        db: AsyncSession, review_id: int, mentor_id: int
    ) -> None:
        review = await ReviewService._get_review_orm(db, review_id)

        if review.mentor_id != mentor_id:
            raise HTTPException(
                status_code=403, detail="You can delete only your own review"
            )

        await ReviewService.delete(db, review_id)
