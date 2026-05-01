import os
from pathlib import Path
import uuid
from django.db import models
from django.utils.text import slugify
from django.conf import settings

from .storage import lesson_content_storage
from apps.modules.models import Module


class Lesson(models.Model):

    slug = models.SlugField(unique=True, blank=True)
    title = models.CharField(max_length=255)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.order}. {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

        if self.module and self.module.course:
            self.module.course.update_lessons_count()

    def delete(self, *args, **kwargs):
        course = self.module.course if self.module else None
        super().delete(*args, **kwargs)
        if course:
            course.update_lessons_count()


class LessonContent(models.Model):
    CONTENT_TYPES = [
        ("markdown", "Markdown"),
        ("image", "Image"),
        ("video", "Video"),
        ("file", "File"),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="content")
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    file = models.FileField(
        upload_to="", storage=lesson_content_storage, max_length=500
    )
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Content {self.id} ({self.content_type})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if self.file and not self.original_filename:
            self.original_filename = Path(self.file.name).name

        if self.file and (is_new or self._file_changed()):
            new_path = self._generate_structured_path()

            self.file.name = new_path

            try:
                if hasattr(self.file, "size"):
                    self.file_size = self.file.size
                elif hasattr(self.file, "file") and hasattr(self.file.file, "size"):
                    self.file_size = self.file.file.size
            except (ValueError, OSError, AttributeError):
                self.file_size = None

        super().save(*args, **kwargs)

    def _file_changed(self):
        """Проверяем, изменился ли файл"""
        if not self.pk:
            return True

        try:
            old_instance = LessonContent.objects.get(pk=self.pk)
            return old_instance.file.name != self.file.name
        except LessonContent.DoesNotExist:
            return True

    def _generate_structured_path(self):
        """Генерация структурированного пути"""
        try:
            course_slug = self.lesson.module.course.slug
            module_slug = self.lesson.module.slug
            lesson_slug = self.lesson.slug
        except AttributeError:
            course_slug = "unknown"
            module_slug = "unknown"
            lesson_slug = "unknown"

        unique_id = str(uuid.uuid4())[:8]

        if self.original_filename:
            safe_name = (
                self.original_filename.replace(" ", "_").replace("/", "_").lower()
            )
        else:
            safe_name = "file"

        return f"{course_slug}/{module_slug}/{lesson_slug}/{unique_id}_{safe_name}"

    def get_download_url(self, expire=3600):
        return self.file.url

    def get_file_info(self):
        """Информация о файле для API"""
        return {
            "id": self.id,
            "lesson": self.lesson.id,
            "content_type": self.content_type,
            "file_url": self.get_download_url(),
            "filename": self.original_filename or Path(self.file.name).name,
            "file_size": self.file_size,
            "order": self.order,
            "original_filename": self.original_filename,
        }

    def get_content_data(self):
        """Получить данные контента для отображения"""
        if self.content_type == "markdown":
            try:
                # Читаем содержимое markdown файла
                content = self.file.read().decode("utf-8")
                return {
                    "type": "markdown",
                    "content": content,
                    "metadata": self.get_file_info(),
                }
            except Exception as e:
                return {"type": "error", "message": f"Error reading markdown: {str(e)}"}
        else:
            return {
                "type": self.content_type,
                "url": self.get_download_url(),
                "metadata": self.get_file_info(),
            }

    def delete(self, *args, **kwargs):
        """Переопределяем удаление для корректного удаления файла"""
        if self.file:
            storage, path = self.file.storage, self.file.name
        super().delete(*args, **kwargs)

        if self.file:
            try:
                storage.delete(path)
            except Exception:
                pass


class LessonTask(models.Model):
    task_uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tasks")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Task {self.task_uuid} - {self.title}"
