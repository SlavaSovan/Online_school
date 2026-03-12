from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.redis import RedisCacheClient
from app.sandbox.utils.producer import enqueue_sandbox_task
from app.submissions.models import Submission
from app.submissions.schemas_payload import SubmissionPayload
from app.utils.enums import TaskType, SubmissionStatus
from app.tasks.models import Task
from app.submissions.test_checker import check_test_submission
from app.core.s3 import s3_client


class SubmissionService:

    @staticmethod
    async def get_by_id(db: AsyncSession, submission_id: int) -> Submission:
        """Получение отправки"""
        cache_key = f"submission:{submission_id}"

        cached = await RedisCacheClient.get(cache_key)
        if cached:
            return Submission(**cached)

        result = await db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()

        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        await RedisCacheClient.set(
            cache_key,
            submission.to_dict(),
            ttl_seconds=300,
        )

        return submission

    @staticmethod
    async def get_by_id_and_task_id(
        db: AsyncSession, submission_id: int, task_id: UUID
    ):
        submission = await SubmissionService.get_by_id(db, submission_id)
        if submission.task_id != task_id:
            raise HTTPException(status_code=404, detail="Submission not found")
        return submission

    @staticmethod
    async def get_user_submissions_for_task(
        db: AsyncSession, user_id: int, task_id: UUID
    ) -> List[Submission]:
        """Получение отправок пользователя для задачи"""
        cache_key = f"submissions:user:{user_id}:task:{task_id}"

        cached = await RedisCacheClient.get(cache_key)
        if cached:
            return [Submission(**submission_data) for submission_data in cached]

        result = await db.execute(
            select(Submission)
            .where(Submission.user_id == user_id, Submission.task_id == task_id)
            .order_by(Submission.created_at.desc())
        )
        submissions = result.scalars().all()

        if submissions:
            await RedisCacheClient.set(
                cache_key,
                [sub.to_dict() for sub in submissions],
                ttl_seconds=300,
            )
        return list(submissions)

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        task_id: UUID,
        payload: SubmissionPayload,
    ) -> Submission:
        result = await db.execute(
            select(Task).where(Task.id == task_id).with_for_update()
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if not task.is_active:
            raise HTTPException(status_code=400, detail="Task is not active")

        attempt = 1
        if task.task_type == TaskType.TEST:
            result = await db.execute(
                select(func.count(Submission.id)).where(
                    Submission.task_id == task_id,
                    Submission.user_id == user_id,
                )
            )
            attempts_used = result.scalar()

            if task.max_attempts is not None and attempts_used >= task.max_attempts:
                raise HTTPException(403, "No attempts left")
            attempt = attempts_used + 1

        submission = Submission(
            user_id=user_id,
            task_id=task_id,
            attempt=attempt,
            payload=payload.model_dump(),
        )

        if task.task_type == TaskType.TEST:
            if payload.type != "test":
                raise HTTPException(
                    status_code=400, detail="Invalid payload type for TEST task"
                )

            score, max_score, feedback = await check_test_submission(
                db=db,
                task_id=task.id,
                answers=payload.answers,
            )

            submission.score = score
            submission.max_score = max_score
            submission.feedback = feedback
            submission.status = (
                SubmissionStatus.PASSED if score > 0 else SubmissionStatus.FAILED
            )

        elif task.task_type == TaskType.SANDBOX:
            if payload.type != "sandbox":
                raise HTTPException(
                    status_code=400, detail="Invalid payload type for SANDBOX task"
                )

            submission.status = SubmissionStatus.QUEUED
            submission.score = None

        elif task.task_type == TaskType.FILE:
            if payload.type != "file":
                raise HTTPException(
                    status_code=400, detail="Invalid payload type for FILE task"
                )

            file_payload = payload
            file_exists = await s3_client.file_exists(file_payload.s3_file_key)

            if not file_exists:
                raise HTTPException(status_code=400, detail="File not found in storage")

            submission.s3_file_key = file_payload.s3_file_key
            submission.file_size = file_payload.file_size
            submission.status = SubmissionStatus.NEEDS_REVIEW
            submission.payload["original_filename"] = file_payload.original_filename

        db.add(submission)
        await db.commit()
        await db.refresh(submission)

        if task.task_type == TaskType.SANDBOX:
            await enqueue_sandbox_task(submission.id)

        return submission

    @staticmethod
    async def delete_file_submission(
        db: AsyncSession,
        submission: Submission,
    ):
        if submission.status != SubmissionStatus.NEEDS_REVIEW:
            raise HTTPException(status_code=403, detail="Cannot delete after review")

        await db.delete(submission)
        await db.commit()

    @staticmethod
    async def admin_list(
        db: AsyncSession,
        *,
        user_id: Optional[int] = None,
        task_id: Optional[UUID] = None,
        status: Optional[SubmissionStatus] = None,
        task_type: Optional[TaskType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Submission]:
        stmt = select(Submission).join(Task)

        if user_id is not None:
            stmt = stmt.where(Submission.user_id == user_id)

        if task_id is not None:
            stmt = stmt.where(Submission.task_id == task_id)

        if status is not None:
            stmt = stmt.where(Submission.status == status)

        if task_type is not None:
            stmt = stmt.where(Task.task_type == task_type)

        stmt = stmt.order_by(Submission.id.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def admin_delete(db: AsyncSession, submission: Submission):
        await db.delete(submission)
        await db.commit()
