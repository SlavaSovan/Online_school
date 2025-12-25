import os
import transliterate
from django.utils.text import slugify
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Lesson, LessonContent


def smart_slugify(text):
    """Создает slug с поддержкой кириллицы"""
    try:
        transliterated = transliterate.translit(text, "ru", reversed=True)
        return slugify(transliterated)
    except:
        return slugify(text)


@receiver(pre_save, sender=Lesson)
def update_course_slug(sender, instance, **kwargs):
    """
    Автоматически обновляет slug при изменении title
    """
    if instance.pk:
        try:
            old_instance = Lesson.objects.get(pk=instance.pk)
            if old_instance.title != instance.title:
                instance.slug = smart_slugify(instance.title)
        except Lesson.DoesNotExist:
            if not instance.slug:
                instance.slug = smart_slugify(instance.title)
    else:
        if not instance.slug:
            instance.slug = smart_slugify(instance.title)


@receiver(pre_save, sender=LessonContent)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Удаляет старый файл при обновлении файла.
    """
    if not instance.pk:
        return False

    try:
        old_instance = LessonContent.objects.get(pk=instance.pk)
        old_file = old_instance.file
        new_file = instance.file

        if old_file and old_file != new_file:
            if os.path.isfile(old_file.path):
                try:
                    os.remove(old_file.path)
                except (OSError, FileNotFoundError) as e:
                    print(f"Error deleting old file {old_file.path}: {e}")
    except LessonContent.DoesNotExist:
        return False


@receiver(post_delete, sender=LessonContent)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Удаляет файл при удалении объекта.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            try:
                os.remove(instance.file.path)
            except (OSError, FileNotFoundError) as e:
                print(f"Error deleting file {instance.file.path}: {e}")
