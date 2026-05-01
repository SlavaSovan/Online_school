import os
from pathlib import Path
from django.conf import settings
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
            "content_type",
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

    def _get_content_type_from_extension(self, filename):
        """
        Определяет content_type по расширению файла.
        Возвращает content_type или None, если расширение не найдено.
        """
        ext = os.path.splitext(filename)[1].lower()

        for content_type, extensions in settings.ALLOWED_CONTENT_TYPES.items():
            if ext in extensions:
                return content_type

        return None

    def _validate_file_size(self, file, content_type):
        """Проверка размера файла"""

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

    def validate(self, data):
        file = data.get("file")

        if not self.instance and not file:
            raise serializers.ValidationError({"file": "File is required."})

        if file:
            content_type = self._get_content_type_from_extension(file.name)

            if not content_type:
                allowed_extensions = []
                for extensions in settings.ALLOWED_CONTENT_TYPES.values():
                    allowed_extensions.extend(extensions)

                allowed_extensions_str = ", ".join(sorted(set(allowed_extensions)))
                raise serializers.ValidationError(
                    f"Unsupported file type. Allowed extensions: {allowed_extensions_str}"
                )

            data["content_type"] = content_type
            self._validate_file_size(file, content_type)

        return data

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

    def get_content(self, obj):
        """Используем префетченный контент если он есть"""
        if hasattr(obj, "content_prefetched"):
            qs = obj.content_prefetched
        else:
            qs = obj.content.all().order_by("order")

        return LessonContentSerializer(qs, many=True, context=self.context).data


class LessonLimitedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = (
            "id",
            "slug",
            "title",
            "module",
            "order",
            "is_published",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class LessonContentDisplaySerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()

    class Meta:
        model = LessonContent
        fields = (
            "id",
            "content_type",
            "order",
            "filename",
            "file_size",
            "url",
            "content",
        )
        read_only_fields = fields

    def get_filename(self, obj):
        """Получаем имя файла"""
        return obj.original_filename or Path(obj.file.name).name

    def get_url(self, obj):
        """Для немаркдаун контента возвращаем подписанный URL"""
        if obj.content_type != "markdown":
            return obj.get_download_url()
        return None

    def get_content(self, obj):
        """Для markdown читаем и возвращаем содержимое"""
        if obj.content_type == "markdown":
            try:
                # Читаем файл с начала
                obj.file.seek(0)
                return obj.file.read().decode("utf-8")
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение
                print(f"Error reading markdown file {obj.id}: {e}")
                return None
        return None

    def to_representation(self, instance):
        """Дополнительная обработка при необходимости"""
        data = super().to_representation(instance)

        # Можно добавить мета-информацию о файле
        if data["content_type"] == "markdown" and data["content"] is None:
            data["error"] = "Could not read markdown content"

        return data
