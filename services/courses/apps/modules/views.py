from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from apps.utils.cache_decorator import cache_response
from apps.utils.cache_invalidator import CacheInvalidator

from .models import Module
from .serializers import ModuleDetailSerializer
from apps.courses.models import Course, CourseMentor, EnrollmentCache
from apps.utils.permission_checker import IsAuthenticated, IsMentor, IsAdmin


class ModuleListView(generics.ListCreateAPIView):
    """Список модулей курса + создание нового"""

    serializer_class = ModuleDetailSerializer

    def get_serializer(self, *args, **kwargs):
        """Переопределяем для установки полей как read_only только при создании"""
        serializer = super().get_serializer(*args, **kwargs)

        if hasattr(serializer, "child"):
            child_serializer = serializer.child
            if hasattr(child_serializer, "fields"):
                if "course" in child_serializer.fields:
                    child_serializer.fields["course"].read_only = True
                    child_serializer.fields["course"].required = False
        elif hasattr(serializer, "fields"):
            if "course" in serializer.fields:
                serializer.fields["course"].read_only = True
                serializer.fields["course"].required = False

        return serializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [IsMentor()]

    def list(self, request, *args, **kwargs):
        """Кэшируем список модулей"""
        course_slug = kwargs.get("course_slug")
        cache_key_prefix = f"modules_list_{course_slug}"

        return cache_response(timeout=300, key_prefix=cache_key_prefix)(super().list)(
            request, *args, **kwargs
        )

    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        course = get_object_or_404(Course, slug=course_slug)

        if course.status == "published":
            return Module.objects.filter(course=course).order_by("order")

        if not hasattr(self.request, "user_data") or not self.request.user_data:
            raise PermissionDenied("Authentication required")

        user_id = self.request.user_data.get("id", None)
        user_role = self.request.user_data.get("role", {}).get("name", None)

        if user_role == "admin":
            return Module.objects.filter(course=course).order_by("order")

        if user_role == "mentor":
            is_owner = course.owner_mentor_id == user_id
            is_mentor = CourseMentor.objects.filter(
                course=course, mentor_id=user_id
            ).exists()

            if is_owner or is_mentor:
                return Module.objects.filter(course=course).order_by("order")

        raise PermissionDenied("You don't have access to this course")

    def perform_create(self, serializer):
        course_slug = self.kwargs.get("course_slug")
        course = get_object_or_404(Course, slug=course_slug)

        if not hasattr(self.request, "user_data") or not self.request.user_data:
            raise PermissionDenied("Authentication required")

        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if user_role == "admin":
            serializer.save(course=course)
            CacheInvalidator.invalidate_module_cache(course_slug=course_slug)
            return

        if user_role != "mentor":
            raise PermissionDenied("Mentor role required")

        if course.owner_mentor_id != user_id:
            raise PermissionDenied("You don't have permission to edit this course")

        module = serializer.save(course=course)
        CacheInvalidator.invalidate_module_cache(course_slug=course_slug)


class ModuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали модуля, обновление, удаление"""

    serializer_class = ModuleDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsMentor()]

    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        module_slug = self.kwargs.get("module_slug")

        queryset = (
            Module.objects.filter(slug=module_slug, course__slug=course_slug)
            .select_related("course")
            .prefetch_related(
                "lessons__content",
                "lessons__tasks",
            )
        )

        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Кэшируем детали модуля"""
        course_slug = kwargs.get("course_slug")
        module_slug = kwargs.get("module_slug")
        cache_key_prefix = f"module_detail_{course_slug}_{module_slug}"

        return cache_response(timeout=300, key_prefix=cache_key_prefix)(
            super().retrieve
        )(request, *args, **kwargs)

    def get_object(self):
        queryset = self.get_queryset()

        if not queryset.exists():
            raise Response(
                data={"detail": "Module not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        module = queryset.first()

        if self.request.method == "GET":
            self._check_view_permissions

        return self._check_edit_permissions(module)

    def _check_view_permissions(self, module):
        """Проверка прав на просмотр модуля"""
        course = module.course
        user_id = self.request.user_data.get("id", None)
        user_role = self.request.user_data.get("role", {}).get("name", None)

        if user_role == "admin":
            return module

        if user_role == "mentor":
            if course.owner_mentor_id != user_id:
                if not CourseMentor.objects.filter(
                    course=course, mentor_id=user_id
                ).exists():
                    raise PermissionDenied("You don't have access to this module")
            return module

        if (
            course.status == "published"
            and EnrollmentCache.objects.filter(user_id=user_id, course=course).exists()
        ):
            return module

        raise PermissionDenied("You don't have access to this module")

    def _check_edit_permissions(self, module):
        course = module.course
        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if user_role == "admin":
            return module

        if user_role != "mentor":
            raise PermissionDenied("Mentor role required")

        if course.owner_mentor_id != user_id:
            raise PermissionDenied("You are not the owner of this course")

        return module

    def perform_update(self, serializer):
        module = serializer.save()

        CacheInvalidator.invalidate_module_cache(
            course_slug=module.course.slug, module_slug=module.slug
        )

    def perform_destroy(self, instance):
        course_slug = instance.course.slug
        module_slug = instance.slug
        super().perform_destroy(instance)

        CacheInvalidator.invalidate_module_cache(
            course_slug=course_slug, module_slug=module_slug
        )


class AdminModuleListView(generics.ListCreateAPIView):
    """Получение списка всех модулей для администратора с фильтрацией"""

    serializer_class = ModuleDetailSerializer
    permission_classes = [IsAdmin]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["title", "description", "course__title"]
    ordering_fields = ["order", "created_at", "updated_at", "course__title"]
    ordering = ["course__title", "order"]

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)

        if hasattr(serializer, "child"):
            child_serializer = serializer.child
            if hasattr(child_serializer, "fields"):
                if "course" in child_serializer.fields:
                    serializer.fields["course"].read_only = False
                    serializer.fields["course"].required = True
        elif hasattr(serializer, "fields"):
            if "course" in serializer.fields:
                serializer.fields["course"].read_only = False
                serializer.fields["course"].required = True

        return serializer

    def get_queryset(self):
        """Получаем все модули с оптимизацией запросов"""
        queryset = (
            Module.objects.select_related("course").prefetch_related("lessons").all()
        )

        course_slug = self.kwargs.get("course_slug")
        if course_slug:
            queryset = queryset.filter(course__slug=course_slug)

        return queryset

    def list(self, request, *args, **kwargs):
        """Добавляем статистику в ответ"""
        queryset = self.filter_queryset(self.get_queryset())
        course_slug = self.kwargs.get("course_slug")

        if course_slug:
            course = get_object_or_404(Course, slug=course_slug)
            course_info = {
                "id": course.id,
                "title": course.title,
                "slug": course.slug,
                "status": course.status,
            }

        total_modules = queryset.count()

        modules_with_stats = []
        for module in queryset:
            module_data = ModuleDetailSerializer(module).data
            module_data["lessons_count"] = module.lessons.count()
            modules_with_stats.append(module_data)

        page = self.paginate_queryset(queryset)
        if page is not None:
            modules_data = []
            for module in page:
                module_data = ModuleDetailSerializer(module).data
                module_data["lessons_count"] = module.lessons.count()
                modules_data.append(module_data)

            response = self.get_paginated_response(modules_data)
            response.data["total_modules"] = total_modules
            if course_info:
                response.data["course"] = course_info
            return response

        response_data = {
            "modules": modules_with_stats,
            "total_modules": total_modules,
        }
        if course_info:
            response_data["course"] = course_info

        return Response(response_data)


class AdminModuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальное управление модулем для администратора"""

    queryset = Module.objects.select_related("course").all()
    serializer_class = ModuleDetailSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"
