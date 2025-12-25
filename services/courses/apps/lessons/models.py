from django.db import models
from django.utils.text import slugify

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
    file = models.FileField(upload_to="lesson_files/")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Content {self.id} ({self.content_type})"


class LessonTask(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tasks")
    external_task_uuid = models.UUIDField()  # from Task Microservice

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Task {self.external_task_uuid}"
