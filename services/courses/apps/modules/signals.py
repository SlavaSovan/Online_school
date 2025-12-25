import transliterate
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Module


def smart_slugify(text):
    """Создает slug с поддержкой кириллицы"""
    try:
        transliterated = transliterate.translit(text, "ru", reversed=True)
        return slugify(transliterated)
    except:
        return slugify(text)


@receiver(pre_save, sender=Module)
def update_course_slug(sender, instance, **kwargs):
    """
    Автоматически обновляет slug при изменении title
    """
    if instance.pk:
        try:
            old_instance = Module.objects.get(pk=instance.pk)
            if old_instance.title != instance.title:
                instance.slug = smart_slugify(instance.title)
        except Module.DoesNotExist:
            if not instance.slug:
                instance.slug = smart_slugify(instance.title)
    else:
        if not instance.slug:
            instance.slug = smart_slugify(instance.title)
