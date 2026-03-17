import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("SECRET_KEY", "")


DEBUG = True


def get_allowed_hosts():
    """Получение списка разрешенных хостов из переменной окружения"""
    hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "")
    if hosts:
        return [h.strip() for h in hosts.split(",") if h.strip()]
    return ["localhost", "127.0.0.1"]


ALLOWED_HOSTS = get_allowed_hosts()


DJANGO_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "storages",
]

LOCAL_APPS = [
    "apps.courses",
    "apps.modules",
    "apps.lessons",
    "apps.admin",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "core.urls"


WSGI_APPLICATION = "core.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "postgres"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DB = os.getenv("REDIS_DB", 1)
REDIS_CACHE_DB = os.getenv("REDIS_CACHE_DB", 2)

REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
REDIS_CACHE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CACHE_DB}"

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour"},
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


SECURE_BROWSER_XXS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


USER_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001")


AWS_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "course-content")
AWS_S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", None)
AWS_S3_REGION_NAME = os.getenv("S3_REGION", "us-east-1")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "private"  # Файлы приватные по умолчанию
AWS_QUERYSTRING_AUTH = True  # Используем signed URLs
AWS_QUERYSTRING_EXPIRE = 3600  # Срок жизни ссылок: 1 час

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 1024))
ALLOWED_CONTENT_TYPES = {
    "markdown": [".md", ".markdown"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
    "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm", ".m4v"],
    "file": [
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".zip",
        ".rar",
        ".txt",
        ".rtf",
        ".csv",
        ".json",
    ],
}


DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CACHE_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": 50,
                "timeout": 20,
            },
            "MAX_CONNECTIONS": 1000,
            "PICKLE_VERSION": -1,
        },
        "KEY_PREFIX": "courses_ms",  # Префикс для всех ключей
        "TIMEOUT": 300,  # Дефолтный таймаут
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
