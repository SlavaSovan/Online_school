import logging
from asyncio import Task
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.core.redis import RedisCacheClient
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreateSchema, ReviewUpdateSchema
from app.submissions.models import Submission
from app.utils.enums import SubmissionStatus, TaskType

logger = logging.getLogger(__name__)


class ReviewService:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        submission_id: int,
        mentor_id: int,
        payload: ReviewCreateSchema,
    ) -> Review:
        submission = await db.get(Submission, submission_id, with_for_update=True)
        if not submission:
            raise HTTPException(404, "Submission not found")

        task = await db.get(Task, submission.task_id)
        if not task or task.task_type != TaskType.FILE:
            raise HTTPException(
                status_code=400, detail="Only FILE tasks require manual review"
            )

        if submission.status != SubmissionStatus.NEEDS_REVIEW:
            raise HTTPException(
                status_code=400, detail="Submission does not require manual review"
            )

        existing = await db.execute(
            select(Review).where(Review.submission_id == submission_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_cose=400, detail="Review already exists")

        if payload.score < 0:
            raise HTTPException(status_code=400, detail="Score must be non-negative")

        if submission.max_score and payload.score > submission.max_score:
            raise HTTPException(
                status_code=400,
                detail=f"Score cannot exceed max_score ({submission.max_score})",
            )

        review = Review(
            submission_id=submission_id,
            mentor_id=mentor_id,
            score=payload.score,
            comment=payload.comment,
        )

        submission.score = payload.score
        submission.status = (
            SubmissionStatus.PASSED if payload.score > 0 else SubmissionStatus.FAILED
        )

        if submission.feedback is None:
            submission.feedback = {}

        submission.feedback["review"] = {
            "mentor_id": mentor_id,
            "comment": payload.comment,
            "reviewed_at": (
                review.reviewed_at.isoformat() if review.reviewed_at else None
            ),
        }

        db.add(review)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        await db.refresh(review)
        return review

    @staticmethod
    async def get(db: AsyncSession, review_id: int) -> Review:
        cache_key = f"review:{review_id}"

        cached = await RedisCacheClient.get(cache_key)
        if cached:
            return Review(**cached)

        review = await db.get(Review, review_id)

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        await RedisCacheClient.set(cache_key, review.to_dict(), ttl_seconds=300)

        return review

    @staticmethod
    async def get_by_submission_id(db: AsyncSession, submission_id: int) -> Review:
        """Получение отзыва по ID отправки с кэшированием"""
        cache_key = f"review:submission:{submission_id}"

        cached = await RedisCacheClient.get(cache_key)
        if cached:
            return Review(**cached)

        result = await db.execute(
            select(Review).where(Review.submission_id == submission_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        await RedisCacheClient.set(cache_key, review.to_dict(), ttl_seconds=300)

        return review

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        review: Review,
        payload: ReviewUpdateSchema,
    ) -> Review:
        review = await db.get(
            Review, review.id, with_for_update=True, populate_existing=True
        )

        submission = await db.get(
            Submission, review.submission_id, with_for_update=True
        )

        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        changes = False

        if payload.score is not None:
            if payload.score < 0:
                raise HTTPException(
                    status_code=400, detail="Score must be non-negative"
                )

            if submission.max_score and payload.score > submission.max_score:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score cannot exceed max_score ({submission.max_score})",
                )

            review.score = payload.score
            submission.score = payload.score
            submission.status = (
                SubmissionStatus.PASSED
                if payload.score > 0
                else SubmissionStatus.FAILED
            )
            changes = True

        if payload.comment is not None:
            review.comment = payload.comment
            changes = True

        if changes:
            if submission.feedback and "review" in submission.feedback:
                submission.feedback["review"]["comment"] = review.comment
                submission.feedback["review"][
                    "updated_at"
                ] = review.reviewed_at.isoformat()

            try:
                await db.commit()
            except Exception:
                await db.rollback()
                raise

        await db.refresh(review)
        return review

    @staticmethod
    async def update_by_mentor(
        db: AsyncSession,
        *,
        review: Review,
        mentor_id: int,
        payload: ReviewUpdateSchema,
    ):
        """Изменение отзыва с проверкой прав ментора"""
        if review.mentor_id != mentor_id:
            raise HTTPException(
                status_code=403, detail="You can delete only your own review"
            )

        return await ReviewService.update(db, review=review, payload=payload)

    @staticmethod
    async def delete(db: AsyncSession, review: Review) -> None:
        review = await db.get(
            Review, review.id, with_for_update=True, populate_existing=True
        )

        submission = await db.get(
            Submission, review.submission_id, with_for_update=True
        )

        if submission:
            submission.status = SubmissionStatus.NEEDS_REVIEW
            submission.score = None

            if submission.feedback and "review" in submission.feedback:
                del submission.feedback["review"]

        await db.delete(review)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_by_mentor(
        db: AsyncSession, review: Review, mentor_id: int
    ) -> None:
        """Удаление отзыва с проверкой прав ментора"""
        if review.mentor_id != mentor_id:
            raise HTTPException(
                status_code=403, detail="You can delete only your own review"
            )

        await ReviewService.delete(db, review)
