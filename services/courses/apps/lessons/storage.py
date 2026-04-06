from urllib.parse import urlparse, urlunparse
from django.conf import settings
from django.utils.deconstruct import deconstructible
from storages.backends.s3boto3 import S3Boto3Storage


@deconstructible
class LessonContentS3Storage(S3Boto3Storage):
    """Кастомное S3 хранилище для контента уроков"""

    def __init__(self, *args, **kwargs):
        kwargs["location"] = settings.AWS_LOCATION
        kwargs["bucket_name"] = settings.AWS_STORAGE_BUCKET_NAME
        super().__init__(*args, **kwargs)

    def get_valid_name(self, name):
        if not name:
            return name
        return name.replace(" ", "_")

    def url(self, name):
        """Генерируем URL с публичным хостом"""
        url = super().url(name)

        # Заменяем внутренний хост на публичный
        if hasattr(settings, "AWS_S3_PUBLIC_URL"):
            parsed = urlparse(url)
            public_parsed = urlparse(settings.AWS_S3_PUBLIC_URL)

            # Собираем новый URL с публичным хостом
            new_url = urlunparse(
                (
                    public_parsed.scheme,
                    public_parsed.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
            return new_url

        return url


lesson_content_storage = LessonContentS3Storage()
