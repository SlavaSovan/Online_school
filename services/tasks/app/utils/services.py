import httpx
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.redis import RedisCacheClient


logger = logging.getLogger(__name__)


class HTTPClient:
    """Клиент для HTTP запросов с кешированием и пулом соединений"""

    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=100),
                transport=httpx.AsyncHTTPTransport(retries=3),
            )
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.aclose()
            cls._client = None


class UserService:
    """Сервис для взаимодействия с User Service"""

    @staticmethod
    async def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе по токену"""
        cache_key = f"user_token:{token[:20]}"

        cached = await RedisCacheClient.get(cache_key)
        if cached:
            return cached

        try:
            client = await HTTPClient.get_client()
            headers = {"Authorization": f"Bearer {token}"}

            response = await client.get(
                f"{settings.USER_SERVICE_URL}/auth/profile",
                headers=headers,
                timeout=10.0,
            )

            if response.status_code == 200:
                user_data = response.json()
                await RedisCacheClient.set(cache_key, user_data, ttl_seconds=300)
                return user_data

        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"Failed to get user: {e}")

        return None


class CourseService:
    """Сервис для взаимодействия с курсами"""

    @staticmethod
    async def _make_request(url: str, token: str) -> Optional[Dict[str, Any]]:
        """Общий метод для выполнения асинхронных запросов с кешированием"""

        try:
            client = await HTTPClient.get_client()
            headers = {"Authorization": f"Bearer {token}"}

            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Resource not found: {url}")
                return None
            else:
                logger.error(f"Request failed: {url}, status: {response.status_code}")
                return None

        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"Failed to make request: {e}")
            return None

    @staticmethod
    async def get_all_courses(token: str) -> List[Dict[str, Any]]:
        """Получение всех курсов с пагинацией"""
        data = await CourseService._make_request(
            f"{settings.COURSE_SERVICE_URL}/courses", token
        )

        if data and isinstance(data, dict):
            return data.get("results", [])
        return []

    @staticmethod
    async def get_course_detail(
        course_slug: str, token: str
    ) -> Optional[Dict[str, Any]]:
        """Получение детальной информации о курсе"""
        return await CourseService._make_request(
            f"{settings.COURSE_SERVICE_URL}/courses/{course_slug}", token
        )

    @staticmethod
    async def get_lesson_detail(
        course_slug: str, module_slug: str, lesson_slug: str, token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации об уроке по его slug.
        """
        url = (
            f"{settings.COURSE_SERVICE_URL}/courses/{course_slug}/"
            f"modules/{module_slug}/lessons/{lesson_slug}"
        )
        return await CourseService._make_request(url, token)

    @staticmethod
    async def get_course_mentors(course_slug: str, token: str) -> List[Dict[str, Any]]:
        """Получение информации о менторах курса"""
        data = await CourseService._make_request(
            f"{settings.COURSE_SERVICE_URL}/courses/{course_slug}/course-mentors", token
        )
        return data if data else []

    @staticmethod
    async def get_user_enrolled_courses(token: str) -> List[Dict[str, Any]]:
        """
        Получение списка курсов, на которые записан текущий пользователь.
        """
        data = await CourseService._make_request(
            f"{settings.COURSE_SERVICE_URL}/my/enrollments", token
        )
        if data and isinstance(data, dict):
            return data.get("results", [])
        return []

    @staticmethod
    async def get_all_lessons_from_all_courses(
        token: str,
    ) -> List[Dict[str, Any]]:
        """
        Получение всех уроков, принадлежащих всем курсам.
        Возвращает список всех уроков из всех курсов.
        """
        all_courses = await CourseService.get_all_courses(token)
        all_lessons = []

        for course in all_courses:
            course_slug = course.get("slug")
            if not course_slug:
                continue

            course_detail = await CourseService.get_course_detail(course_slug, token)
            if not course_detail:
                continue

            modules = course_detail.get("modules", [])
            for module in modules:
                lessons = module.get("lessons", [])
                for lesson in lessons:
                    lesson["course_info"] = {
                        "id": course_detail.get("id"),
                        "slug": course_slug,
                        "title": course_detail.get("title"),
                    }
                    all_lessons.append(lesson)

        return all_lessons

    @staticmethod
    async def get_mentor_courses_lessons(
        mentor_id: int, token: str
    ) -> List[Dict[str, Any]]:
        """
        Получение всех уроков, принадлежащих курсам, которыми владеет ментор.
        """
        all_courses = await CourseService.get_all_courses(token)
        mentor_lessons = []

        for course in all_courses:
            if course.get("owner_mentor_id") == mentor_id:
                course_slug = course.get("slug")
                if course_slug:
                    course_detail = await CourseService.get_course_detail(
                        course_slug, token
                    )
                    if course_detail and "lessons" in course_detail:
                        for lesson in course_detail["lessons"]:
                            lesson["course_info"] = {
                                "id": course.get("id"),
                                "slug": course_slug,
                                "title": course.get("title"),
                            }
                        mentor_lessons.extend(course_detail["lessons"])

        return mentor_lessons

    @staticmethod
    async def check_mentor_is_owner(
        mentor_id: int,
        course_slug: str,
        token: str,
    ) -> bool:
        """
        Проверяет, является ли ментор владельцем курса.
        """
        course_detail = await CourseService.get_course_detail(course_slug, token)
        if not course_detail:
            return False

        return course_detail.get("owner_mentor_id") == mentor_id

    @staticmethod
    async def check_mentor_course_access(
        mentor_id: int, course_slug: str, token: str
    ) -> bool:
        """
        Проверяет, имеет ли ментор доступ к курсу.
        Ментор имеет доступ если:
        1. Он владелец курса (owner_mentor_id == mentor_id)
        2. Он связан с курсом через таблицу course_mentors
        """

        course_detail = await CourseService.get_course_detail(course_slug, token)
        if not course_detail:
            return False

        if course_detail.get("owner_mentor_id") == mentor_id:
            return True

        course_mentors = await CourseService.get_course_mentors(course_slug, token)

        for mentor in course_mentors:
            if mentor.get("user_id") == mentor_id and mentor.get("is_active", False):
                return True

        return False

    @staticmethod
    async def get_course_info_by_lesson_id(
        lesson_id: int,
        token: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Получение полной информации о курсе по lesson_id.
        Возвращает словарь с информацией о курсе, содержащем данный урок.
        """
        all_courses = await CourseService.get_all_courses(token)

        for course in all_courses:
            course_slug = course.get("slug")
            if not course_slug:
                continue

            # Получаем детальную информацию о курсе
            course_detail = await CourseService.get_course_detail(course_slug, token)
            if not course_detail:
                continue

            # Ищем урок в модулях курса
            modules = course_detail.get("modules", [])
            for module in modules:
                lessons = module.get("lessons", [])
                for lesson in lessons:
                    if lesson.get("id") == lesson_id:
                        # Нашли нужный урок
                        return {
                            "course_id": course_detail.get("id"),
                            "course_slug": course_detail.get("slug"),
                            "course_title": course_detail.get("title"),
                            "module_info": {
                                "id": module.get("id"),
                                "slug": module.get("slug"),
                                "title": module.get("title"),
                            },
                            "lesson_info": {
                                "id": lesson.get("id"),
                                "title": lesson.get("title"),
                                "slug": lesson.get("slug"),
                            },
                        }

        logger.warning(f"Lesson {lesson_id} not found in any course")
        return None

    @staticmethod
    async def is_user_enrolled_in_course(course_slug: str, token: str) -> bool:
        """
        Проверяет, записан ли пользователь на конкретный курс.
        """
        enrolled_courses = await CourseService.get_user_enrolled_courses(token)

        for course in enrolled_courses:
            if course.get("slug") == course_slug:
                return True

        return False
