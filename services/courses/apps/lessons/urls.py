from django.urls import path
from . import views


urlpatterns = [
    # ==================== УРОКИ ====================
    path("", views.LessonListView.as_view(), name="lesson-list"),
    path("<slug:lesson_slug>/", views.LessonDetailView.as_view(), name="lesson-detail"),
    # ==================== КОНТЕНТ УРОКОВ ====================
    path(
        "<slug:lesson_slug>/content/",
        views.LessonContentListView.as_view(),
        name="lesson-content-list",
    ),
    path(
        "<slug:lesson_slug>/content/<int:id>/",
        views.LessonContentDetailView.as_view(),
        name="lesson-content-detail",
    ),
]
