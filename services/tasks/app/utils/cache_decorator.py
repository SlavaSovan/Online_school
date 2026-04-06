from functools import wraps
from typing import Callable, List, Optional

from fastapi import Request
from app.core.redis import RedisCacheClient
import logging

logger = logging.getLogger(__name__)


def invalidate_cache(
    keys: Optional[List[str]] = None,
    before_call: bool = False,
    extract_user_from_request: bool = False,
    extract_from_result: Optional[List[str]] = None,
):
    """
    Простой декоратор для инвалидации кэша

    Args:
        keys: Список ключей для инвалидации
              Можно использовать {param_name} для подстановки
        before_call: Инвалидировать перед вызовом функции (для DELETE-запросов)
        extract_user_from_request: Получает user из запроса (для ключей, где нужен user_id)

    Примеры:
        @invalidate_cache(keys=["task:{task_id}"])
        @invalidate_cache(keys=["questions:task:{task_id}", "task:{task_id}"])
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            context = {**kwargs}

            if extract_user_from_request:
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

                if request and hasattr(request.state, "user_data"):
                    user_id = request.state.user_data.get("id")
                    if user_id:
                        context["user_id"] = user_id

            if before_call and keys:
                for key_template in keys:
                    key = _resolve_key(key_template, context)
                    if key:
                        if "*" in key:
                            await RedisCacheClient.delete_pattern(key)
                        else:
                            await RedisCacheClient.delete(key)
                        logger.debug(f"Invalidated cache (before): {key}")

            result = await func(*args, **kwargs)

            if extract_from_result:
                for field in extract_from_result:
                    if hasattr(result, field):
                        context[field] = getattr(result, field)
                    elif isinstance(result, dict) and field in result:
                        context[field] = result[field]

            if not before_call and keys:
                if isinstance(result, dict):
                    context.update(result)
                elif hasattr(result, "__dict__"):
                    context.update(result.__dict__)

                for key_template in keys:
                    key = _resolve_key(key_template, context)

                    if key:
                        if "*" in key:
                            await RedisCacheClient.delete_pattern(key)
                        else:
                            await RedisCacheClient.delete(key)
                        logger.debug(f"Invalidated cache key (after): {key}")
            return result

        return wrapper

    return decorator


def _resolve_key(key_template: str, context: dict) -> str:
    """Разрешение плейсхолдеров в ключе кэша"""
    key = key_template

    for param_name, param_value in context.items():
        placeholder = f"{{{param_name}}}"

        if placeholder in key:

            if hasattr(param_value, "id"):
                key = key.replace(placeholder, str(param_value.id))
            else:
                key = key.replace(placeholder, str(param_value))
    return key
