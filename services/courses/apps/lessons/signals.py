import logging
import transliterate
from django.utils.text import slugify
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from apps.utils.cache_invalidator import CacheInvalidator
from apps.utils.signal_helpers import (
    handle_slug_on_save,
    invalidate_lesson_related_cache,
    update_course_counters,
    update_module_counters,
)
from .models import Lesson, LessonContent

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Lesson)
def update_lesson_slug(sender, instance, **kwargs):
    """Автоматически обновляет slug при изменении title"""
    handle_slug_on_save(sender, instance)


@receiver(post_delete, sender=LessonContent)
def auto_delete_file_from_s3(sender, instance, **kwargs):
    """
    Удаляет файл при удалении объекта.
    """
    if instance.file:
        try:
            instance.file.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting file from S3 {instance.file.name}: {e}")


@receiver(pre_save, sender=LessonContent)
def auto_delete_old_file_from_s3(sender, instance, **kwargs):
    """
    Удаляет старый файл при обновлении файла.
    """
    if not instance.pk:
        return

    try:
        old_instance = LessonContent.objects.get(pk=instance.pk)
        old_file = old_instance.file
        new_file = instance.file

        if old_file and new_file and old_file.name != new_file.name:
            try:
                old_file.delete(save=False)
                logger.info(f"Deleted old file: {old_file.name}")
            except Exception as e:
                logger.error(f"Error deleting old file from S3 {old_file.name}: {e}")

    except LessonContent.DoesNotExist:
        pass


@receiver([post_save, post_delete], sender=Lesson)
def handle_lesson_cache_invalidation(sender, instance, **kwargs):
    """Обработка инвалидации кэша при изменении урока"""
    invalidate_lesson_related_cache(instance)

    if hasattr(instance, "module"):
        update_module_counters(instance.module)

        if hasattr(instance.module, "course"):
            update_course_counters(instance.module.course)


@receiver([post_save, post_delete], sender=LessonContent)
def handle_lesson_content_cache_invalidation(sender, instance, **kwargs):
    """Инвалидация кэша при изменении контента урока"""
    if hasattr(instance, "lesson"):
        invalidate_lesson_related_cache(instance.lesson)
