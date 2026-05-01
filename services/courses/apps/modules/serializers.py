from rest_framework import serializers
from .models import Module
from apps.lessons.serializers import (
    LessonLimitedSerializer,
    LessonSerializer,
)


class ModuleDetailSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "course",
            "order",
            "lessons",
            "lessons_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")

    def get_lessons(self, obj):
        if hasattr(obj, "lessons_prefetched"):
            qs = obj.lessons_prefetched
        else:
            qs = obj.lessons.all()

        qs = sorted(qs, key=lambda x: x.order)

        return LessonSerializer(qs, many=True, context=self.context).data

    def get_lessons_count(self, obj):
        """Количество уроков - можно получить из prefetch_related"""
        if hasattr(obj, "lessons_prefetched"):
            return len(obj.lessons_prefetched)
        return obj.lessons.count()


class ModuleWithLessonsSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "order",
            "lessons",
        )


class ModuleWithLessonsLimitedSerializer(serializers.ModelSerializer):
    """Сериализатор модуля с уроками без контента и заданий"""

    lessons = LessonLimitedSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "order",
            "lessons",
        )
