from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("", include("apps.courses.urls")),
    path("courses/<slug:course_slug>/modules/", include("apps.modules.urls")),
    path(
        "courses/<slug:course_slug>/modules/<slug:module_slug>/lessons/",
        include("apps.lessons.urls"),
    ),
    path("admin/", include("apps.admin.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
