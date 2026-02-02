from django.forms import ValidationError
from rest_framework import generics, permissions, filters, serializers
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

from apps.utils.cache_decorator import cache_response
from apps.utils.cache_invalidator import CacheInvalidator

from .models import Category, Course, CourseMentor, EnrollmentCache
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseCreateUpdateSerializer,
    CourseMentorSerializer,
    EnrollmentSerializer,
    CategorySerializer,
    AdminEnrollmentSerializer,
)
from .filters import AdminCourseFilter, CourseFilter
from apps.utils.permission_checker import IsAuthenticated, IsMentor, IsAdmin


class CourseListView(generics.ListAPIView):
    """Каталог курсов - ТОЛЬКО опубликованные курсы для всех пользователей"""

    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = CourseFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "price", "lessons_count"]
    ordering = ["-created_at"]

    @cache_response(timeout=300, key_prefix="courses_list")
    def list(self, request, *args, **kwargs):
        """Кэшируем список курсов на 5 минут"""
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Course.objects.filter(status="published")

        return queryset.select_related("category")


class CategoryListView(generics.ListAPIView):
    """Список всех категорий"""

    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    @cache_response(timeout=600, key_prefix="categories_list")  # 10 минут
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Category.objects.all().order_by("name")


class CategoryDetailView(generics.RetrieveAPIView):
    """Детальная информация о категории"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    @cache_response(timeout=600, key_prefix="category_detail")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CategoryCoursesView(generics.ListAPIView):
    """Курсы определенной категории с фильтрацией"""

    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CourseFilter
    search_fields = ["title", "description"]

    @cache_response(timeout=300, key_prefix="category_courses")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        category_slug = self.kwargs.get("slug")

        category = get_object_or_404(Category, slug=category_slug)

        queryset = Course.objects.filter(
            status="published", category=category
        ).select_related("category")

        return queryset.order_by("-created_at")


class CourseDetailPublicView(generics.RetrieveAPIView):
    """Детальная информация об опубликованном курсе"""

    serializer_class = CourseDetailSerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]

    @cache_response(timeout=300, key_prefix="course_detail_public")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Course.objects.filter(status="published")
            .select_related("category")
            .prefetch_related(
                "mentors",
                "modules__lessons__content",
                "modules__lessons__tasks",
            )
        )

    def get_object(self):
        obj = super().get_object()

        if hasattr(obj, "modules_prefetched"):
            # modules уже prefetched
            for module in obj.modules_prefetched:
                if hasattr(module, "lessons_prefetched"):
                    for lesson in module.lessons_prefetched:
                        if hasattr(lesson, "content_prefetched"):
                            lesson.content_prefetched = lesson.content_prefetched

        return obj


class CourseDetailPrivateView(generics.RetrieveAPIView):
    """Детальная информация о курсе, если он не обязательно опубликован"""

    serializer_class = CourseDetailSerializer
    lookup_field = "slug"
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        cache_key_prefix = f"course_detail_private_{kwargs.get('slug')}"
        return cache_response(
            timeout=180, key_prefix=cache_key_prefix, vary_on_user=True
        )(super().retrieve)(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Course.objects.all()
            .select_related("owner_mentor", "category")
            .prefetch_related("mentors", "modules")
        )

    def get_object(self):
        course = super().get_object()

        if course.status == "published":
            return course

        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if user_role == "admin":
            return course

        if user_role == "mentor":
            is_owner = course.owner_mentor_id == user_id
            is_mentor = CourseMentor.objects.filter(
                course=course.id, mentor_id=user_id
            ).exists()

            if is_owner or is_mentor:
                return course

        raise PermissionDenied("You don't have access to this course")


class CourseCreateView(generics.CreateAPIView):
    """Создание курса (только для менторов)"""

    serializer_class = CourseCreateUpdateSerializer
    permission_classes = [IsMentor]

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        serializer.fields["owner_mentor_id"].read_only = True
        serializer.fields["owner_mentor_id"].required = False
        return serializer

    def perform_create(self, serializer):
        mentor_id = self.request.user_data.get("id")
        course = serializer.save(owner_mentor_id=mentor_id)

        CacheInvalidator.invalidate_course_cache(course_slug=course.slug)


class CourseUpdateView(generics.UpdateAPIView):
    """Редактирование курса (владелец или администратор)"""

    queryset = Course.objects.all()
    serializer_class = CourseCreateUpdateSerializer
    lookup_field = "slug"
    permission_classes = [IsMentor]

    def perform_update(self, serializer):
        course = serializer.save()

        CacheInvalidator.invalidate_course_cache(course_slug=course.slug)

    def get_object(self):
        course = super().get_object()
        user_id = self.request.user_data.get("id")
        user_role = self.request.user_data.get("role", {}).get("name")

        if user_role == "admin":
            return course

        if course.owner_mentor_id != user_id:
            raise PermissionDenied("You are not the owner of this course")

        return course


class CourseMentorsView(generics.ListCreateAPIView):
    """Управление менторами курса"""

    serializer_class = CourseMentorSerializer

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

    @cache_response(timeout=300, key_prefix="course_mentors")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        course_slug = self.kwargs.get("slug")
        course = get_object_or_404(Course, slug=course_slug)
        return CourseMentor.objects.filter(course=course)

    def perform_create(self, serializer):
        course_slug = self.kwargs.get("slug")
        course = get_object_or_404(Course, slug=course_slug)

        # Проверяем, является ли пользователь владельцем курса
        user_id = self.request.user_data.get("id")
        if course.owner_mentor_id != user_id:
            raise PermissionDenied("Only course owner can add mentors")

        course_mentor = serializer.save(course=course)

        CacheInvalidator.invalidate_course_cache(course_slug=course_slug)


class CourseMentorDeleteView(generics.DestroyAPIView):
    """Удаление ментора из курса"""

    queryset = CourseMentor.objects.all()
    permission_classes = [IsMentor]

    def perform_destroy(self, instance):
        course_slug = instance.course.slug
        super().perform_destroy(instance)

        CacheInvalidator.invalidate_course_cache(course_slug=course_slug)

    def get_object(self):
        course_slug = self.kwargs.get("slug")
        mentor_id = self.kwargs.get("mentor_id")

        course = get_object_or_404(Course, slug=course_slug)

        user_id = self.request.user_data.get("id")
        if course.owner_mentor_id != user_id:
            raise PermissionDenied("Only course owner can remove mentors")

        if mentor_id == course.owner_mentor_id:
            raise PermissionDenied("Cannot remove course owner")

        return get_object_or_404(CourseMentor, course=course, mentor_id=mentor_id)


class EnrollmentView(generics.CreateAPIView):
    """Запись на курс"""

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        course_slug = self.kwargs.get("slug")

        try:
            course = Course.objects.get(slug=course_slug)
            if course.status != "published":
                raise PermissionDenied("Course is not available for enrollment")
        except Course.DoesNotExist:
            raise NotFound("Course not found")

        user_id = self.request.user_data.get("id", None)

        if EnrollmentCache.objects.filter(user_id=user_id, course=course).exists():
            raise serializers.ValidationError("User already enrolled in this course.")

        price = course.price
        if price and price > 0:
            pass
            # payment_ok = verify_payment_for_enrollment(
            #     user_id=user_id, course_id=course.id
            # )
            # if not payment_ok:
            #     raise serializers.ValidationError(
            #         "Course requires payment. No confirmed payment found for this user/course."
            #     )

        enrollment = serializer.save(course=course, user_id=user_id)

        CacheInvalidator.invalidate_course_cache(course_slug=course_slug)


class MyEnrollmentsView(generics.ListAPIView):
    """Курсы, на которые записан текущий пользователь"""

    serializer_class = CourseListSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user_id = self.request.user_data.get("id")
        cache_key_prefix = f"my_enrollments_user_{user_id}"

        return cache_response(timeout=180, key_prefix=cache_key_prefix)(super().list)(
            request, *args, **kwargs
        )

    def get_queryset(self):
        user_id = self.request.user_data.get("id")
        return (
            Course.objects.filter(enrollments__user_id=user_id)
            .prefetch_related("enrollments")
            .order_by("-created_at")
        )


class MyCoursesView(generics.ListAPIView):
    """Курсы текущего пользователя как ментора"""

    serializer_class = CourseListSerializer
    permission_classes = [IsMentor]

    def list(self, request, *args, **kwargs):
        user_id = self.request.user_data.get("id")
        cache_key_prefix = f"my_courses_user_{user_id}"

        return cache_response(timeout=180, key_prefix=cache_key_prefix)(super().list)(
            request, *args, **kwargs
        )

    def get_queryset(self):
        mentor_id = self.request.user_data.get("id")

        return (
            Course.objects.filter(
                Q(owner_mentor_id=mentor_id) | Q(mentors__mentor_id=mentor_id)
            )
            .distinct()
            .order_by("-created_at")
        )


class AdminCourseManagementView(generics.ListCreateAPIView):
    """Полное управление курсами для администратора"""

    serializer_class = CourseCreateUpdateSerializer
    permission_classes = [IsAdmin]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AdminCourseFilter
    search_fields = ["title", "description", "owner_mentor_id"]
    ordering_fields = "__all__"
    ordering = ["-created_at"]

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        serializer.fields["owner_mentor_id"].read_only = False
        serializer.fields["owner_mentor_id"].required = True
        return serializer

    def get_queryset(self):
        return (
            Course.objects.all()
            .select_related("category")
            .prefetch_related("mentors", "enrollments")
        )


class AdminCourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальное управление курсом для администратора"""

    queryset = Course.objects.all()
    serializer_class = CourseCreateUpdateSerializer
    lookup_field = "id"
    permission_classes = [IsAdmin]


