from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from apps.lessons.filters import (
    AdminLessonContentFilter,
    AdminLessonFilter,
)

from .models import Lesson, LessonContent
from .serializers import LessonContentSerializer, LessonSerializer
from apps.modules.models import Module
from apps.courses.models import CourseMentor, EnrollmentCache
from apps.utils.permission_checker import IsAuthenticated, IsMentor, IsAdmin


class LessonListView(generics.ListCreateAPIView):
    """Список уроков модуля + создание нового"""

    serializer_class = LessonSerializer

    def get_serializer(self, *args, **kwargs):
        """Переопределяем для установки полей как read_only только при создании"""
        serializer = super().get_serializer(*args, **kwargs)

        if hasattr(serializer, "child"):
            child_serializer = serializer.child
            if hasattr(child_serializer, "fields"):
                if "module" in child_serializer.fields:
                    child_serializer.fields["module"].read_only = True
                    child_serializer.fields["module"].required = False
        elif hasattr(serializer, "fields"):
            if "module" in serializer.fields:
                serializer.fields["module"].read_only = True
                serializer.fields["module"].required = False

        return serializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsMentor()]

    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")

        module = get_object_or_404(
            Module.objects.select_related("course"),
            slug=module_slug,
            course__slug=course_slug,
        )
        course = module.course

        user_id = self.request.user_data.get("id", None)
        user_role = self.request.user_data.get("role", {}).get("name", None)

        if course.status == "published":
            if (
                user_id
                and EnrollmentCache.objects.filter(
                    user_id=user_id, course=course
                ).exists()
            ):
                return Lesson.objects.filter(module=module, is_published=True).order_by(
                    "order"
                )

        if user_role == "admin":
            return Lesson.objects.filter(module=module).order_by("order")

        if user_role == "mentor":
            is_owner = course.owner_mentor_id == user_id
            is_mentor = CourseMentor.objects.filter(
                course=course, mentor_id=user_id
            ).exists()

            if is_owner or is_mentor:
                return Lesson.objects.filter(module=module).order_by("order")

        raise PermissionDenied("You don't have access to this course")

    def perform_create(self, serializer):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")

        module = get_object_or_404(
            Module.objects.select_related("course"),
            slug=module_slug,
            course__slug=course_slug,
        )

        course = module.course
        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if user_role == "admin":
            serializer.save(module=module)
            return

        if user_role != "mentor":
            raise PermissionDenied("Mentor role required")

        if course.owner_mentor_id != user_id:
            raise PermissionDenied("You are not the owner of this course")

        serializer.save(module=module)


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали урока, обновление, удаление"""

    serializer_class = LessonSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsMentor()]

    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")

        module = get_object_or_404(
            Module.objects.select_related("course"),
            slug=module_slug,
            course__slug=course_slug,
        )
        return Lesson.objects.filter(module=module)

    def get_object(self):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")
        lesson_slug = self.kwargs.get("lesson_slug")

        lesson = get_object_or_404(
            Lesson.objects.select_related("module__course"),
            slug=lesson_slug,
            module__slug=module_slug,
            module__course__slug=course_slug,
        )

        if self.request.method == "GET":
            course = lesson.module.course

            user_id = self.request.user_data.get("id", None)
            user_role = self.request.user_data.get("role", {}).get("name", None)

            if lesson.is_published and course.status == "published":
                if (
                    user_id
                    and EnrollmentCache.objects.filter(
                        user_id=user_id, course=course
                    ).exists()
                ):
                    return lesson

            if user_role == "admin":
                return lesson

            if user_role == "mentor":
                is_owner = course.owner_mentor_id == user_id
                is_mentor = CourseMentor.objects.filter(
                    course=course, mentor_id=user_id
                ).exists()

                if is_owner or is_mentor:
                    return lesson

            raise PermissionDenied("You don't have access to this lesson")

        return self.check_edit_permissions(lesson)

    def check_edit_permissions(self, lesson):
        course = lesson.module.course
        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if user_role == "admin":
            return lesson

        if user_role != "mentor":
            raise PermissionDenied("Mentor role required")

        if course.owner_mentor_id != user_id:
            raise PermissionDenied("You are not the owner of this course")

        return lesson


class LessonContentListView(generics.ListCreateAPIView):
    """Список контента урока + создание нового"""

    serializer_class = LessonContentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer(self, *args, **kwargs):
        """Переопределяем для установки полей как read_only только при создании"""
        serializer = super().get_serializer(*args, **kwargs)

        if hasattr(serializer, "child"):
            child_serializer = serializer.child
            if hasattr(child_serializer, "fields"):
                if "lesson" in child_serializer.fields:
                    child_serializer.fields["lesson"].read_only = True
                    child_serializer.fields["lesson"].required = False
        elif hasattr(serializer, "fields"):
            if "lesson" in serializer.fields:
                serializer.fields["lesson"].read_only = True
                serializer.fields["lesson"].required = False

        return serializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsMentor()]

    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")
        lesson_slug = self.kwargs.get("lesson_slug")

        lesson = get_object_or_404(
            Lesson.objects.select_related("module__course"),
            slug=lesson_slug,
            module__slug=module_slug,
            module__course__slug=course_slug,
        )

        self.check_lesson_access(lesson)

        return LessonContent.objects.filter(lesson=lesson).order_by("order")

    def perform_create(self, serializer):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")
        lesson_slug = self.kwargs.get("lesson_slug")

        lesson = get_object_or_404(
            Lesson.objects.select_related("module__course"),
            slug=lesson_slug,
            module__slug=module_slug,
            module__course__slug=course_slug,
        )

        self.check_edit_permissions(lesson)

        serializer.save(lesson=lesson)

    def check_lesson_access(self, lesson):
        """Проверка доступа к уроку"""
        course = lesson.module.course
        user_id = self.request.user_data.get("id", None)
        user_role = self.request.user_data.get("role", {}).get("name", None)

        if lesson.is_published and course.status == "published":
            if (
                user_id
                and EnrollmentCache.objects.filter(
                    user_id=user_id, course=course
                ).exists()
            ):
                return True

        if user_role == "admin":
            return True

        if user_role == "mentor":
            is_owner = course.owner_mentor_id == user_id
            is_mentor = CourseMentor.objects.filter(
                course=course, mentor_id=user_id
            ).exists()

            if is_owner or is_mentor:
                return True

        raise PermissionDenied("You don't have access to this lesson content")

    def check_edit_permissions(self, lesson):
        """Проверка прав на редактирование"""
        course = lesson.module.course
        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if user_role == "admin":
            return True

        if user_role != "mentor":
            raise PermissionDenied("Mentor role required")

        if course.owner_mentor_id != user_id:
            raise PermissionDenied("You are not the owner of this course")

        return True


class LessonContentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали контента, обновление, удаление"""

    serializer_class = LessonContentSerializer
    lookup_field = "id"

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsMentor()]

    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")
        lesson_slug = self.kwargs.get("lesson_slug")

        lesson = get_object_or_404(
            Lesson.objects.select_related("module__course"),
            slug=lesson_slug,
            module__slug=module_slug,
            module__course__slug=course_slug,
        )

        return LessonContent.objects.filter(lesson=lesson)

    def get_object(self):
        content = super().get_object()
        lesson = content.lesson

        if self.request.method == "GET":
            self.check_lesson_access(lesson)
        else:
            self.check_edit_permissions(lesson)

        return content

    def check_lesson_access(self, lesson):
        """Проверка доступа к уроку"""
        course = lesson.module.course
        user_id = self.request.user_data.get("id", None)
        user_role = self.request.user_data.get("role", {}).get("name", None)

        if lesson.is_published and course.status == "published":
            if (
                user_id
                and EnrollmentCache.objects.filter(
                    user_id=user_id, course=course
                ).exists()
            ):
                return True

        if user_role == "admin":
            return True

        if user_role == "mentor":
            is_owner = course.owner_mentor_id == user_id
            is_mentor = CourseMentor.objects.filter(
                course=course, mentor_id=user_id
            ).exists()

            if is_owner or is_mentor:
                return True

        raise PermissionDenied("You don't have access to this lesson content")

    def check_edit_permissions(self, lesson):
        """Проверка прав на редактирование"""
        course = lesson.module.course
        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if user_role == "admin":
            return True

        if user_role != "mentor":
            raise PermissionDenied("Mentor role required")

        if course.owner_mentor_id != user_id:
            raise PermissionDenied("You are not the owner of this course")

        return True


