from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID


from app.core.database import get_db

from app.questions.schemas import (
    QuestionCreateSchema,
    QuestionResponseSchema,
    QuestionStudentSchema,
)
from app.questions.services import QuestionService

from app.tasks.models import Task
from app.tasks.services import TaskService
from app.utils.cache_decorator import invalidate_cache
from app.utils.permission_checker import IsAuthenticated, IsMentor
from app.utils.course_dependencies import (
    CheckMentorIsOwner,
    GetCourseInfoByLessonId,
    CheckUserEnrolledInCourse,
)


router = APIRouter(tags=["Questions"])


async def get_task_and_check_access(
    task_id: UUID, request: Request, db: AsyncSession, check_mentor: bool = False
) -> Task:
    """Общая функция для получения задачи и проверки доступа"""
    task = await TaskService.get_by_id(db, task_id)

    course_info = await GetCourseInfoByLessonId(task.lesson_id)(request)
    course_slug = course_info.get("slug")

    if not course_slug:
        raise HTTPException(status_code=404, detail="Course not found")

    if check_mentor:
        await CheckMentorIsOwner(course_slug=course_slug)(request)
    else:
        await CheckUserEnrolledInCourse(course_slug=course_slug)(request)

    return task


@router.post(
    "/tasks/{task_id}/questions",
    response_model=QuestionResponseSchema,
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=[
        "questions:mentor:task:{task_id}",
        "questions:student:task:{task_id}",
        "question:{id}",
        "question:student:{id}",
    ],
    extract_from_result=["id"],
)
async def mentor_create_question(
    task_id: UUID,
    payload: QuestionCreateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Ментор создаёт вопрос для тестового задания.
    """

    task = await get_task_and_check_access(task_id, request, db, check_mentor=True)
    question = await QuestionService.create(db=db, task_id=task.id, payload=payload)

    return question


@router.delete(
    "/tasks/{task_id}/questions/{question_id}",
    dependencies=[Depends(IsMentor())],
)
@invalidate_cache(
    keys=[
        "questions:mentor:task:{task_id}",
        "questions:student:task:{task_id}",
        "question:{question_id}",
        "question:student:{question_id}",
    ],
    before_call=True,
)
async def mentor_delete_question(
    task_id: UUID,
    question_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Ментор удаляет вопрос для тестового задания.
    """

    task = await get_task_and_check_access(task_id, request, db, check_mentor=True)
    await QuestionService.delete(db=db, question_id=question_id)

    return {"status": "deleted"}


@router.get(
    "/tasks/{task_id}/questions",
    response_model=List[QuestionResponseSchema],
    dependencies=[Depends(IsMentor())],
)
async def list_questions_for_task(
    task_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Получение вопроса для тестового задания (для ментора).
    """

    task = await get_task_and_check_access(task_id, request, db, check_mentor=True)
    questions = await QuestionService.get_for_task_mentor(db, task_id)
    return questions


@router.get(
    "/tasks/{task_id}/test",
    response_model=List[QuestionStudentSchema],
    dependencies=[Depends(IsAuthenticated())],
)
async def list_questions_for_task_student(
    task_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Получение вопросов для тестового задания (для студента).
    """
    task = await get_task_and_check_access(task_id, request, db, check_mentor=False)
    questions = await QuestionService.get_for_task_student(db, task_id)
    return questions
