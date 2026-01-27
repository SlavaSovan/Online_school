import os
from rest_framework import serializers
from .models import Lesson, LessonContent, LessonTask


class LessonContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonContent
        fields = ("id", "lesson", "content_type", "file", "order")
        read_only_fields = ("id",)
        extra_kwargs = {"file": {"required": False}}

    def validate(self, data):
        content_type = data.get("content_type")
        file = data.get("file")

        if not self.instance:
            if not content_type:
                raise serializers.ValidationError("content_type is required")

            if not file:
                raise serializers.ValidationError(
                    f"File is required for {content_type} content"
                )

            self.validate_file_extension(file, content_type)
            self.validate_file_size(file, content_type)

            if content_type == "markdown":
                self.validate_markdown_file(file)
            elif content_type == "image":
                self.validate_image_file(file)
            elif content_type == "video":
                self.validate_video_file(file)

        elif self.instance and "content_type" in data and "file" not in data:
            if data["content_type"] != self.instance.content_type:
                raise serializers.ValidationError(
                    f"When changing content type to {data['content_type']}, "
                    f"a new file must be provided"
                )

        return data

    def validate_file_extension(self, file, content_type):
        """Проверка расширения файла"""
        filename = file.name.lower()
        allowed_extensions = {
            "markdown": [".md", ".markdown"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
            "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm", ".m4v"],
            "file": [
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                ".zip",
                ".rar",
                ".7z",
                ".txt",
                ".rtf",
                ".csv",
                ".json",
            ],
        }

        if content_type not in allowed_extensions:
            raise serializers.ValidationError(f"Invalid content type: {content_type}")

        _, ext = os.path.splitext(filename)

        if ext not in allowed_extensions[content_type]:
            allowed_str = ", ".join(allowed_extensions[content_type])
            raise serializers.ValidationError(
                f"Invalid file extension for {content_type}. "
                f"Allowed extensions: {allowed_str}"
            )

    def validate_file_size(self, file, content_type):
        """Проверка размера файла"""
        max_sizes = {
            "markdown": 5 * 1024 * 1024,  # 5MB
            "image": 10 * 1024 * 1024,  # 10MB
            "video": 1024 * 1024 * 1024,  # 1GB
            "file": 100 * 1024 * 1024,  # 100MB
        }

        max_size = max_sizes.get(content_type, 100 * 1024 * 1024)  # 100MB по умолчанию

        if file.size > max_size:
            raise serializers.ValidationError(
                f"File size should not exceed {max_size / 1024 / 1024}MB "
                f"for {content_type} content"
            )

    def validate_markdown_file(self, file):
        """Дополнительная валидация для Markdown файлов"""
        filename = file.name.lower()

        if not filename.endswith((".md", ".markdown")):
            raise serializers.ValidationError(
                "Markdown files must have .md or .markdown extension"
            )

        try:
            file.seek(0)
            content = file.read(1024).decode("utf-8", errors="ignore")
        except UnicodeDecodeError:
            raise serializers.ValidationError("Markdown file must be a valid text file")
        finally:
            file.seek(0)

    def validate_image_file(self, file):
        """Валидация с использованием python-magic"""
        try:
            import magic

            file.seek(0)
            file_data = file.read(2048)

            mime_type = magic.from_buffer(file_data, mime=True)

            allowed_types = [
                "image/jpg",
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/bmp",
                "image/webp",
                "image/svg",
            ]

            if mime_type not in allowed_types:
                raise serializers.ValidationError(
                    f"Unsupported image format: {mime_type}"
                )

        except ImportError:
            pass
        finally:
            file.seek(0)

        if file.size == 0:
            raise serializers.ValidationError("Image file cannot be empty")

    def validate_video_file(self, file):
        """Дополнительная валидация для видео файлов"""
        try:
            import magic

            file.seek(0)
            mime_type = magic.from_buffer(file.read(2048), mime=True)

            allowed_types = {
                ".mp4": ["video/mp4", "video/x-mp4"],
                ".avi": ["video/x-msvideo", "video/avi"],
                ".mov": ["video/quicktime"],
                ".wmv": ["video/x-ms-wmv"],
                ".flv": ["video/x-flv"],
                ".mkv": ["video/x-matroska"],
                ".webm": ["video/webm"],
                ".m4v": ["video/x-m4v", "video/mp4"],
            }

            file_ext = os.path.splitext(file.name)[1].lower()
            allowed_mimes = allowed_types.get(file_ext, [])

            if allowed_mimes and mime_type not in allowed_mimes:
                raise serializers.ValidationError(
                    f"The file extension and type mismatch: {file_ext}."
                )

        except ImportError:
            pass
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to check video MIME type: {e}")
        finally:
            file.seek(0)

        if file.size == 0:
            raise serializers.ValidationError("Video file cannot be empty")

    def create(self, validated_data):
        """Создание нового контента"""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Обновление существующего контента"""
        new_content_type = validated_data.get("content_type")
        new_file = validated_data.get("file")

        if (
            new_content_type
            and new_content_type != instance.content_type
            and not new_file
        ):
            raise serializers.ValidationError(
                f"When changing content type to {new_content_type}, "
                f"a new file must be provided"
            )

        return super().update(instance, validated_data)


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
