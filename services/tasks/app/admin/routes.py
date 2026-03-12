from asyncio import Task
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db

from app.questions.models import Question
from app.questions.schemas import (
    QuestionCreateByAdminSchema,
    QuestionCreateSchema,
    QuestionResponseSchema,
    QuestionUpdateSchema,
)
from app.questions.services import QuestionService
from app.reviews.models import Review
from app.reviews.schemas import (
    ReviewCreateByAdminSchema,
    ReviewCreateSchema,
    ReviewResponseSchema,
    ReviewUpdateSchema,
)
from app.reviews.services import ReviewService

from app.sandbox.models import CodeTask, SandboxExecution
from app.sandbox.schemas import (
    CodeTaskCreateSchema,
    CodeTaskResponseSchema,
    CodeTaskUpdateSchema,
)
from app.sandbox.services import SandboxService
from app.sandbox.utils.result import SandboxResult
from app.submissions.models import Submission
from app.submissions.schemas import SubmissionResponseSchema
from app.submissions.services import SubmissionService
from app.tasks.schemas import (
    TaskCreateByAdminSchema,
    TaskCreateSchema,
    TaskResponseSchema,
    TaskUpdateSchema,
)
from app.tasks.services import TaskService
from app.utils.enums import SubmissionStatus, TaskType
from app.utils.permission_checker import IsAdmin

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(IsAdmin())],
)


# ============================= REVIEWS =============================


