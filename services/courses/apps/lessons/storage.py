import os
import uuid
from pathlib import Path
from django.core.files.storage import Storage
from django.conf import settings
from django.utils.deconstruct import deconstructible
from storages.backends.s3boto3 import S3Boto3Storage


@deconstructible
class LessonContentS3Storage(S3Boto3Storage):
    """Кастомное S3 хранилище для контента уроков"""

    def __init__(self, *args, **kwargs):
        kwargs["location"] = "lesson-content"
        super().__init__(*args, **kwargs)

    def get_valid_name(self, name):
        if not name:
            return name
        return name.replace(" ", "_")

    def generate_filename(self, filename):
        """Генерация уникального имени файла в S3"""
        return self.get_valid_name(filename)

    def url(self, name):
        """Генерируем signed URL для приватных файлов"""
        return super().url(name)


lesson_content_storage = LessonContentS3Storage()
