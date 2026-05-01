from uuid import UUID
from pydantic import BaseModel
from typing import Dict, Optional, Any
from datetime import datetime

from app.submissions.models import Submission
from app.utils.enums import SubmissionStatus, TaskType


class SubmissionResponseSchema(BaseModel):
    id: int
    task_id: UUID
    user_id: int

    attempt: int
    status: SubmissionStatus

    score: Optional[float] = None
    feedback: Optional[Dict[str, Any]]

    file_info: Optional[Dict[str, Any]] = None
    code: Optional[str] = None

    created_at: datetime

    @classmethod
    def from_orm(cls, submission: Submission):
        """Добавляем информацию о файле"""

        file_info = None
        if submission.s3_file_key:
            file_info = {
                "s3_file_key": submission.s3_file_key,
                "file_size": submission.file_size,
                "original_filename": (
                    submission.payload.get("original_filename")
                    if submission.payload
                    else None
                ),
            }

        code = None
        if submission.payload and submission.payload.get("type") == "sandbox":
            code = submission.payload.get("code")

        return cls(
            id=submission.id,
            task_id=submission.task_id,
            user_id=submission.user_id,
            attempt=submission.attempt,
            status=submission.status,
            score=submission.score,
            feedback=submission.feedback,
            file_info=file_info,
            code=code,
            created_at=submission.created_at,
        )

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """Ответ после загрузки файла"""

    s3_file_key: str
    original_filename: str
    size: int
    download_url: Optional[str] = None


class FileDownloadResponse(BaseModel):
    """Ссылка для скачивания файла"""

    download_url: str
    filename: str
    expires_at: datetime


class SubmissionTaskStateSchema(BaseModel):
    task_type: TaskType
    max_attempts: int
    max_score: int
    attempts_used: int
    can_submit: bool
    last_submission: Optional[SubmissionResponseSchema]
