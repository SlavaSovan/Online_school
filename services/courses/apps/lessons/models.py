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
            name_without_ext = Path(self.original_filename).stem
            safe_name = name_without_ext.replace(" ", "_").replace("/", "_").lower()
            ext = Path(self.original_filename).suffix.lower()
        else:
            safe_name = self.content_type
            ext = ""

        safe_name = self.original_filename or "file"
        safe_name = safe_name.replace(" ", "_").replace("/", "_").lower()

        return f"{course_slug}/{module_slug}/{lesson_slug}/{unique_id}_{safe_name}{ext}"

    def get_download_url(self, expire=3600):
        if hasattr(self.file.storage, "url"):
            return self.file.storage.url(self.file.name)
        return self.file.url

    def get_file_info(self):
        return {
            "filename": (
                self.original_filename or Path(self.file.name).name
                if self.file
                else None
            ),
            "size": self.file_size,
            "url": self.get_download_url(),
            "content_type": self.content_type,
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
    task_uuid = models.UUIDField(primary_key=True, unique=True)
    title = models.CharField(max_length=255)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tasks")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Task {self.task_uuid}"
