from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Optional, List, Dict, Any
import logging
from app.utils.services import CourseService
from app.utils.permission_checker import IsMentor

logger = logging.getLogger(__name__)


async def get_token_from_request(request: Request) -> str:
    """Извлекает токен из request state или заголовков"""
    if hasattr(request.state, "token"):
        return request.state.token

    bearer = HTTPBearer(auto_error=False)
    credentials = await bearer(request)

    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication token not provided")

    return credentials.credentials


class GetAllCoursesLessons:
    """Получение всех уроков из всех курсов с пагинацией"""

    async def __call__(self, request: Request) -> List[Dict[str, Any]]:
        token = await get_token_from_request(request)
        return await CourseService.get_all_lessons_from_all_courses(token)


class GetMentorCoursesLessons:
    """Получение всех уроков из курсов ментора с ограничениями"""

    async def __call__(
        self, request: Request, user: Dict[str, Any] = Depends(IsMentor())
    ) -> List[Dict[str, Any]]:
        mentor_id = user.get("id")
        if not mentor_id:
            raise HTTPException(status_code=400, detail="Mentor ID not found")

        token = await get_token_from_request(request)
        return await CourseService.get_mentor_courses_lessons(mentor_id, token)


class CheckMentorIsOwner:
    """Проверяет является ли ментор владельцем курса"""

    def __init__(self, course_slug: str):
        self.course_slug = course_slug

    async def __call__(
        self, request: Request, user: Dict[str, Any] = Depends(IsMentor())
    ) -> bool:
        mentor_id = user.get("id")
        if not mentor_id:
            raise HTTPException(status_code=400, detail="Mentor ID not found")

        token = await get_token_from_request(request)
        is_owner = await CourseService.check_mentor_is_owner(
            mentor_id, self.course_slug, token
        )

        if not is_owner:
            raise HTTPException(
                status_code=403,
                detail=f"Mentor is not the owner of course {self.course_slug}",
            )

        return True


class CheckMentorCourseAccess:
    """Проверка доступа ментора к курсу"""

    def __init__(self, course_slug: str):
        self.course_slug = course_slug

    async def __call__(
        self, request: Request, user: Dict[str, Any] = Depends(IsMentor())
    ) -> bool:
        mentor_id = user.get("id")
        if not mentor_id:
            raise HTTPException(status_code=400, detail="Mentor ID not found")

        token = await get_token_from_request(request)
        has_access = await CourseService.check_mentor_course_access(
            mentor_id, self.course_slug, token
        )

        if not has_access:
            raise HTTPException(
                status_code=403,
                detail=f"Mentor does not have access to course {self.course_slug}",
            )

        return True


class GetCourseInfoByLessonId:
    """Получение информации о курсе по lesson_id"""

    def __init__(self, lesson_id: int):
        self.lesson_id = lesson_id

    async def __call__(self, request: Request) -> Dict[str, Any]:
        token = await get_token_from_request(request)
        course_info = await CourseService.get_course_info_by_lesson_id(
            self.lesson_id, token
        )

        if not course_info:
            raise HTTPException(
                status_code=404,
                detail=f"Course not found for lesson with id {self.lesson_id}",
            )

        return course_info


class GetLessonDetail:
    """Получение детальной информации об уроке по slug"""

    def __init__(self, course_slug: str, module_slug: str, lesson_slug: str):
        self.course_slug = course_slug
        self.module_slug = module_slug
        self.lesson_slug = lesson_slug

    async def __call__(self, request: Request) -> Dict[str, Any]:
        token = await get_token_from_request(request)
        lesson_detail = await CourseService.get_lesson_detail(
            self.course_slug, self.module_slug, self.lesson_slug, token
        )

        if not lesson_detail:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Lesson '{self.lesson_slug}' not found in module "
                    f"'{self.module_slug}' of course '{self.course_slug}'"
                ),
            )

        return lesson_detail


class GetUserEnrolledCourses:
    """Получение курсов, на которые записан пользователь с пагинацией"""

    async def __call__(self, request: Request) -> List[Dict[str, Any]]:
        token = await get_token_from_request(request)
        courses = await CourseService.get_user_enrolled_courses(token)

        return courses


class CheckUserEnrolledInCourse:
    """Проверка, записан ли пользователь на курс"""

    def __init__(self, course_slug: str):
        self.course_slug = course_slug

    async def __call__(self, request: Request) -> bool:
        token = await get_token_from_request(request)
        is_enrolled = await CourseService.is_user_enrolled_in_course(
            self.course_slug, token
        )

        if not is_enrolled:
            raise HTTPException(
                status_code=403,
                detail=f"User is not enrolled in course {self.course_slug}",
            )

        return True
