from django.urls import path
from . import views


urlpatterns = [
    # ==================== УРОКИ ====================
    path("lessons", views.LessonListView.as_view(), name="lesson-list"),
    path(
        "lessons/<slug:lesson_slug>",
        views.LessonDetailView.as_view(),
        name="lesson-detail",
    ),
    # ==================== КОНТЕНТ УРОКОВ ====================
    path(
        "lessons/<slug:lesson_slug>/content",
        views.LessonContentListView.as_view(),
        name="lesson-content-list",
    ),
    path(
        "lessons/<slug:lesson_slug>/content/<int:id>",
        views.LessonContentDetailView.as_view(),
        name="lesson-content-detail",
    ),
    path(
        "lessons/<slug:lesson_slug>/content/<int:content_id>/display",
        views.LessonContentDisplayView.as_view(),
        name="lesson-content-display",
    ),
]
