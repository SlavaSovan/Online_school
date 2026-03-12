from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.redis import RedisCacheClient
from app.tasks.models import Task
from app.tasks.schemas import TaskCreateSchema, TaskUpdateSchema
from app.utils.events import (
    publish_task_created,
    publish_task_deleted,
    publish_task_updated,
)


class TaskService:
    @staticmethod
    async def get_by_id(db: AsyncSession, task_id: UUID) -> Task:
        cache_key = f"task:{task_id}"

        cached = await RedisCacheClient.get(cache_key)
        if cached:
            task = Task(**cached)
            task.id = UUID(cached["id"])
            return task

        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        await RedisCacheClient.set(cache_key, task.to_dict(), ttl_seconds=300)
        return task

    @staticmethod
    async def create(
        db: AsyncSession, payload: TaskCreateSchema, lesson_id: int
    ) -> Task:
        task = Task(
            lesson_id=lesson_id,
            title=payload.title,
            description=payload.description,
            task_type=payload.task_type,
            order=payload.order,
            max_attempts=payload.max_attempts,
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

        return task

    @staticmethod
    async def update(db: AsyncSession, task: Task, data: TaskUpdateSchema) -> Task:
        for key, value in data.items():
            setattr(task, key, value)

        await db.commit()
        await db.refresh(task)

        await publish_task_updated(task_id=task.id, data=data)

        return task

    @staticmethod
    async def delete(db: AsyncSession, task: Task) -> None:
        task_id = task.id
        await db.delete(task)
        await db.commit()

        await publish_task_deleted(task_id=task_id)
