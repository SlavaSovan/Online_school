import transliterate
from django.utils.text import slugify
from django.core.cache import cache
from apps.utils.cache_invalidator import CacheInvalidator


def smart_slugify(text):
    """Создает slug с поддержкой кириллицы"""
    try:
        transliterated = transliterate.translit(text, "ru", reversed=True)
        return slugify(transliterated)
    except:
        return slugify(text)


def generate_unique_slug(model_class, instance, slug_field="slug"):
    """Генерирует уникальный slug для модели"""
    if getattr(instance, slug_field):
        base_slug = getattr(instance, slug_field)
    else:
        base_slug = smart_slugify(instance.title)

    slug = base_slug
    counter = 1

    while (
        model_class.objects.filter(**{slug_field: slug})
        .exclude(pk=instance.pk)
        .exists()
    ):
        slug = f"{base_slug}-{counter}"
        counter += 1

    setattr(instance, slug_field, slug)


def handle_slug_on_save(sender, instance, **kwargs):
    """Обработчик slug для любой модели с полями title и slug"""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.title != instance.title:
                instance.slug = smart_slugify(instance.title)
        except sender.DoesNotExist:
            if not instance.slug:
                instance.slug = smart_slugify(instance.title)
    else:
        if not instance.slug:
            instance.slug = smart_slugify(instance.title)

    # Делаем slug уникальным
    generate_unique_slug(sender, instance)


def invalidate_course_related_cache(course_slug=None, course_id=None):
    """Инвалидирует все кэши, связанные с курсом"""
    if course_slug:
        CacheInvalidator.invalidate_course_cache(course_slug=course_slug)

    if course_id:
        CacheInvalidator.invalidate_course_cache(course_id=course_id)


def invalidate_module_related_cache(module_instance):
    """Инвалидирует все кэши, связанные с модулем"""
    if hasattr(module_instance, "course"):
        course_slug = module_instance.course.slug
        module_slug = module_instance.slug

        CacheInvalidator.invalidate_module_cache(
            course_slug=course_slug, module_slug=module_slug
        )
        CacheInvalidator.invalidate_course_cache(course_slug=course_slug)


def invalidate_lesson_related_cache(lesson_instance):
    """Инвалидирует все кэши, связанные с уроком"""
    if hasattr(lesson_instance, "module") and hasattr(lesson_instance.module, "course"):
        course_slug = lesson_instance.module.course.slug
        module_slug = lesson_instance.module.slug
        lesson_slug = lesson_instance.slug

        CacheInvalidator.invalidate_lesson_cache(
            course_slug=course_slug, module_slug=module_slug, lesson_slug=lesson_slug
        )
        CacheInvalidator.invalidate_module_cache(
            course_slug=course_slug, module_slug=module_slug
        )
        CacheInvalidator.invalidate_course_cache(course_slug=course_slug)


def update_course_counters(course):
    """Обновляет счетчики курса в кэше"""
    cache_keys_to_delete = [
        f"course_{course.id}_modules_count",
        f"course_{course.id}_lessons_count",
        f"course_detail_public:{course.slug}",
        f"course_detail_private:{course.slug}*",
    ]

    for key in cache_keys_to_delete:
        cache.delete_pattern(key)


def update_module_counters(module):
    """Обновляет счетчики модуля в кэше"""
    if hasattr(module, "course"):
        cache_key = f"module_detail_{module.course.slug}_{module.slug}"
        cache.delete(cache_key)

        # Также удаляем счетчик уроков в модуле
        cache.delete(f"module_{module.id}_lessons_count")
