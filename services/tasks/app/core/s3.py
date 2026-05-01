import os
import unicodedata
import uuid
import mimetypes
from pathlib import Path
from typing import Any, Dict, AsyncIterator
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.config import settings


class S3Client:
    def __init__(self):
        self.config = {
            "aws_access_key_id": settings.S3.S3_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.S3.S3_SECRET_ACCESS_KEY,
            "endpoint_url": settings.S3.S3_ENDPOINT_URL,
            "region_name": settings.S3.S3_REGION,
        }
        self.bucket = settings.S3.S3_BUCKET_NAME
        self.session = get_session()

        # Парсим разрешенные типы файлов
        self.allowed_file_types = set(
            ext.strip() for ext in settings.FILES.ALLOWED_FILE_TYPES.split(",")
        )

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    def _get_file_extension(self, filename: str) -> str:
        """Получает расширение файла без точки"""
        ext = Path(filename).suffix.lower().lstrip(".")
        return ext

    def _is_file_type_allowed(self, filename: str) -> bool:
        """Проверяет, разрешен ли тип файла"""
        ext = self._get_file_extension(filename)
        return ext in self.allowed_file_types

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

        # Проверяем разрешенный тип файла
        if not self._is_file_type_allowed(safe_name):
            ext = self._get_file_extension(safe_name)
            allowed_extensions = ", ".join(sorted(self.allowed_file_types))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '.{ext}' is not allowed. Allowed types: {allowed_extensions}",
            )

        name_without_ext, file_extension = os.path.splitext(safe_name)

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

    def _sanitize_metadata_value(self, value: str) -> str:
        """
        Очистка значения для S3 метаданных.
        Оставляет только ASCII символы.
        """
        if not value:
            return ""

        # Нормализуем Unicode
        value = unicodedata.normalize("NFKD", value)
        # Оставляем только ASCII символы
        value = value.encode("ascii", "ignore").decode("ascii")
        return value

    async def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        task_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Загрузка файла в S3"""
        max_size = settings.FILES.MAX_FILE_SIZE_MB * 1024 * 1024
        contents = await file.read()
        contents_size = len(contents)

        if contents_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File size ({contents_size / (1024*1024):.2f} MB) exceeds maximum limit of {settings.FILES.MAX_FILE_SIZE_MB} Mb",
            )

        original_filename = file.filename or "file"

        file_key = self._generate_file_key(
            user_id=user_id,
            task_id=str(task_id),
            filename=original_filename,
        )

        sanitized_filename = self._sanitize_metadata_value(original_filename)

        try:
            async with self.get_client() as client:
                await client.put_object(
                    Bucket=self.bucket,
                    Key=file_key,
                    Body=contents,
                    ContentType=file.content_type or "application/octet-stream",
                    Metadata={
                        "user_id": str(user_id),
                        "task_id": str(task_id),
                        "orginal_filename": sanitized_filename,
                        "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    },
                )

                return {
                    "s3_file_key": file_key,
                    "original_filename": original_filename,
                    "size": contents_size,
                    "content_type": file.content_type,
                    "bucket": self.bucket,
                }
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3: {str(e)}",
            )

    async def download_file(
        self,
        file_key: str,
    ) -> AsyncIterator[bytes]:
        """
        Потоковое скачивание файла из S3.
        Возвращает асинхронный итератор чанков файла.
        """
        try:
            async with self.get_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket,
                    Key=file_key,
                )

                async for chunk in response["Body"].iter_chunks():
                    yield chunk

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found in storage",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download file: {str(e)}",
            )

    async def download_file_as_streaming_response(
        self,
        file_key: str,
        filename: str,
    ) -> StreamingResponse:
        """
        Возвращает StreamingResponse для скачивания файла.
        """
        from urllib.parse import quote

        file_stream = self.download_file(file_key)

        # Определяем Content-Type
        content_type = self._get_content_type(filename)
        safe_filename = self._sanitize_metadata_value(filename)

        if not safe_filename or safe_filename == ".":
            # Берем только расширение или используем стандартное имя
            ext = self._get_file_extension(filename)
            safe_filename = f"submission.{ext}" if ext else "submission"

        # Создаем заголовок с ASCII именем
        content_disposition = f'attachment; filename="{safe_filename}"'

        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": content_disposition,
                "Content-Type": content_type,
            },
        )

    def _get_content_type(self, filename: str) -> str:
        """Определяет Content-Type по расширению файла"""
        ext = self._get_file_extension(filename)

        # Маппинг расширений на Content-Type
        content_type_map = {
            # Документы
            "pdf": "application/pdf",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xlsm": "application/vnd.ms-excel.sheet.macroenabled.12",
            "ppt": "application/vnd.ms-powerpoint",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "pptm": "application/vnd.ms-powerpoint.presentation.macroenabled.12",
            # Текстовые файлы
            "txt": "text/plain",
            # Архивы
            "zip": "application/zip",
            "rar": "application/x-rar-compressed",
            # Код
            "py": "text/x-python",
            "java": "text/x-java",
            "cpp": "text/x-c++src",
            "c": "text/x-csrc",
            "js": "application/javascript",
            "html": "text/html",
            "css": "text/css",
        }

        content_type = content_type_map.get(ext)
        if not content_type:
            # Пробуем определить через mimetypes
            content_type, _ = mimetypes.guess_type(filename)

        return content_type or "application/octet-stream"

    async def get_public_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
    ) -> str:
        """Получение временной ссылки для скачивания"""
        public_endpoint = settings.S3.S3_PUBLIC_ENDPOINT

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
            internal_endpoint = self.config["endpoint_url"]
            if internal_endpoint in url:
                url = url.replace(internal_endpoint, public_endpoint)

            return url

        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate download URL: {str(e)}",
            )

    async def get_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
    ) -> str:
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