# --------------------------- ADMIN VIEWS ---------------------------


class AdminLessonListView(generics.ListCreateAPIView):
    """Получение списка всех уроков для администратора с фильтрацией"""

    serializer_class = LessonSerializer
    permission_classes = [IsAdmin]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AdminLessonFilter
    search_fields = ["title", "slug", "module__title", "module__course__title"]
    ordering_fields = ["order", "created_at", "updated_at", "title"]
    ordering = ["-created_at"]

    def get_serializer(self, *args, **kwargs):
        """Переопределяем для установки полей как read_only только при создании"""
        serializer = super().get_serializer(*args, **kwargs)

        if hasattr(serializer, "child"):
            child_serializer = serializer.child
            if hasattr(child_serializer, "fields"):
                if "module" in child_serializer.fields:
                    child_serializer.fields["module"].read_only = False
                    child_serializer.fields["module"].required = True
        elif hasattr(serializer, "fields"):
            if "module" in serializer.fields:
                serializer.fields["module"].read_only = False
                serializer.fields["module"].required = True

    def get_queryset(self):
        queryset = (
            Lesson.objects.select_related("module", "module__course")
            .prefetch_related("content", "tasks")
            .all()
        )

        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")

        if course_slug and module_slug:
            queryset = queryset.filter(
                module__course__slug=course_slug, module__slug=module_slug
            )

        return queryset

    def list(self, request, *args, **kwargs):
        """Добавляем статистику и доступные фильтры в ответ"""
        queryset = self.filter_queryset(self.get_queryset())
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")

        if course_slug and module_slug:
            module = get_object_or_404(Module, slug=module_slug)
            module_info = {
                "id": module.id,
                "title": module.title,
                "slug": module.slug,
                "order": module.order,
            }
            course_info = {
                "id": module.course.id,
                "title": module.course.title,
                "slug": module.course.slug,
                "status": module.course.status,
            }

        total_lessons = queryset.count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["total_lessons"] = total_lessons
            if course_slug and module_slug:
                response.data["module"] = module_info
                response.data["course"] = course_info
            return response

        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            "lessons": serializer.data,
            "total_lessons": total_lessons,
        }
        if course_slug and module_slug:
            response.data["module"] = module_info
            response.data["course"] = course_info
        return Response(response_data)


class AdminLessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальное управление уроком для администратора"""

    queryset = Lesson.objects.select_related("module__course").all()
    serializer_class = LessonSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"


class AdminLessonContentListView(generics.ListCreateAPIView):
    """Получение списка всего контента для администратора с фильтрацией"""

    serializer_class = LessonContentSerializer
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AdminLessonContentFilter
    search_fields = ["file"]
    ordering_fields = ["order", "content_type", "created_at"]
    ordering = ["-created_at"]

    def get_serializer(self, *args, **kwargs):
        """Переопределяем для установки полей как read_only только при создании"""
        serializer = super().get_serializer(*args, **kwargs)

        if hasattr(serializer, "child"):
            child_serializer = serializer.child
            if hasattr(child_serializer, "fields"):
                if "lesson" in child_serializer.fields:
                    child_serializer.fields["lesson"].read_only = False
                    child_serializer.fields["lesson"].required = True
        elif hasattr(serializer, "fields"):
            if "lesson" in serializer.fields:
                serializer.fields["lesson"].read_only = False
                serializer.fields["lesson"].required = True

        return serializer

    def get_queryset(self):
        """Получаем весь контент с оптимизацией"""
        return LessonContent.objects.select_related(
            "lesson", "lesson__module", "lesson__module__course"
        ).all()


class AdminLessonContentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальное управление контентом для администратора"""

    queryset = LessonContent.objects.select_related("lesson").all()
    serializer_class = LessonContentSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"
