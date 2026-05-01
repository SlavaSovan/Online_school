from django.urls import path
from . import views


urlpatterns = [
    # ==================== КАТАЛОГ КУРСОВ ====================
    path("courses", views.CourseListView.as_view(), name="course-list"),
    path("courses/create", views.CourseCreateView.as_view(), name="course-create"),
    path(
        "courses/<slug:slug>/edit",
        views.CourseUpdateView.as_view(),
        name="course-update",
    ),
    path(
        "courses/<slug:slug>/delete",
        views.CourseDeleteView.as_view(),
        name="course-delete",
    ),
    path(
        "courses/<slug:slug>",
        views.CourseDetailPublicView.as_view(),
        name="course-detail-public",
    ),
    path(
        "courses/by-lesson/<int:lesson_id>",
        views.CourseByLessonIdView.as_view(),
        name="course-by-lesson-id",
    ),
    path(
        "private/courses/<slug:slug>",
        views.CourseDetailPrivateView.as_view(),
        name="course-detail-private",
    ),
    path(
        "private/courses",
        views.CourseListPrivateView.as_view(),
        name="course-private",
    ),
    # ==================== КАТЕГОРИИ ====================
    path("categories", views.CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>",
        views.CategoryDetailView.as_view(),
        name="category-detail",
    ),
    # ==================== ЛИЧНЫЕ ДАННЫЕ ====================
    path("my/courses", views.MyCoursesView.as_view(), name="my-courses"),
    path(
        "my/courses-owner", views.MyCoursesOwnerView.as_view(), name="my-courses-owner"
    ),
    path("my/enrollments", views.MyEnrollmentsView.as_view(), name="my-enrollments"),
    # ==================== МЕНТОРЫ КУРСА ====================
    path(
        "courses/<slug:slug>/course-mentors",
        views.CourseMentorsView.as_view(),
        name="course-mentors",
    ),
    path(
        "courses/<slug:slug>/course-mentors/<int:mentor_id>",
        views.CourseMentorDeleteView.as_view(),
        name="course-mentor-delete",
    ),
    # ==================== ЗАПИСЬ НА КУРСЫ ====================
    path(
        "courses/<slug:slug>/enroll", views.EnrollmentView.as_view(), name="enrollment"
    ),
]
