from pathlib import Path
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

from apps.lessons.filters import (
    AdminLessonContentFilter,
    AdminLessonFilter,
)
from apps.utils.cache_decorator import cache_response
from apps.utils.cache_invalidator import CacheInvalidator

from .models import Lesson, LessonContent, LessonTask
from .serializers import (
    LessonContentDisplaySerializer,
    LessonContentSerializer,
    LessonSerializer,
)
from apps.modules.models import Module
from apps.courses.models import CourseMentor, EnrollmentCache
from apps.utils.permission_checker import IsAuthenticated, IsMentor, IsAdmin


class LessonAccessMixin:
    """Миксин для проверки доступа к урокам"""

    def _check_lesson_access(self, lesson, user_id, user_role):
        """Проверка доступа к уроку для просмотра"""
        course = lesson.module.course

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

            return is_owner or is_mentor

        return False

    def _check_edit_permissions(self, lesson, user_id, user_role):
        """Проверка прав на редактирование урока"""
        course = lesson.module.course

        if user_role == "admin":
            return True

        if user_role != "mentor":
            raise PermissionDenied("Mentor role required")

        if course.owner_mentor_id != user_id:
            raise PermissionDenied("You are not the owner of this course")

        return True


class LessonListView(generics.ListCreateAPIView, LessonAccessMixin):
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

    def list(self, request, *args, **kwargs):
        """Кэшируем список уроков"""
        course_slug = kwargs.get("course_slug")
        module_slug = kwargs.get("module_slug")
        cache_key_prefix = f"lessons_list_{course_slug}_{module_slug}"

        decorator = cache_response(timeout=180, key_prefix=cache_key_prefix)
        decorated_method = decorator(super().list)
        return decorated_method(self, request, *args, **kwargs)

    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")

        module = get_object_or_404(
            Module.objects.select_related("course"),
            slug=module_slug,
            course__slug=course_slug,
        )

        user_id = self.request.user_data.get("id", None)
        user_role = self.request.user_data.get("role", {}).get("name", None)

        queryset = Lesson.objects.filter(module=module).select_related("module__course")
        queryset = queryset.prefetch_related(
            Prefetch(
                "content",
                queryset=LessonContent.objects.order_by("order"),
                to_attr="content_prefetched",
            ),
            Prefetch(
                "tasks",
                queryset=LessonTask.objects.all(),
                to_attr="tasks_prefetched",
            ),
        ).order_by("order")

        if self.request.method == "GET":
            course = module.course

            if course.status == "published":
                if (
                    user_id
                    and EnrollmentCache.objects.filter(
                        user_id=user_id, course=course
                    ).exists()
                ):
                    return queryset.filter(is_published=True)

            if user_role == "admin":
                return queryset

            if user_role == "mentor":
                is_owner = course.owner_mentor_id == user_id
                is_mentor = CourseMentor.objects.filter(
                    course=course, mentor_id=user_id
                ).exists()

                if is_owner or is_mentor:
                    return queryset

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
            lesson = serializer.save(module=module)
            CacheInvalidator.invalidate_lesson_cache(
                course_slug=course_slug, module_slug=module_slug
            )
            return

        if user_role != "mentor":
            raise PermissionDenied("Mentor role required")

        if course.owner_mentor_id != user_id:
            raise PermissionDenied("You are not the owner of this course")

        lesson = serializer.save(module=module)
        CacheInvalidator.invalidate_lesson_cache(
            course_slug=course_slug, module_slug=module_slug
        )


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView, LessonAccessMixin):
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

        return (
            Lesson.objects.filter(
                module__slug=module_slug, module__course__slug=course_slug
            )
            .select_related("module__course")
            .prefetch_related(
                Prefetch(
                    "content",
                    queryset=LessonContent.objects.order_by("order"),
                    to_attr="content_prefetched",
                ),
                Prefetch(
                    "tasks",
                    queryset=LessonTask.objects.all(),
                    to_attr="tasks_prefetched",
                ),
            )
        )

    def retrieve(self, request, *args, **kwargs):
        """Кэшируем детали урока"""
        course_slug = kwargs.get("course_slug")
        module_slug = kwargs.get("module_slug")
        lesson_slug = kwargs.get("lesson_slug")
        cache_key_prefix = f"lesson_detail_{course_slug}_{module_slug}_{lesson_slug}"

        decorator = cache_response(timeout=300, key_prefix=cache_key_prefix)
        decorated_method = decorator(super().retrieve)
        return decorated_method(self, request, *args, **kwargs)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lesson_slug = self.kwargs.get("lesson_slug")

        lesson = get_object_or_404(queryset, slug=lesson_slug)

        user_id = self.request.user_data.get("id", None)
        user_role = self.request.user_data.get("role", {}).get("name", None)

        if self.request.method == "GET":
            if not self._check_lesson_access(lesson, user_id, user_role):
                raise PermissionDenied("You don't have access to this lesson")
            return lesson
        else:
            self._check_edit_permissions(lesson, user_id, user_role)
            return lesson

    def perform_update(self, serializer):
        lesson = serializer.save()
        CacheInvalidator.invalidate_lesson_cache(
            course_slug=lesson.module.course.slug,
            module_slug=lesson.module.slug,
            lesson_slug=lesson.slug,
        )

    def perform_destroy(self, instance):
        course_slug = instance.module.course.slug
        module_slug = instance.module.slug
        lesson_slug = instance.slug
        super().perform_destroy(instance)
        CacheInvalidator.invalidate_lesson_cache(
            course_slug=course_slug, module_slug=module_slug, lesson_slug=lesson_slug
        )


