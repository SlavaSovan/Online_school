from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from apps.utils.signal_helpers import (
    handle_slug_on_save,
    invalidate_module_related_cache,
    update_course_counters,
    update_module_counters,
)
from .models import Module


@receiver(pre_save, sender=Module)
def update_module_slug(sender, instance, **kwargs):
    """Автоматически обновляет slug при изменении title"""
    handle_slug_on_save(sender, instance)


@receiver([post_save, post_delete], sender=Module)
def handle_module_cache_invalidation(sender, instance, **kwargs):
    """Обработка инвалидации кэша при изменении модуля"""
    invalidate_module_related_cache(instance)

    update_module_counters(instance)
    update_course_counters(instance.course)
