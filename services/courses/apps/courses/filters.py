import django_filters
from django.db.models import Q
from .models import Course


class CourseFilter(django_filters.FilterSet):
    """Простые фильтры для каталога курсов"""

    search = django_filters.CharFilter(method="filter_search")
    category = django_filters.CharFilter(field_name="category__slug")
    free_only = django_filters.BooleanFilter(method="filter_free_courses")

    class Meta:
        model = Course
        fields = [
            "search",
            "category",
            "status",
        ]

    def filter_search(self, queryset, name, value):
        """Поиск по названию и описанию"""
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )

    def filter_free_courses(self, queryset, name, value):
        """Фильтрация бесплатных курсов"""
        if value is True:
            return queryset.filter(Q(price=0) | Q(price__isnull=True))
        return queryset


class AdminCourseFilter(CourseFilter):
    """Фильтры для администратора (добавляем статус)"""

    status = django_filters.MultipleChoiceFilter(
        field_name="status", choices=Course.STATUS_CHOICES
    )

    class Meta(CourseFilter.Meta):
        fields = CourseFilter.Meta.fields + ["status"]
