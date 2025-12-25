from django.urls import path
from . import views


urlpatterns = [
    # ==================== КАТАЛОГ КУРСОВ ====================
    path("courses/", views.CourseListView.as_view(), name="course-list"),
    path("courses/create/", views.CourseCreateView.as_view(), name="course-create"),
    path(
        "courses/<slug:slug>/edit/",
        views.CourseUpdateView.as_view(),
        name="course-update",
    ),
    path(
        "courses/<slug:slug>/",
        views.CourseDetailPublicView.as_view(),
        name="course-detail-public",
    ),
    path(
        "private/courses/<slug:slug>/",
        views.CourseDetailPrivateView.as_view(),
        name="course-detail-private",
    ),
    # ==================== КАТЕГОРИИ ====================
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>/",
        views.CategoryDetailView.as_view(),
        name="category-detail",
    ),
    path(
        "categories/<slug:slug>/courses/",
        views.CategoryCoursesView.as_view(),
        name="category-courses",
    ),
    # ==================== ЛИЧНЫЕ ДАННЫЕ ====================
    path("my/courses/", views.MyCoursesView.as_view(), name="my-courses"),
    path("my/enrollments/", views.MyEnrollmentsView.as_view(), name="my-enrollments"),
    # ==================== МЕНТОРЫ КУРСА ====================
    path(
        "courses/<slug:slug>/course-mentors/",
        views.CourseMentorsView.as_view(),
        name="course-mentors",
    ),
    path(
        "courses/<slug:slug>/course-mentors/<int:mentor_id>/",
        views.CourseMentorDeleteView.as_view(),
        name="course-mentor-delete",
    ),
    # ==================== ЗАПИСЬ НА КУРСЫ ====================
    path(
        "courses/<slug:slug>/enroll/", views.EnrollmentView.as_view(), name="enrollment"
    ),
]
