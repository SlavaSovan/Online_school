from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, HTTPException

from app.core.s3 import s3_client
from app.submissions.models import Submission
from app.submissions.services import SubmissionService
from app.tasks.services import TaskService


class SubmissionFileService:
    """Сервис для работы с файлами отправок"""

    @staticmethod
    async def upload_file(
        file: UploadFile, user_id: int, task_id: UUID
    ) -> Dict[str, Any]:
        """Загрузка файла в S3"""
        upload_result = await s3_client.upload_file(
            file=file, user_id=user_id, task_id=task_id
        )

        download_url = await s3_client.get_download_url(upload_result["file_key"])

        return {**upload_result, "download_url": download_url}

    @staticmethod
    async def create_submission_with_file(
        db: AsyncSession, user_id: int, task_id: UUID, file: UploadFile
    ) -> Submission:
        """Создание отправки с файлом (все в одной транзакции)"""
        from sqlalchemy import func

        task = await TaskService.get_by_id(db, task_id)

        if task.task_type != "FILE":
            raise HTTPException(
                status_code=400, detail="File upload is only allowed for FILE tasks"
            )

        from app.submissions.models import Submission

        result = await db.execute(
            select(func.count(Submission.id)).where(
                Submission.task_id == task_id,
                Submission.user_id == user_id,
            )
        )
        attempts_used = result.scalar()

        if task.max_attempts and attempts_used >= task.max_attempts:
            raise HTTPException(status_code=403, detail="No attempts left")

        attempt = attempts_used + 1

        try:
            upload_result = await SubmissionFileService.upload_file(
                file=file, user_id=user_id, task_id=task_id
            )

            submission = Submission(
                user_id=user_id,
                task_id=task_id,
                attempt=attempt,
                status="NEEDS_REVIEW",
                payload={
                    "type": "file",
                    "s3_file_key": upload_result["s3_file_key"],
                    "original_filename": upload_result["original_filename"],
                    "file_size": upload_result["size"],
                },
                s3_file_key=upload_result["s3_file_key"],
                file_size=upload_result["size"],
            )

            db.add(submission)
            await db.commit()
            await db.refresh(submission)

            return submission

        except Exception as e:
            await db.rollback()
            if "upload_result" in locals():
                await s3_client.delete_file(upload_result["s3_file_key"])
            raise

    @staticmethod
    async def get_download_url(
        submission_id: int,
        db: AsyncSession,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> Dict[str, Any]:
        """Получение ссылки для скачивания файла"""
        submission = await SubmissionService.get_by_id(db, submission_id)

        if not is_admin and user_id:
            if submission.user_id != user_id:
                raise HTTPException(status_code=404, detail="Submission not found")

        if not submission.s3_file_key:
            raise HTTPException(status_code=404, detail="No file attached")

        download_url = await s3_client.get_download_url(submission.s3_file_key)

        # Получаем имя файла из payload
        filename = submission.payload.get(
            "original_filename", f"submission_{submission_id}"
        )

        return {
            "download_url": download_url,
            "filename": filename,
            "expires_at": datetime.now(datetime.timezone.utc) + timedelta(hours=1),
        }

    @staticmethod
    async def delete_submission_file(
        db: AsyncSession, submission: Submission, delete_from_s3: bool = True
    ) -> bool:
        """Удаление файла отправки"""
        if submission.status != "NEEDS_REVIEW":
            raise HTTPException(status_code=403, detail="Cannot delete after review")

        if delete_from_s3 and submission.s3_file_key:
            await s3_client.delete_file(submission.s3_file_key)

        await db.delete(submission)
        await db.commit()

        return True


submission_file_service = SubmissionFileService()