class LessonContentListView(generics.ListCreateAPIView, LessonAccessMixin):
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

    def list(self, request, *args, **kwargs):
        """Кэшируем контент урока"""
        course_slug = kwargs.get("course_slug")
        module_slug = kwargs.get("module_slug")
        lesson_slug = kwargs.get("lesson_slug")
        cache_key_prefix = f"lesson_content_{course_slug}_{module_slug}_{lesson_slug}"

        decorator = cache_response(timeout=300, key_prefix=cache_key_prefix)
        decorated_method = decorator(super().list)
        return decorated_method(self, request, *args, **kwargs)

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

        user_id = self.request.user_data.get("id", None)
        user_role = self.request.user_data.get("role", {}).get("name", None)

        if not self._check_lesson_access(lesson, user_id, user_role):
            raise PermissionDenied("You don't have access to this lesson content")

        return (
            LessonContent.objects.filter(lesson=lesson)
            .select_related("lesson")
            .order_by("order")
        )

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

        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if not self._check_edit_permissions(lesson, user_id, user_role):
            raise PermissionDenied("You don't have permission to edit this lesson")

        content = serializer.save(lesson=lesson)

        CacheInvalidator.invalidate_lesson_cache(
            course_slug=course_slug, module_slug=module_slug, lesson_slug=lesson_slug
        )


class LessonContentDetailView(generics.RetrieveUpdateDestroyAPIView, LessonAccessMixin):
    """Детали контента, обновление, удаление"""

    serializer_class = LessonContentSerializer
    lookup_field = "id"

    def get_permissions(self):
        return [IsMentor()]

    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")
        lesson_slug = self.kwargs.get("lesson_slug")

        return (
            LessonContent.objects.filter(
                lesson__slug=lesson_slug,
                lesson__module__slug=module_slug,
                lesson__module__course__slug=course_slug,
            )
            .select_related("lesson__module__course")
            .order_by("order")
        )

    def get_object(self):
        content = super().get_object()
        lesson = content.lesson

        user_id = self.request.user_data.get("id", None)
        user_role = self.request.user_data.get("role", {}).get("name", None)

        if not self._check_edit_permissions(lesson, user_id, user_role):
            raise PermissionDenied("You don't have permission to edit this lesson")

        return content

    def perform_update(self, serializer):
        content = serializer.save()
        lesson = content.lesson

        CacheInvalidator.invalidate_lesson_cache(
            course_slug=lesson.module.course.slug,
            module_slug=lesson.module.slug,
            lesson_slug=lesson.slug,
        )

    def perform_destroy(self, instance):
        lesson = instance.lesson
        course_slug = lesson.module.course.slug
        module_slug = lesson.module.slug
        lesson_slug = lesson.slug

        super().perform_destroy(instance)

        CacheInvalidator.invalidate_lesson_cache(
            course_slug=course_slug,
            module_slug=module_slug,
            lesson_slug=lesson_slug,
        )


class LessonContentDisplayView(generics.RetrieveAPIView, LessonAccessMixin):
    """
    Отдельное View для отображения контента на странице урока.
    """

    serializer_class = LessonContentDisplaySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "content_id"

    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")
        lesson_slug = self.kwargs.get("lesson_slug")
        content_id = self.kwargs.get("content_id")

        return LessonContent.objects.filter(
            id=content_id,
            lesson__slug=lesson_slug,
            lesson__module__slug=module_slug,
            lesson__module__course__slug=course_slug,
        )

    def get_object(self):
        content = super().get_object()
        lesson = content.lesson

        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if not self._check_lesson_access(lesson, user_id, user_role):
            raise PermissionDenied("You don't have access to this lesson")

        return content

    def retrieve(self, request, *args, **kwargs):
        course_slug = kwargs.get("course_slug")
        module_slug = kwargs.get("module_slug")
        lesson_slug = kwargs.get("lesson_slug")
        content_id = kwargs.get("content_id")

        cache_key_prefix = f"lesson_content_display_{course_slug}_{module_slug}_{lesson_slug}_{content_id}"

        decorator = cache_response(timeout=300, key_prefix=cache_key_prefix)
        decorated_method = decorator(super().retrieve)
        return decorated_method(self, request, *args, **kwargs)


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

        return serializer

    def get_queryset(self):
        queryset = (
            Lesson.objects.select_related("module", "module__course")
            .prefetch_related(
                Prefetch(
                    "content",
                    queryset=LessonContent.objects.order_by("order"),
                    to_attr="content_prefetched",
                ),
                "tasks",
            )
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

    def get_queryset(self):
        """Оптимизированный queryset для детального просмотра урока"""
        return (
            Lesson.objects.select_related("module__course")
            .prefetch_related(
                Prefetch(
                    "content",
                    queryset=LessonContent.objects.order_by("order"),
                    to_attr="content_prefetched",
                ),
                "tasks",
            )
            .all()
        )


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
