import os
from rest_framework import serializers
from .models import Lesson, LessonContent, LessonTask


class LessonContentSerializer(serializers.ModelSerializer):

    file_url = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = LessonContent
        fields = (
            "id",
            "lesson",
            "content_type",
            "file",
            "file_url",
            "filename",
            "file_size",
            "order",
            "original_filename",
        )
        read_only_fields = (
            "id",
            "file_url",
            "filename",
            "file_size",
            "original_filename",
        )
        extra_kwargs = {
            "file": {"required": False, "write_only": True},
            "lesson": {"required": True},
        }

    def get_file_url(self, obj):
        """Возвращаем URL для доступа к файлу"""
        return obj.get_download_url() if obj.file else None

    def get_filename(self, obj):
        """Возвращаем оригинальное имя файла"""
        return obj.original_filename

    def get_file_size(self, obj):
        """Возвращаем размер файла"""
        return obj.file_size

    def validate(self, data):
        content_type = data.get("content_type")
        file = data.get("file")

        if not self.instance:
            if not content_type:
                raise serializers.ValidationError(
                    {"content_type": "This field is required."}
                )
            if not file:
                raise serializers.ValidationError({"file": "This field is required."})

            self.validate_file_extension(file, content_type)
            self.validate_file_size(file, content_type)

            # if content_type == "markdown":
            #     self.validate_markdown_file(file)
            # elif content_type == "image":
            #     self.validate_image_file(file)
            # elif content_type == "video":
            #     self.validate_video_file(file)

        if (
            self.instance
            and content_type
            and content_type != self.instance.content_type
            and not file
        ):
            raise serializers.ValidationError(
                {"file": "New file is required when changing content type."}
            )

        return data

    def validate_file_extension(self, file, content_type):
        """Проверка расширения файла"""
        from django.conf import settings

        filename = file.name.lower()
        allowed_extensions = settings.ALLOWED_CONTENT_TYPES.get(content_type, [])

        if not allowed_extensions:
            raise serializers.ValidationError(f"Invalid content type: {content_type}")

        _, ext = os.path.splitext(filename)

        if ext not in allowed_extensions:
            allowed_str = ", ".join(allowed_extensions)
            raise serializers.ValidationError(
                f"Invalid file extension for {content_type}. "
                f"Allowed extensions: {allowed_str}"
            )

    def validate_file_size(self, file, content_type):
        """Проверка размера файла"""
        from django.conf import settings

        max_sizes = {
            "markdown": 5 * 1024 * 1024,  # 5MB
            "image": 10 * 1024 * 1024,  # 10MB
            "video": 1024 * 1024 * 1024,  # 1GB
            "file": 100 * 1024 * 1024,  # 100MB
        }

        max_size = max_sizes.get(content_type, 100 * 1024 * 1024)  # 100MB по умолчанию
        max_config_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

        max_allowed = min(max_size, max_config_size)

        if file.size > max_allowed:
            raise serializers.ValidationError(
                f"File size should not exceed {max_size / 1024 / 1024} Mb "
                f"for {content_type} content"
            )

    # def validate_markdown_file(self, file):
    #     """Дополнительная валидация для Markdown файлов"""
    #     filename = file.name.lower()

    #     if not filename.endswith((".md", ".markdown")):
    #         raise serializers.ValidationError(
    #             "Markdown files must have .md or .markdown extension"
    #         )

    #     try:
    #         file.seek(0)
    #         content = file.read(1024).decode("utf-8", errors="ignore")
    #     except UnicodeDecodeError:
    #         raise serializers.ValidationError("Markdown file must be a valid text file")
    #     finally:
    #         file.seek(0)

    # def validate_image_file(self, file):
    #     """Валидация с использованием python-magic"""
    #     try:
    #         import magic

    #         file.seek(0)
    #         file_data = file.read(2048)

    #         mime_type = magic.from_buffer(file_data, mime=True)

    #         allowed_types = [
    #             "image/jpg",
    #             "image/jpeg",
    #             "image/png",
    #             "image/gif",
    #             "image/bmp",
    #             "image/webp",
    #             "image/svg",
    #         ]

    #         if mime_type not in allowed_types:
    #             raise serializers.ValidationError(
    #                 f"Unsupported image format: {mime_type}"
    #             )

    #     except ImportError:
    #         pass
    #     finally:
    #         file.seek(0)

    #     if file.size == 0:
    #         raise serializers.ValidationError("Image file cannot be empty")

    # def validate_video_file(self, file):
    #     """Дополнительная валидация для видео файлов"""
    #     try:
    #         import magic

    #         file.seek(0)
    #         mime_type = magic.from_buffer(file.read(2048), mime=True)

    #         allowed_types = {
    #             ".mp4": ["video/mp4", "video/x-mp4"],
    #             ".avi": ["video/x-msvideo", "video/avi"],
    #             ".mov": ["video/quicktime"],
    #             ".wmv": ["video/x-ms-wmv"],
    #             ".flv": ["video/x-flv"],
    #             ".mkv": ["video/x-matroska"],
    #             ".webm": ["video/webm"],
    #             ".m4v": ["video/x-m4v", "video/mp4"],
    #         }

    #         file_ext = os.path.splitext(file.name)[1].lower()
    #         allowed_mimes = allowed_types.get(file_ext, [])

    #         if allowed_mimes and mime_type not in allowed_mimes:
    #             raise serializers.ValidationError(
    #                 f"The file extension and type mismatch: {file_ext}."
    #             )

    #     except ImportError:
    #         pass
    #     except Exception as e:
    #         import logging

    #         logger = logging.getLogger(__name__)
    #         logger.warning(f"Failed to check video MIME type: {e}")
    #     finally:
    #         file.seek(0)

    #     if file.size == 0:
    #         raise serializers.ValidationError("Video file cannot be empty")

    def create(self, validated_data):
        """Создание нового контента"""
        file = validated_data.get("file")
        if file and "original_filename" not in validated_data:
            validated_data["original_filename"] = file.name

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Обновление существующего контента"""
        file = validated_data.get("file")

        if file and "original_filename" not in validated_data:
            validated_data["original_filename"] = file.name

        return instance


class LessonTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonTask
        fields = ("task_uuid", "title", "lesson", "order")
        read_only_fields = ("task_uuid", "title", "lesson", "order")


class LessonSerializer(serializers.ModelSerializer):
    content = LessonContentSerializer(many=True, read_only=True)
    tasks = LessonTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = (
            "id",
            "slug",
            "title",
            "module",
            "order",
            "is_published",
            "content",
            "tasks",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")

    def get_content(self, obj):
        """Используем префетченный контент если он есть"""
        if hasattr(obj, "content_prefetched"):
            qs = obj.content_prefetched
        else:
            qs = obj.content.all().order_by("order")

        return LessonContentSerializer(qs, many=True, context=self.context).data
