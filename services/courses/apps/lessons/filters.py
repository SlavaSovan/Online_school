import django_filters
from django.db.models import Q
from .models import Lesson, LessonContent


class AdminLessonFilter(django_filters.FilterSet):
    """Фильтры для уроков в админ-панели"""

    search = django_filters.CharFilter(method="filter_search")

    course_slug = django_filters.CharFilter(field_name="module__course__slug")
    course_id = django_filters.NumberFilter(field_name="module__course__id")

    module_slug = django_filters.CharFilter(field_name="module__slug")
    module_id = django_filters.NumberFilter(field_name="module__id")

    has_content = django_filters.BooleanFilter(method="filter_has_content")

    has_tasks = django_filters.BooleanFilter(method="filter_has_tasks")

    class Meta:
        model = Lesson
        fields = [
            "search",
            "course_slug",
            "course_id",
            "module_slug",
            "module_id",
            "is_published",
            "has_content",
            "has_tasks",
        ]

    def filter_search(self, queryset, name, value):
        """Поиск по названию урока, модуля или курса"""
        return queryset.filter(
            Q(title__icontains=value)
            | Q(module__title__icontains=value)
            | Q(module__course__title__icontains=value)
        )

    def filter_has_content(self, queryset, name, value):
        """Фильтрация по наличию контента"""
        if value is True:
            return queryset.filter(content__isnull=False).distinct()
        elif value is False:
            return queryset.filter(content__isnull=True)
        return queryset

    def filter_has_tasks(self, queryset, name, value):
        """Фильтрация по наличию задач"""
        if value is True:
            return queryset.filter(tasks__isnull=False).distinct()
        elif value is False:
            return queryset.filter(tasks__isnull=True)
        return queryset


class AdminLessonContentFilter(django_filters.FilterSet):
    """Фильтры для контента уроков в админ-панели"""

    search = django_filters.CharFilter(method="filter_search")

    content_type = django_filters.MultipleChoiceFilter(
        field_name="content_type", choices=LessonContent.CONTENT_TYPES
    )

    course_slug = django_filters.CharFilter(field_name="lesson__module__course__slug")
    course_id = django_filters.NumberFilter(field_name="lesson__module__course__id")

    module_slug = django_filters.CharFilter(field_name="lesson__module__slug")
    module_id = django_filters.NumberFilter(field_name="lesson__module__id")

    lesson_slug = django_filters.CharFilter(field_name="lesson__slug")
    lesson_id = django_filters.NumberFilter(field_name="lesson__id")

    class Meta:
        model = LessonContent
        fields = [
            "search",
            "content_type",
            "course_slug",
            "course_id",
            "module_slug",
            "module_id",
            "lesson_slug",
            "lesson_id",
        ]

    def filter_search(self, queryset, name, value):
        """Поиск по имени файла или названию урока"""
        return queryset.filter(
            Q(file__icontains=value) | Q(lesson__title__icontains=value)
        )
