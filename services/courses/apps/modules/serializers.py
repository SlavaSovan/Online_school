from rest_framework import serializers
from .models import Module
from apps.lessons.serializers import (
    LessonSerializer,
)


class ModuleDetailSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()

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
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")

    def get_lessons(self, obj):
        qs = obj.lessons.all().order_by("order")
        return LessonSerializer(qs, many=True).data


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
