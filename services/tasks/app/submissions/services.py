from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile

from app.core.redis import RedisCacheClient
from app.core.s3 import s3_client
from app.submissions.models import Submission
from app.submissions.schemas_payload import (
    FileSubmissionPayload,
    SandboxSubmissionPayload,
    TestSubmissionPayload,
)
from app.submissions.schemas import (
    FileDownloadResponse,
    FileUploadResponse,
    SubmissionResponseSchema,
    SubmissionTaskStateSchema,
)
from app.submissions.test_checker import check_test_submission
from app.tasks.services import TaskService
from app.tasks.models import Task
from app.utils.enums import TaskType, SubmissionStatus


class SubmissionService:
    """
    Сервис для работы с отправками.
    Все публичные методы возвращают Pydantic схемы (SubmissionResponseSchema).
    Внутренние методы могут использовать ORM объекты, но никогда их не возвращают наружу.
    """

    @staticmethod
    async def _get_submission_orm(db: AsyncSession, submission_id: int) -> Submission:
        """Внутренний метод для получения ORM объекта."""
        result = await db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()

        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        return submission

    @staticmethod
    async def _check_attempts_limit(
        db: AsyncSession,
        task: Task,
        user_id: int,
    ) -> int:
        """Проверка лимита попыток и возврат номера попытки."""
        # Считаем использованные попытки
        result = await db.execute(
            select(func.count(Submission.id)).where(
                Submission.task_id == task.id,
                Submission.user_id == user_id,
            )
        )
        attempts_used = result.scalar()
        attempt = attempts_used + 1

        # Если max_attempts = 0 - бесконечные попытки
        if task.max_attempts == 0:
            return attempt

        # Если max_attempts > 0 - проверяем лимит
        if attempt > task.max_attempts:
            raise HTTPException(
                status_code=403,
                detail=f"No attempts left. Maximum attempts: {task.max_attempts}",
            )

        return attempt

    @staticmethod
    async def _validate_task(
        db: AsyncSession,
        task_id: UUID,
        expected_type: TaskType,
        check_active: bool = True,
    ) -> Task:
        """Внутренний метод для валидации задачи."""
        result = await db.execute(
            select(Task).where(Task.id == task_id).with_for_update()
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if check_active and not task.is_active:
            raise HTTPException(status_code=400, detail="Task is not active")

        if task.task_type != expected_type:
            raise HTTPException(
                status_code=400,
                detail=f"Task type is {task.task_type}, expected {expected_type}",
            )

        return task

    @staticmethod
    async def _upload_file(
        file: UploadFile, user_id: int, task_id: UUID
    ) -> FileUploadResponse:
        """Загрузка файла в S3"""
        upload_result = await s3_client.upload_file(
            file=file,
            user_id=user_id,
            task_id=task_id,
        )

        download_url = await s3_client.get_download_url(upload_result["s3_file_key"])

        return FileUploadResponse(
            s3_file_key=upload_result["s3_file_key"],
            original_filename=upload_result["original_filename"],
            size=upload_result["size"],
            download_url=download_url,
        )

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        submission_id: int,
    ) -> SubmissionResponseSchema:
        """Получение отправки"""
        cache_key = f"submission:{submission_id}"
        cached = await RedisCacheClient.get(cache_key)

        if cached:
            return SubmissionResponseSchema(**cached)

        submission = await SubmissionService._get_submission_orm(db, submission_id)

        schema = SubmissionResponseSchema.from_orm(submission)

        await RedisCacheClient.set(
            cache_key,
            schema.model_dump(mode="json"),
            ttl_seconds=300,
        )

        return schema

    @staticmethod
    async def get_by_id_and_task_id(
        db: AsyncSession,
        submission_id: int,
        task_id: UUID,
    ) -> SubmissionResponseSchema:
        submission = await SubmissionService._get_submission_orm(db, submission_id)

        if submission.task_id != task_id:
            raise HTTPException(status_code=404, detail="Submission not found")

        return submission

    @staticmethod
    async def get_submissions_for_task(
        db: AsyncSession,
        task_id: UUID,
    ) -> List[SubmissionResponseSchema]:
        cache_key = f"submissions:task:{task_id}"
        cached = await RedisCacheClient.get(cache_key)

        if cached:
            return [SubmissionResponseSchema(**item) for item in cached]

        result = await db.execute(
            select(Submission)
            .where(Submission.task_id == task_id)
            .order_by(Submission.created_at.desc())
        )
        submissions = result.scalars().all()

        schemas = [SubmissionResponseSchema.from_orm(sub) for sub in submissions]

        if schemas:
            await RedisCacheClient.set(
                cache_key,
                [s.model_dump(mode="json") for s in schemas],
                ttl_seconds=300,
            )

        return schemas

    @staticmethod
    async def get_user_submissions_for_task(
        db: AsyncSession,
        user_id: int,
        task_id: UUID,
    ) -> List[SubmissionResponseSchema]:
        """Получение отправок пользователя для задачи"""
        cache_key = f"submissions:task:{task_id}:user:{user_id}"
        cached = await RedisCacheClient.get(cache_key)

        if cached:
            return [SubmissionResponseSchema(**item) for item in cached]

        result = await db.execute(
            select(Submission)
            .where(Submission.user_id == user_id, Submission.task_id == task_id)
            .order_by(Submission.created_at.desc())
        )
        submissions = result.scalars().all()

        schemas = [SubmissionResponseSchema.from_orm(sub) for sub in submissions]

        if schemas:
            await RedisCacheClient.set(
                cache_key,
                [s.model_dump(mode="json") for s in schemas],
                ttl_seconds=300,
            )
        return schemas

    @staticmethod
    async def get_task_state(
        db: AsyncSession, user_id: int, task_id: UUID
    ) -> SubmissionTaskStateSchema:
        """Получение состояния задачи для пользователя."""
        task = await TaskService.get_by_id(db, task_id, as_orm=True)

        result = await db.execute(
            select(func.count(Submission.id)).where(
                Submission.task_id == task_id,
                Submission.user_id == user_id,
            )
        )
        attempts_used = result.scalar()

        result = await db.execute(
            select(Submission)
            .where(Submission.task_id == task_id, Submission.user_id == user_id)
            .order_by(Submission.created_at.desc())
            .limit(1)
        )
        last_submission = result.scalar_one_or_none()
        last_submission_schema = (
            SubmissionResponseSchema.from_orm(last_submission)
            if last_submission
            else None
        )

        # Проверяем, может ли пользователь отправлять
        can_submit = True

        if task.max_attempts == 0:
            can_submit = True
        elif task.max_attempts > 0:
            can_submit = attempts_used < task.max_attempts

        return SubmissionTaskStateSchema(
            task_type=task.task_type,
            max_attempts=task.max_attempts or 0,
            max_score=task.max_score,
            attempts_used=attempts_used,
            can_submit=can_submit,
            last_submission=last_submission_schema,
        )

    @staticmethod
    async def create_test_submission(
        db: AsyncSession,
        user_id: int,
        task_id: UUID,
        payload: TestSubmissionPayload,
    ) -> SubmissionResponseSchema:
        """Создание отправки для тестового задания"""
        task = await SubmissionService._validate_task(db, task_id, TaskType.TEST)

        attempt = await SubmissionService._check_attempts_limit(db, task, user_id)
        max_attempts = task.max_attempts
        is_last_attempt = attempt == max_attempts

        submission = Submission(
            user_id=user_id,
            task_id=task.id,
            attempt=attempt,
            payload=payload.model_dump(),
        )

        # Проверяем тест
        score, feedback = await check_test_submission(
            db=db,
            task_id=task.id,
            answers=payload.answers,
            task_max_score=task.max_score,
            is_last_attempt=is_last_attempt,
        )

        submission.score = score
        submission.feedback = feedback
        submission.status = (
            SubmissionStatus.PASSED if score > 0 else SubmissionStatus.FAILED
        )

        db.add(submission)
        await db.commit()
        await db.refresh(submission)

        return SubmissionResponseSchema.from_orm(submission)

    @staticmethod
    async def create_sandbox_submission(
        db: AsyncSession,
        user_id: int,
        task_id: UUID,
        payload: SandboxSubmissionPayload,
    ) -> SubmissionResponseSchema:
        """
        Создание отправки для задания с кодом.
        Отправляется в очередь на асинхронную проверку.
        """
        task = await SubmissionService._validate_task(db, task_id, TaskType.SANDBOX)

        result = await db.execute(
            select(Submission)
            .where(
                Submission.task_id == task_id,
                Submission.user_id == user_id,
            )
            .order_by(Submission.created_at.desc())
            .limit(1)
        )
        last_submission = result.scalar_one_or_none()

        if last_submission and last_submission.status == SubmissionStatus.PASSED:
            raise HTTPException(
                status_code=403,
                detail="Task already passed. Cannot modify submission.",
            )

        result = await db.execute(
            select(Submission).where(
                Submission.task_id == task_id,
                Submission.user_id == user_id,
                Submission.status == SubmissionStatus.NEEDS_REVIEW,
            )
        )

        # Если есть отправка на проверке - обновляем её
        if last_submission and last_submission.status == SubmissionStatus.NEEDS_REVIEW:
            last_submission.payload = payload.model_dump()

            await db.commit()
            await db.refresh(last_submission)

            return SubmissionResponseSchema.from_orm(last_submission)

        attempt = await SubmissionService._check_attempts_limit(db, task, user_id)

        submission = Submission(
            user_id=user_id,
            task_id=task_id,
            attempt=attempt,
            status=SubmissionStatus.NEEDS_REVIEW,
            payload=payload.model_dump(),
        )

        db.add(submission)
        await db.commit()
        await db.refresh(submission)

        return SubmissionResponseSchema.from_orm(submission)

    @staticmethod
    async def create_file_submission(
        db: AsyncSession,
        user_id: int,
        task_id: UUID,
        file: UploadFile,
    ) -> SubmissionResponseSchema:
        """Создание отправки для файлового задания"""
        try:
            # Получаем задачу с блокировкой
            task = await SubmissionService._validate_task(
                db, task_id, TaskType.FILE_UPLOAD
            )

            result = await db.execute(
                select(Submission)
                .where(
                    Submission.task_id == task_id,
                    Submission.user_id == user_id,
                )
                .order_by(Submission.created_at.desc())
                .limit(1)
            )
            last_submission = result.scalar_one_or_none()

            if last_submission and last_submission.status == SubmissionStatus.PASSED:
                raise HTTPException(
                    status_code=403,
                    detail="Task already passed. Cannot modify submission.",
                )

            upload_result = await SubmissionService._upload_file(
                file=file, user_id=user_id, task_id=task_id
            )
            payload = FileSubmissionPayload(
                s3_file_key=upload_result.s3_file_key,
                original_filename=upload_result.original_filename,
                file_size=upload_result.size,
            )

            if (
                last_submission
                and last_submission.status == SubmissionStatus.NEEDS_REVIEW
            ):
                if last_submission.s3_file_key:
                    await s3_client.delete_file(last_submission.s3_file_key)

                # Обновляем существующую отправку
                last_submission.payload = payload.model_dump()
                last_submission.s3_file_key = payload.s3_file_key
                last_submission.file_size = payload.file_size

                await db.commit()
                await db.refresh(last_submission)

                return SubmissionResponseSchema.from_orm(last_submission)

            attempt = await SubmissionService._check_attempts_limit(db, task, user_id)

            submission = Submission(
                user_id=user_id,
                task_id=task_id,
                attempt=attempt,
                status=SubmissionStatus.NEEDS_REVIEW,
                payload=payload.model_dump(),
                s3_file_key=payload.s3_file_key,
                file_size=payload.file_size,
            )

            db.add(submission)
            await db.commit()
            await db.refresh(submission)

            return SubmissionResponseSchema.from_orm(submission)

        except HTTPException:
            raise

        except Exception as e:
            await db.rollback()
            if upload_result:
                await s3_client.delete_file(upload_result.s3_file_key)
            raise HTTPException(
                status_code=500, detail=f"Failed to create submission: {e}"
            )

    @staticmethod
    async def get_download_url(
        db: AsyncSession,
        submission_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> FileDownloadResponse:
        """Получение ссылки для скачивания файла"""
        submission_orm = await SubmissionService._get_submission_orm(db, submission_id)

        if not is_admin and user_id:
            if submission_orm.user_id != user_id:
                raise HTTPException(status_code=404, detail="Submission not found")

        if not submission_orm.s3_file_key:
            raise HTTPException(
                status_code=404,
                detail="No file attached to this submission",
            )

        s3_file_key = submission_orm.s3_file_key
        download_url = await s3_client.get_public_download_url(s3_file_key)

        original_filename = submission_orm.payload.get(
            "original_filename", f"submission_{submission_id}"
        )

        return FileDownloadResponse(
            download_url=download_url,
            filename=original_filename,
            expires_at=datetime.now() + timedelta(hours=1),
        )

    @staticmethod
    async def download_submission_file(
        db: AsyncSession,
        submission_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ):
        """Скачивание файла решения"""
        submission_orm = await SubmissionService._get_submission_orm(db, submission_id)

        if not is_admin and user_id:
            if submission_orm.user_id != user_id:
                raise HTTPException(status_code=404, detail="Submission not found")

        if not submission_orm.s3_file_key:
            raise HTTPException(
                status_code=404,
                detail="No file attached to this submission",
            )

        original_filename = submission_orm.payload.get(
            "original_filename", f"submission_{submission_id}"
        )

        return await s3_client.download_file_as_streaming_response(
            file_key=submission_orm.s3_file_key,
            filename=original_filename,
        )

    @staticmethod
    async def delete_file_submission(
        db: AsyncSession,
        submission: Submission,
    ) -> None:
        submission = await SubmissionService._get_submission_orm(db, submission.id)

        if submission.status != SubmissionStatus.NEEDS_REVIEW:
            raise HTTPException(status_code=403, detail="Cannot delete after review")

        if submission.s3_file_key:
            await s3_client.delete_file(submission.s3_file_key)

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
    async def admin_delete(db: AsyncSession, submission_id: int):
        submission = await SubmissionService._get_submission_orm(db, submission_id)

        await db.delete(submission)
        await db.commit()
