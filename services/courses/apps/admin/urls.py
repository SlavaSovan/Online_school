from django.urls import path
from apps.courses import views as courses_views
from apps.modules import views as modules_views
from apps.lessons import views as lessons_views


courses_urlpatterns = [
    # ==================== КУРСЫ (админ) ====================
    path(
        "courses/",
        courses_views.AdminCourseManagementView.as_view(),
        name="admin-course-list",
    ),
    path(
        "courses/<int:id>/",
        courses_views.AdminCourseDetailView.as_view(),
        name="admin-course-detail",
    ),
    # ==================== КАТЕГОРИИ (админ) ====================
    path(
        "categories/",
        courses_views.AdminCategoryListView.as_view(),
        name="admin-category-list",
    ),
    path(
        "categories/<int:id>/",
        courses_views.AdminCategoryDetailView.as_view(),
        name="admin-category-detail",
    ),
    # ==================== МЕНТОРЫ (админ) ====================
    path(
        "course-mentors/",
        courses_views.AdminCourseMentorListView.as_view(),
        name="admin-course-mentor-list",
    ),
    path(
        "course-mentors/<int:id>/",
        courses_views.AdminCourseMentorDetailView.as_view(),
        name="admin-course-mentor-detail",
    ),
    # ==================== ЗАПИСИ НА КУРСЫ (админ) ====================
    path(
        "enrollments/",
        courses_views.AdminEnrollmentListView.as_view(),
        name="admin-enrollment-list",
    ),
    path(
        "enrollments/<int:id>/",
        courses_views.AdminEnrollmentDetailView.as_view(),
        name="admin-enrollment-detail",
    ),
]


modules_urlpatterns = [
    path(
        "modules/",
        modules_views.AdminModuleListView.as_view(),
        name="admin-module-list",
    ),
    path(
        "modules/<int:id>/",
        modules_views.AdminModuleDetailView.as_view(),
        name="admin-module-detail",
    ),
    path(
        "courses/<slug:course_slug>/modules/",
        modules_views.AdminModuleListView.as_view(),
        name="admin-course-lessons",
    ),
]


lessons_urlpatterns = [
    # ==================== УРОКИ (админ) ====================
    path(
        "lessons/",
        lessons_views.AdminLessonListView.as_view(),
        name="admin-lesson-list",
    ),
    path(
        "lessons/<int:id>/",
        lessons_views.AdminLessonDetailView.as_view(),
        name="admin-lesson-detail",
    ),
    # ==================== УРОКИ ПО КУРСУ (админ) ====================
    path(
        "courses/<slug:course_slug>/modules/<slug:module_slug>/lessons/",
        lessons_views.AdminLessonListView.as_view(),
        name="admin-module-lessons",
    ),
    # ==================== КОНТЕНТ УРОКОВ (админ) ====================
    path(
        "lesson-content/",
        lessons_views.AdminLessonContentListView.as_view(),
        name="admin-lesson-content-list",
    ),
    path(
        "lesson-content/<int:id>/",
        lessons_views.AdminLessonContentDetailView.as_view(),
        name="admin-lesson-content-detail",
    ),
]

urlpatterns = courses_urlpatterns + modules_urlpatterns + lessons_urlpatterns
