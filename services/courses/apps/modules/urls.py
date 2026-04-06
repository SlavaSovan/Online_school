from django.urls import path
from . import views


urlpatterns = [
    path("modules", views.ModuleListView.as_view(), name="module-list"),
    path(
        "modules/<slug:module_slug>",
        views.ModuleDetailView.as_view(),
        name="module-detail",
    ),
]
