from django.db.models.signals import post_save, post_delete
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.cache import cache

from apps.utils.signal_helpers import (
    handle_slug_on_save,
    invalidate_course_related_cache,
    update_course_counters,
)

from .models import Course, Category, CourseMentor, EnrollmentCache
from apps.utils.cache_invalidator import CacheInvalidator


@receiver(pre_save, sender=Course)
def update_course_slug(sender, instance, **kwargs):
    """Автоматически обновляет slug при изменении title"""
    handle_slug_on_save(sender, instance)


@receiver([post_save, post_delete], sender=Course)
def handle_course_cache_invalidation(sender, instance, **kwargs):
    """Обработка инвалидации кэша при изменении курса"""
    invalidate_course_related_cache(course_slug=instance.slug, course_id=instance.id)

    update_course_counters(instance)

    if kwargs.get("created") is False:
        try:
            old_category_id = sender.objects.get(pk=instance.id).category_id
            if old_category_id != instance.category_id:
                cache.delete_pattern(f"category_courses_{old_category_id}_*")
        except sender.DoesNotExist:
            pass


@receiver([post_save, post_delete], sender=Category)
def handle_category_cache_invalidation(sender, instance, **kwargs):
    """Инвалидация кэша при изменении категории"""
    CacheInvalidator.invalidate_category_cache(
        category_id=instance.id, category_slug=instance.slug
    )


@receiver([post_save, post_delete], sender=CourseMentor)
def handle_course_mentor_cache_invalidation(sender, instance, **kwargs):
    """Инвалидация кэша при изменении связи курс-ментор"""
    if instance.course:
        invalidate_course_related_cache(course_slug=instance.course.slug)


@receiver([post_save, post_delete], sender=EnrollmentCache)
def handle_enrollment_cache_invalidation(sender, instance, **kwargs):
    """Инвалидация кэша при изменении записи на курс"""
    if instance.course:
        invalidate_course_related_cache(course_slug=instance.course.slug)

    if instance.user_id:
        cache.delete_pattern(f"my_enrollments_user_{instance.user_id}_*")
        cache.delete_pattern(f"my_courses_user_{instance.user_id}_*")