class AdminCategoryListView(generics.ListCreateAPIView):
    """Полное управление категориями для администратора"""

    serializer_class = CategorySerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]

    def get_queryset(self):
        return Category.objects.all().order_by("name")


class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальное управление категорией для администратора"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"

    def perform_destroy(self, instance):
        if instance.courses.exists():
            raise ValidationError(
                {
                    "error": "Cannot delete category with existing courses. "
                    "First move or delete the courses."
                }
            )
        instance.delete()


class AdminCourseMentorListView(generics.ListCreateAPIView):
    """Получение списка всех связей курс-ментор (для администратора)"""

    serializer_class = CourseMentorSerializer
    permission_classes = [IsAdmin]

    def get_serializer(self, *args, **kwargs):
        """Переопределяем для установки полей как read_only только при создании"""
        serializer = super().get_serializer(*args, **kwargs)

        if hasattr(serializer, "child"):
            child_serializer = serializer.child
            if hasattr(child_serializer, "fields"):
                if "course" in child_serializer.fields:
                    child_serializer.fields["course"].read_only = False
                    child_serializer.fields["course"].required = True
        elif hasattr(serializer, "fields"):
            if "course" in serializer.fields:
                serializer.fields["course"].read_only = False
                serializer.fields["course"].required = True

        return serializer

    def get_queryset(self):
        return CourseMentor.objects.select_related("course").order_by("-id")

    def get(self, request, *args, **kwargs):
        """
        Дополнительные фильтры:
        - ?course_slug=... - фильтрация по курсу
        - ?mentor_id=... - фильтрация по ментору
        """
        queryset = self.get_queryset()

        course_slug = request.query_params.get("course_slug")
        if course_slug:
            queryset = queryset.filter(course__slug=course_slug)

        mentor_id = request.query_params.get("mentor_id")
        if mentor_id:
            queryset = queryset.filter(mentor_id=mentor_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AdminCourseMentorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальное управление связью курс-ментор (для администратора)"""

    queryset = CourseMentor.objects.all()
    serializer_class = CourseMentorSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"

    def perform_destroy(self, instance):
        if instance.course.owner_mentor_id == instance.mentor_id:
            raise PermissionDenied("Cannot remove course owner from mentors")
        instance.delete()


class AdminEnrollmentListView(generics.ListCreateAPIView):
    """Получение списка всех записей на курсы (для администратора)"""

    serializer_class = AdminEnrollmentSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return EnrollmentCache.objects.select_related("course").order_by("-id")

    def get(self, request, *args, **kwargs):
        """
        Дополнительные фильтры:
        - ?course_slug=... - фильтрация по курсу
        - ?user_id=... - фильтрация по пользователю
        """
        queryset = self.get_queryset()

        course_slug = request.query_params.get("course_slug")
        if course_slug:
            queryset = queryset.filter(course__slug=course_slug)

        user_id = request.query_params.get("user_id")
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AdminEnrollmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальное управление записью на курс (для администратора)"""

    queryset = EnrollmentCache.objects.all()
    serializer_class = AdminEnrollmentSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"
