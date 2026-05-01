from rest_framework import serializers

from apps.modules.serializers import (
    ModuleWithLessonsLimitedSerializer,
    ModuleWithLessonsSerializer,
)
from .models import Category, Course, CourseMentor, EnrollmentCache


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории"""

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]
        read_only_fields = ["slug"]


class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "price",
            "lessons_count",
            "owner_mentor_id",
            "status",
            "category",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class CourseDetailSerializer(serializers.ModelSerializer):
    modules = serializers.SerializerMethodField()
    mentors = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "owner_mentor_id",
            "price",
            "lessons_count",
            "mentors",
            "modules",
            "status",
            "category",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")

    def get_modules(self, obj):
        qs = obj.modules.all().order_by("order")
        return ModuleWithLessonsSerializer(qs, many=True).data

    def get_mentors(self, obj):
        mentors_qs = obj.mentors.all()
        return CourseMentorSerializer(mentors_qs, many=True).data


class CourseLimitedSerializer(serializers.ModelSerializer):
    """Сжатый сериализатор для курса (без контента и заданий)"""

    modules = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "owner_mentor_id",
            "price",
            "lessons_count",
            "modules",
            "status",
            "category",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")

    def get_modules(self, obj):
        qs = obj.modules.all().order_by("order")
        return ModuleWithLessonsLimitedSerializer(qs, many=True).data


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """
    При создании курса: slug генерируем при отсутствии.
    Валидация: только ментор может создавать курс – проверка в view/permission (см. permissions.py).
    """

    class Meta:
        model = Course
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "price",
            "owner_mentor_id",
            "status",
            "category",
        )
        read_only_fields = ("id", "slug")
        extra_kwargs = {
            "status": {"default": "draft", "required": False},
            "owner_mentor_id": {"required": True},
        }


class CourseMentorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMentor
        fields = ("id", "course", "mentor_id")
        read_only_fields = ("id",)


class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для записи на курс.
    """

    class Meta:
        model = EnrollmentCache
        fields = ("id", "user_id", "course")
        read_only_fields = ("id", "user_id", "course")


class AdminEnrollmentSerializer(serializers.ModelSerializer):
    """Сериализатор для записи на курс через админку"""

    class Meta:
        model = EnrollmentCache
        fields = ("id", "user_id", "course")
        read_only_fields = ("id",)
