import redis
from django.http import JsonResponse
from django.db import connections
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


def health_check(request):
    # Check database connections
    db_ok = all(conn.cursor().execute("SELECT 1") for conn in connections.all())

    # Check cache connection
    cache_ok = False
    try:
        redis_client = redis.from_url(settings.REDIS_CACHE_URL)
        cache_ok = redis_client.ping()
    except (redis.exceptions.RedisError, KeyError):
        pass

    status = db_ok and cache_ok
    status_code = 200 if status else 503
    return JsonResponse({"status": "ok" if status else "unhealthy"}, status=status_code)


urlpatterns = [
    path("health/", health_check, name="health_check"),
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
