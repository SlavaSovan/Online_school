import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

from app.core.redis import RedisCacheClient
from app.tasks.models import Task
from app.tasks.schemas import (
    TestTaskCreateSchema,
    FileTaskCreateSchema,
    SandboxTaskCreateSchema,
    TaskReadSchema,
    TaskUpdateSchema,
)
from app.utils.events import (
    publish_task_created,
    publish_task_deleted,
    publish_task_updated,
)
from app.utils.enums import CodeLanguage, TaskType
from app.sandbox.models import CodeTask


class TaskService:
    @staticmethod
    async def get_by_id(
        db: AsyncSession, task_id: UUID, as_orm: bool = False
    ) -> TaskReadSchema:
        if as_orm:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            return task

        cache_key = f"task:{task_id}"

        cached = await RedisCacheClient.get(cache_key)
        if cached:
            return TaskReadSchema(**cached)

        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        dto = TaskReadSchema.model_validate(task)
        await RedisCacheClient.set(
            cache_key,
            dto.model_dump(mode="json"),
            ttl_seconds=300,
        )
        return dto

    @staticmethod
    async def create_test_task(
        db: AsyncSession, payload: TestTaskCreateSchema, lesson_id: int
    ) -> TaskReadSchema:
        task = Task(
            lesson_id=lesson_id,
            title=payload.title,
            description=payload.description,
            task_type=TaskType.TEST,
            order=payload.order,
            max_attempts=payload.max_attempts,
            max_score=payload.max_score,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        await publish_task_created(
            task_id=task.id,
            lesson_id=task.lesson_id,
            title=task.title,
            order=task.order,
        )

        return TaskReadSchema.model_validate(task)

    @staticmethod
    async def create_sandbox_task(
        db: AsyncSession, payload: SandboxTaskCreateSchema, lesson_id: int
    ) -> TaskReadSchema:
        task_id = uuid.uuid4()
        task = Task(
            id=task_id,
            lesson_id=lesson_id,
            title=payload.title,
            description=payload.description,
            task_type=TaskType.SANDBOX,
            order=payload.order,
            max_attempts=payload.max_attempts,
            max_score=payload.max_score,
        )

        db.add(task)

        code_task = CodeTask(task_id=task_id, language=CodeLanguage(payload.language))

        db.add(code_task)
        try:
            await db.commit()
            await db.refresh(task)
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create task")

        await publish_task_created(
            task_id=task.id,
            lesson_id=task.lesson_id,
            title=task.title,
            order=task.order,
        )

        return TaskReadSchema.model_validate(task)

    @staticmethod
    async def create_file_task(
        db: AsyncSession, payload: FileTaskCreateSchema, lesson_id: int
    ) -> TaskReadSchema:
        """Создание файлового задания"""
        task = Task(
            lesson_id=lesson_id,
            title=payload.title,
            description=payload.description,
            task_type=TaskType.FILE_UPLOAD,
            order=payload.order,
            max_attempts=payload.max_attempts,
            max_score=payload.max_score,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        await publish_task_created(
            task_id=task.id,
            lesson_id=task.lesson_id,
            title=task.title,
            order=task.order,
        )

        return TaskReadSchema.model_validate(task)

    @staticmethod
    async def update(
        db: AsyncSession, task_id: UUID, payload: TaskUpdateSchema
    ) -> TaskReadSchema:
        task = await TaskService.get_by_id(db, task_id, as_orm=True)

        if payload.max_attempts is not None and task.task_type == TaskType.SANDBOX:
            raise HTTPException(
                status_code=400,
                detail="SANDBOX tasks always have unlimited attempts. Cannot change max_attempts.",
            )

        try:
            data = payload.model_dump(exclude_unset=True)

            for key, value in data.items():
                setattr(task, key, value)

            db.add(task)
            await db.commit()
            await db.refresh(task)

            await publish_task_updated(task_id=task.id, update_data=data)

            return TaskReadSchema.model_validate(task)

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error")

    @staticmethod
    async def delete(db: AsyncSession, task_id: UUID) -> None:
        task = await TaskService.get_by_id(db, task_id, as_orm=True)
        await db.delete(task)
        await db.commit()

        await publish_task_deleted(task_id=task_id)
