import datetime
import os
import uuid
from pathlib import Path
from typing import Any, Dict
from contextlib import asynccontextmanager
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


class S3Client:
    def __init__(self):
        self.config = {
            "aws_access_key_id": settings.S3.S3_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.S3.S3_SECRET_ACCESS_KEY,
            "endpoint_url": settings.S3.S3_ENDPOINT_URL,
            "region_name": settings.S3.S3_REGION,
        }
        self.bucket_name = settings.S3.S3_BUCKET_NAME
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    def _generate_file_key(
        self,
        user_id: int,
        task_id: str,
        filename: str,
    ) -> str:
        """
        Генерация уникального ключа файла в S3.
        Формат: users/{user_id}/tasks/{task_id}/{uuid}_{filename}
        """

        safe_name = Path(filename).name

        name_without_ext, file_extension = os.path.splitext(safe_name)

        ext_clean = file_extension.lstrip(".")
        if ext_clean not in settings.FILES.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type .{file_extension} is not allowed",
            )

        file_uuid = str(uuid.uuid4())[:8]
        new_filename = f"{file_uuid}_{safe_name}"

        max_filename_length = settings.FILES.MAX_FILENAME_LENGTH

        if len(new_filename) > max_filename_length:
            available_name_length = max_filename_length - 9 - len(file_extension)

            if available_name_length < 1:
                new_filename = f"{file_uuid}{file_extension}"
            else:
                truncated_name = name_without_ext[:available_name_length]
                new_filename = f"{file_uuid}_{truncated_name}{file_extension}"

        return f"users/{user_id}/tasks/{task_id}/{new_filename}"

    async def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        task_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Загрузка файла в S3"""
        max_size = settings.FILES.MAX_FILE_SIZE_MB
        contents = await file.read()
        contents_size = len(contents)

        if contents_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum limit of {settings.FILES.MAX_FILE_SIZE_MB} Mb",
            )

        file_key = self._generate_file_key(
            user_id=user_id,
            task_id=str(task_id),
            filename=file.filename or "file",
        )

        try:
            async with self.get_client() as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    Body=contents,
                    ContentType=file.content_type or "application/octet-stream",
                    Metadata={
                        "user_id": str(user_id),
                        "task_id": task_id,
                        "orginal_filename": file.filename or "",
                        "uploaded_at": datetime.utcnow().isoformat(),
                    },
                )

                return {
                    "file_key": file_key,
                    "original_filename": file.filename or "file",
                    "size": contents_size,
                    "content_type": file.content_type,
                    "bucket": self.bucket_name,
                }
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3: {str(e)}",
            )

    async def get_download_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Получение временной ссылки для скачивания"""
        try:
            async with self.get_client() as client:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": file_key,
                    },
                    ExpiresIn=expires_in,
                )
                return url

        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate download URL: {str(e)}",
            )

    async def delete_file(self, file_key: str) -> bool:
        """Удаление файла из S3"""
        try:
            async with self.get_client() as client:
                await client.delete_object(Bucket=self.bucket, Key=file_key)
                return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}",
            )

    async def file_exists(self, file_key: str) -> bool:
        """Проверка существования файла"""
        try:
            async with self.get_client() as client:
                await client.head_object(Bucket=self.bucket, Key=file_key)
                return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise


s3_client = S3Client()