@admin_router.get(
    "/reviews/",
    response_model=List[ReviewResponseSchema],
)
async def admin_get_review(
    submission_id: Optional[int] = Query(None, description="Filter by submission ID"),
    mentor_id: Optional[int] = Query(None, description="Filter by mentor ID"),
    date_from: Optional[datetime] = Query(None, description="Filter by date from"),
    date_to: Optional[datetime] = Query(None, description="Filter by date to"),
    min_score: Optional[int] = Query(None, description="Filter by minimum score"),
    max_score: Optional[int] = Query(None, description="Filter by maximum score"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Review)

    if submission_id is not None:
        query = query.where(Review.submission_id == submission_id)

    if mentor_id is not None:
        query = query.where(Review.mentor_id == mentor_id)

    if date_from is not None:
        query = query.where(Review.reviewed_at >= date_from)

    if date_to is not None:
        query = query.where(Review.reviewed_at <= date_to)

    if min_score is not None:
        query = query.where(Review.score >= min_score)

    if max_score is not None:
        query = query.where(Review.score <= max_score)

    query = query.order_by(desc(Review.reviewed_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


@admin_router.post(
    "/reviews/",
    response_model=ReviewResponseSchema,
)
async def admin_create_review(
    payload: ReviewCreateByAdminSchema,
    db: AsyncSession = Depends(get_db),
):
    normal_payload = ReviewCreateSchema(score=payload.score, comment=payload.comment)
    return await ReviewService.create(
        db=db,
        submission_id=payload.submission_id,
        mentor_id=payload.mentor_id,
        payload=normal_payload,
    )


@admin_router.get(
    "/reviews/{review_id}/",
    response_model=ReviewResponseSchema,
)
async def admin_get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await ReviewService.get(db, review_id)


@admin_router.patch(
    "/reviews/{review_id}/",
    response_model=ReviewResponseSchema,
)
async def admin_update_review(
    review_id: int,
    payload: ReviewUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    review = await ReviewService.get(db, review_id)
    return await ReviewService.update(db=db, review=review, payload=payload)


@admin_router.delete(
    "/reviews/{review_id}/",
)
async def admin_delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    review = await ReviewService.get(db, review_id)
    await ReviewService.delete(db, review)
    return {"status": "deleted"}


# ============================= SANDBOX =============================


@admin_router.get("/code-tasks/", response_model=List[CodeTaskResponseSchema])
async def admin_list_code_tasks(
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    language: Optional[str] = Query(None, description="Filter by language"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    db: AsyncSession = Depends(get_db),
):
    query = select(CodeTask)

    if task_id is not None:
        query = query.where(CodeTask.task_id == task_id)

    if language is not None:
        query = query.where(CodeTask.language == language)

    query = query.order_by(desc(CodeTask.id)).offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


@admin_router.post("/code-tasks/", response_model=CodeTaskResponseSchema)
async def admin_create_code_task(
    payload: CodeTaskCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    return await SandboxService.create_code_task(
        db=db,
        task_id=payload.task_id,
        language=payload.language,
        template_code=payload.template_code,
        tests_definition=payload.tests_definition.model_dump(),
        time_limit=payload.time_limit,
        memory_limit=payload.memory_limit,
    )


@admin_router.get("/code-tasks/{code_task_id}/", response_model=CodeTaskResponseSchema)
async def admin_get_code_task(
    code_task_id: int,
    db: AsyncSession = Depends(get_db),
):
    code_task = await db.get(CodeTask, code_task_id)
    if not code_task:
        raise HTTPException(status_code=404, detail="Code task not found")
    return code_task


@admin_router.patch(
    "/code-tasks/{code_task_id}/", response_model=CodeTaskResponseSchema
)
async def admin_patch_code_task(
    code_task_id: int,
    payload: CodeTaskUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    code_task = await db.get(CodeTask, code_task_id)
    if not code_task:
        raise HTTPException(status_code=404, detail="Code task not found")

    data = payload.model_dump(exclude_unset=True)
    return await SandboxService.update_code_task(db, code_task, data)


@admin_router.delete("/code-tasks/{code_task_id}/")
async def admin_delete_code_task(
    code_task_id: int,
    db: AsyncSession = Depends(get_db),
):
    code_task = await db.get(CodeTask, code_task_id)
    if not code_task:
        raise HTTPException(status_code=404, detail="Code task not found")

    await SandboxService.delete_code_task(db, code_task)
    return {"status": "deleted"}


@admin_router.get("/executions/", response_model=List[SandboxResult])
async def admin_list_executions(
    submission_id: Optional[int] = Query(None, description="Filter by submission ID"),
    success: Optional[bool] = Query(None, description="Filter by success"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    db: AsyncSession = Depends(get_db),
):
    query = select(SandboxExecution)

    if submission_id is not None:
        query = query.where(SandboxExecution.submission_id == submission_id)

    if success is not None:
        query = query.where(SandboxExecution.result["success"].as_boolean() == success)

    query = query.order_by(desc(SandboxExecution.id)).offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


# ============================= SUBMISSIONS =============================


@admin_router.get("/submissions/", response_model=List[SubmissionResponseSchema])
async def admin_list_submissions(
    user_id: Optional[int] = Query(None),
    task_id: Optional[UUID] = Query(None),
    status: Optional[SubmissionStatus] = Query(None),
    task_type: Optional[TaskType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    db: AsyncSession = Depends(get_db),
):
    submissions = await SubmissionService.admin_list(
        db=db,
        user_id=user_id,
        task_id=task_id,
        status=status,
        task_type=task_type,
        skip=skip,
        limit=limit,
    )

    if date_from or date_to:
        filtered = []
        for submission in submissions:
            if date_from and submission.created_at < date_from:
                continue
            if date_to and submission.created_at > date_to:
                continue
            filtered.append(submission)
        return filtered

    return submissions


@admin_router.get(
    "/submissions/{submission_id}/", response_model=SubmissionResponseSchema
)
async def admin_get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
):
    submission = await SubmissionService.get_by_id(db, submission_id)
    return submission


@admin_router.delete("/submissions/{submission_id}/")
async def admin_delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
):
    submission = await SubmissionService.get_by_id(db, submission_id)

    await SubmissionService.admin_delete(db, submission)
    return {"status": "deleted"}


# ============================= QUESTIONS =============================


@admin_router.get("/questions/", response_model=List[QuestionResponseSchema])
async def list_questions(
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Question)

    if task_id:
        query = query.where(Question.task_id == task_id)

    if question_type:
        query = query.where(Question.question_type == question_type)

    query = query.order_by(Question.id.desc()).offset(skip).limit(limit)
    query = query.options(selectinload(Question.options))  # Оптимизация загрузки

    result = await db.execute(query)
    return list(result.scalars().all())


@admin_router.post("/questions/", response_model=QuestionResponseSchema)
async def admin_create_question(
    payload: QuestionCreateByAdminSchema,
    db: AsyncSession = Depends(get_db),
):
    create_payload = QuestionCreateSchema(**payload.model_dump(exclude={"task_id"}))
    return await QuestionService.create(
        db=db,
        task_id=UUID(payload.task_id),
        payload=create_payload,
    )


@admin_router.get("/questions/{question_id}/", response_model=QuestionResponseSchema)
async def admin_get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
):
    question = await QuestionService.get_by_id_with_options_or_404(db, question_id)
    return question


@admin_router.patch("/questions/{question_id}/", response_model=QuestionResponseSchema)
async def admin_update_question(
    question_id: int,
    payload: QuestionUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    question = await QuestionService.get_by_id_with_options_or_404(db, question_id)
    return await QuestionService.update(
        db,
        question,
        payload.model_dump(exclude_unset=True),
    )


@admin_router.delete("/questions/{question_id}/")
async def admin_delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
):
    question = await db.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    await QuestionService.delete(db, question)
    return {"status": "deleted"}


# ============================= QUESTIONS =============================


@admin_router.get("/tasks/", response_model=List[TaskResponseSchema])
async def admin_list_tasks(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    lesson_id: Optional[int] = Query(None, description="Filter by lesson ID"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    db: AsyncSession = Depends(get_db),
):

    query = select(Task)

    if is_active is not None:
        query = query.where(Task.is_active == is_active)

    if lesson_id is not None:
        query = query.where(Task.lesson_id == lesson_id)

    if task_type is not None:
        query = query.where(Task.task_type == task_type)

    query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


@admin_router.post("/tasks/", response_model=TaskResponseSchema)
async def admin_create_task(
    payload: TaskCreateByAdminSchema,
    db: AsyncSession = Depends(get_db),
):
    clean_payload = TaskCreateSchema(**payload.model_dump(exclude={"lesson_id"}))
    return await TaskService.create(db, clean_payload, payload.lesson_id)


@admin_router.patch("/tasks/{task_id}/", response_model=TaskResponseSchema)
async def admin_update_task(
    task_id: UUID,
    payload: TaskUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    task = await TaskService.get_by_id(db, task_id)

    data = payload.model_dump(exclude_unset=True)
    return await TaskService.update(db, task, data)


@admin_router.delete("/tasks/{task_id}/")
async def admin_delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    task = await TaskService.get_by_id(db, task_id)
    await TaskService.delete(db, task)
    return {"status": "deleted"}
