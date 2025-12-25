from django.urls import path
from . import views


urlpatterns = [
    path("", views.ModuleListView.as_view(), name="module-list"),
    path("<slug:module_slug>/", views.ModuleDetailView.as_view(), name="module-detail"),
]
