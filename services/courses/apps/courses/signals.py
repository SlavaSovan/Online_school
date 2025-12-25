import transliterate
from django.db.models.signals import post_save, post_delete
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Course
from apps.lessons.models import Lesson


def smart_slugify(text):
    """Создает slug с поддержкой кириллицы"""
    try:
        transliterated = transliterate.translit(text, "ru", reversed=True)
        return slugify(transliterated)
    except:
        return slugify(text)


@receiver([post_save, post_delete], sender=Lesson)
def update_course_lessons_on_lesson_change(sender, instance, **kwargs):
    """Обновляем счетчик уроков при изменении уроков"""
    if instance.module.course_id:
        course = Course.objects.get(pk=instance.module.course_id)
        course.update_lessons_count()


@receiver(pre_save, sender=Course)
def update_course_slug(sender, instance, **kwargs):
    """
    Автоматически обновляет slug при изменении title
    """
    if instance.pk:
        try:
            old_instance = Course.objects.get(pk=instance.pk)
            if old_instance.title != instance.title:
                instance.slug = smart_slugify(instance.title)
        except Course.DoesNotExist:
            if not instance.slug:
                instance.slug = smart_slugify(instance.title)
    else:
        if not instance.slug:
            instance.slug = smart_slugify(instance.title)

    if instance.slug:
        base_slug = instance.slug
        slug = base_slug
        counter = 1

        while Course.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        instance.slug = slug
