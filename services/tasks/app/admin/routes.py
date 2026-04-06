from uuid import UUID
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.tasks.models import Task
from app.tasks.services import TaskService
from app.tasks.schemas import (
    TestTaskCreateByAdminSchema,
    TestTaskCreateSchema,
    SandboxTaskCreateByAdminSchema,
    SandboxTaskCreateSchema,
    FileTaskCreateByAdminSchema,
    FileTaskCreateSchema,
    TaskResponseSchema,
    TaskUpdateSchema,
)

from app.questions.models import Question
from app.questions.services import QuestionService
from app.questions.schemas import (
    QuestionCreateByAdminSchema,
    QuestionCreateSchema,
    QuestionResponseSchema,
    QuestionUpdateSchema,
)

from app.sandbox.models import CodeTask
from app.sandbox.schemas import CodeTaskResponseSchema

from app.submissions.schemas import SubmissionResponseSchema
from app.submissions.services import SubmissionService

from app.reviews.models import Review
from app.reviews.services import ReviewService
from app.reviews.schemas import (
    ReviewCreateByAdminSchema,
    ReviewCreateSchema,
    ReviewResponseSchema,
    ReviewUpdateSchema,
)

from app.utils.enums import CodeLanguage, QuestionType, SubmissionStatus, TaskType
from app.utils.permission_checker import IsAdmin
from app.utils.cache_decorator import invalidate_cache

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(IsAdmin())],
)


# ============================== TASKS ==============================


