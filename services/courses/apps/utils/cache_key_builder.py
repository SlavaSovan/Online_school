import hashlib


class CacheKeyBuilder:
    """Построитель ключей для кэша"""

    @staticmethod
    def build_key(prefix, request=None, **kwargs):
        """
        Создает ключ кэша на основе префикса и параметров запроса

        Args:
            prefix (str): Префикс ключа
            request: Объект запроса Django
            **kwargs: Дополнительные параметры

        Returns:
            str: Ключ кэша
        """
        key_parts = [prefix]

        if request:
            # Добавляем параметры запроса
            if request.GET:
                key_parts.append(
                    f"query_{hashlib.md5(request.GET.urlencode().encode()).hexdigest()[:8]}"
                )

            # Добавляем user_id если есть
            if hasattr(request, "user_data") and request.user_data:
                user_id = request.user_data.get("id")
                if user_id:
                    key_parts.append(f"user_{user_id}")

        # Добавляем дополнительные параметры
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}_{value}")

        return "_".join(key_parts)
