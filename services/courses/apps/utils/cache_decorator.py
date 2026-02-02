from functools import wraps
from requests import Response

from apps.utils.cache_key_builder import CacheKeyBuilder


def cache_response(timeout=300, key_prefix=None, vary_on_user=False):
    """
    Декоратор для кэширования ответов DRF views

    Args:
        timeout (int): Время жизни кэша в секундах
        key_prefix (str): Префикс ключа кэша
        vary_on_user (bool): Разделять кэш по пользователям
    """

    def decorator(view_method):
        @wraps(view_method)
        def wrapper(view_instance, request, *args, **kwargs):
            from django.core.cache import cache

            # Строим ключ кэша
            if key_prefix:
                prefix = key_prefix
            else:
                prefix = f"{view_instance.__class__.__name__}_{view_method.__name__}"

            cache_key = CacheKeyBuilder.build_key(
                prefix=prefix, request=request, **kwargs
            )

            # Проверяем кэш
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return Response(cached_response)

            # Выполняем оригинальный метод
            response = view_method(view_instance, request, *args, **kwargs)

            # Кэшируем успешные ответы
            if response.status_code == 200:
                cache.set(cache_key, response.data, timeout)

            return response

        return wrapper

    return decorator