@admin_router.get("/tasks", response_model=List[TaskResponseSchema])
async def admin_list_tasks(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    lesson_id: Optional[int] = Query(None, description="Filter by lesson ID"),
    task_type: Optional[TaskType] = Query(None, description="Filter by task type"),
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
    tasks = result.scalars().all()
    return [TaskResponseSchema.model_validate(t) for t in tasks]


@admin_router.post("/tasks/test", response_model=TaskResponseSchema)
@invalidate_cache(keys=["task:*"])
async def admin_create_test_task(
    payload: TestTaskCreateByAdminSchema,
    db: AsyncSession = Depends(get_db),
):
    """Создание тестового задания (администратор)"""
    clean_payload = TestTaskCreateSchema(
        title=payload.title,
        description=payload.description,
        order=payload.order,
        max_attempts=payload.max_attempts,
        max_score=payload.max_score,
    )
    return await TaskService.create_test_task(db, clean_payload, payload.lesson_id)


@admin_router.post("/tasks/sandbox", response_model=TaskResponseSchema)
@invalidate_cache(keys=["task:*"])
async def admin_create_sandbox_task(
    payload: SandboxTaskCreateByAdminSchema,
    db: AsyncSession = Depends(get_db),
):
    """Создание sandbox задания (администратор)"""
    clean_payload = SandboxTaskCreateSchema(
        title=payload.title,
        description=payload.description,
        order=payload.order,
        max_attempts=payload.max_attempts,
        max_score=payload.max_score,
        language=payload.language,
    )
    return await TaskService.create_sandbox_task(db, clean_payload, payload.lesson_id)


@admin_router.post("/tasks/file", response_model=TaskResponseSchema)
@invalidate_cache(keys=["task:*"])
async def admin_create_file_task(
    payload: FileTaskCreateByAdminSchema,
    db: AsyncSession = Depends(get_db),
):
    """Создание файлового задания (администратор)"""
    clean_payload = FileTaskCreateSchema(
        title=payload.title,
        description=payload.description,
        order=payload.order,
        max_attempts=payload.max_attempts,
        max_score=payload.max_score,
    )
    return await TaskService.create_file_task(db, clean_payload, payload.lesson_id)


@admin_router.get("/tasks/{task_id}", response_model=TaskResponseSchema)
async def admin_get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    task = await TaskService.get_by_id(db, task_id)
    return TaskResponseSchema.model_validate(task)


@admin_router.patch("/tasks/{task_id}", response_model=TaskResponseSchema)
@invalidate_cache(keys=["task:{task_id}"])
async def admin_update_task(
    task_id: UUID,
    payload: TaskUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    return await TaskService.update(db, task_id, payload)


@admin_router.delete("/tasks/{task_id}")
@invalidate_cache(keys=["task:{task_id}"], before_call=True)
async def admin_delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await TaskService.delete(db, task_id)
    return {"status": "deleted"}


# ============================= SANDBOX =============================


@admin_router.get("/code-tasks", response_model=List[CodeTaskResponseSchema])
async def admin_list_code_tasks(
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    language: Optional[CodeLanguage] = Query(None, description="Filter by language"),
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
    code_tasks = result.scalars().all()
    return [CodeTaskResponseSchema.model_validate(ct) for ct in code_tasks]


@admin_router.get("/code-tasks/{code_task_id}", response_model=CodeTaskResponseSchema)
async def admin_get_code_task(
    code_task_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CodeTask).where(CodeTask.id == code_task_id))
    code_task = result.scalar_one_or_none()

    if not code_task:
        raise HTTPException(status_code=404, detail="Code task not found")

    return CodeTaskResponseSchema.model_validate(code_task)


# ============================= SUBMISSIONS =============================


@admin_router.get("/submissions", response_model=List[SubmissionResponseSchema])
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
            if date_from and submission.created_at.replace(
                tzinfo=None
            ) < date_from.replace(tzinfo=None):
                continue
            if date_to and submission.created_at.replace(tzinfo=None) > date_to.replace(
                tzinfo=None
            ):
                continue
            filtered.append(submission)
        submission = filtered

    return [SubmissionResponseSchema.from_orm(s) for s in submissions]


@admin_router.get(
    "/submissions/{submission_id}", response_model=SubmissionResponseSchema
)
async def admin_get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await SubmissionService.get_by_id(db, submission_id)


@admin_router.delete("/submissions/{submission_id}")
@invalidate_cache(
    keys=["submission:{submission_id}", "submissions:user:*:task:*"],
    before_call=True,
)
async def admin_delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
):
    await SubmissionService.admin_delete(db, submission_id)
    return {"status": "deleted"}


# ============================= QUESTIONS =============================


@admin_router.get("/questions", response_model=List[QuestionResponseSchema])
async def list_questions(
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    question_type: Optional[QuestionType] = Query(
        None, description="Filter by question type"
    ),
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
    query = query.options(selectinload(Question.options))

    result = await db.execute(query)
    questions = result.scalars().all()
    return [QuestionResponseSchema.model_validate(q) for q in questions]


@admin_router.post("/questions", response_model=QuestionResponseSchema)
@invalidate_cache(
    keys=[
        "questions:mentor:task:{task_id}",
        "questions:student:task:{task_id}",
    ],
    extract_from_result=["task_id"],
)
async def admin_create_question(
    payload: QuestionCreateByAdminSchema,
    db: AsyncSession = Depends(get_db),
):
    create_payload = QuestionCreateSchema(**payload.model_dump(exclude={"task_id"}))
    return await QuestionService.create(
        db=db,
        task_id=payload.task_id,
        payload=create_payload,
    )


@admin_router.get("/questions/{question_id}", response_model=QuestionResponseSchema)
async def admin_get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await QuestionService.get_by_id_with_options_or_404(db, question_id)


@admin_router.patch("/questions/{question_id}", response_model=QuestionResponseSchema)
@invalidate_cache(
    keys=[
        "question:{question_id}",
        "questions:mentor:task:{task_id}",
        "questions:student:task:{task_id}",
    ],
    extract_from_result=["task_id"],
)
async def admin_update_question(
    question_id: int,
    payload: QuestionUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    return await QuestionService.update(db, question_id, payload)


@admin_router.delete("/questions/{question_id}")
@invalidate_cache(
    keys=[
        "question:{question_id}",
        "questions:mentor:task:{task_id}",
        "questions:student:task:{task_id}",
    ],
    before_call=True,
    extract_from_result=["task_id"],
)
async def admin_delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
):
    question = await QuestionService.get_by_id_with_options(db, question_id)
    task_id = question.task_id

    await QuestionService.delete(db, question_id)
    return {"status": "deleted", "task_id": str(task_id)}


# ============================= REVIEWS =============================


@admin_router.get(
    "/reviews",
    response_model=List[ReviewResponseSchema],
)
async def admin_list_reviews(
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
    "/reviews",
    response_model=ReviewResponseSchema,
)
@invalidate_cache(
    keys=[
        "review:*",
        "review:submission:{submission_id}",
        "submission:{submission_id}",
    ],
    extract_from_result=["submission_id"],
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
    "/reviews/{review_id}",
    response_model=ReviewResponseSchema,
)
async def admin_get_review_by_id(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await ReviewService.get_by_id(db, review_id)


@admin_router.patch(
    "/reviews/{review_id}",
    response_model=ReviewResponseSchema,
)
@invalidate_cache(
    keys=[
        "review:*",
        "review:submission:{submission_id}",
        "submission:{submission_id}",
    ],
    extract_from_result=["submission_id"],
)
async def admin_update_review(
    review_id: int,
    payload: ReviewUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    return await ReviewService.update(db=db, review_id=review_id, payload=payload)


@admin_router.delete(
    "/reviews/{review_id}",
)
@invalidate_cache(
    keys=[
        "review:*",
        "review:submission:{submission_id}",
        "submission:{submission_id}",
    ],
    before_call=True,
    extract_from_result=["submission_id"],
)
async def admin_delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    review = await ReviewService.get_by_id(db, review_id)
    submission_id = review.submission_id

    await ReviewService.delete(db, review_id)
    return {"status": "deleted", "submission_id": str(submission_id)}
