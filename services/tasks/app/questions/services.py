from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.redis import RedisCacheClient
from app.questions.models import Question, AnswerOption
from app.questions.schemas import (
    QuestionCreateSchema,
    QuestionResponseSchema,
    QuestionStudentSchema,
    QuestionUpdateSchema,
)
from app.tasks.services import TaskService
from app.utils.enums import TaskType, QuestionType


class QuestionService:
    @staticmethod
    async def get_for_task_mentor(
        db: AsyncSession,
        task_id: UUID,
    ) -> List[QuestionResponseSchema]:
        """Получение вопросов для задачи с кэшированием"""
        cache_key = f"questions:mentor:task:{task_id}"
        cached = await RedisCacheClient.get(cache_key)

        if cached:
            return [QuestionResponseSchema(**item) for item in cached]

        result = await db.execute(
            select(Question)
            .where(Question.task_id == task_id)
            .order_by(Question.order)
            .options(selectinload(Question.options))
        )
        questions = result.scalars().all()

        schemas = [QuestionResponseSchema.model_validate(q) for q in questions]

        await RedisCacheClient.set(
            cache_key,
            [s.model_dump(mode="json") for s in schemas],
            ttl_seconds=600,
        )

        return schemas

    @staticmethod
    async def get_for_task_student(
        db: AsyncSession,
        task_id: UUID,
    ) -> List[QuestionStudentSchema]:
        """Получение вопросов для задачи для студента без правильных ответов."""
        cache_key = f"questions:student:task:{task_id}"
        cached = await RedisCacheClient.get(cache_key)

        if cached:
            return [QuestionStudentSchema(**item) for item in cached]

        result = await db.execute(
            select(Question)
            .where(Question.task_id == task_id)
            .order_by(Question.order)
            .options(selectinload(Question.options))
        )
        questions = result.scalars().all()

        # Создаем студенческие схемы без правильных ответов
        schemas = [QuestionStudentSchema.from_question(q) for q in questions]

        await RedisCacheClient.set(
            cache_key,
            [s.model_dump(mode="json") for s in schemas],
            ttl_seconds=600,
        )

        return schemas

    @staticmethod
    async def get_by_id_with_options(
        db: AsyncSession, question_id: int, as_orm: bool = False
    ) -> Optional[QuestionResponseSchema]:
        """Получить вопрос с загруженными опциями ответов"""
        if as_orm:
            result = await db.execute(
                select(Question)
                .where(Question.id == question_id)
                .options(selectinload(Question.options))
            )
            return result.scalar_one_or_none()

        cache_key = f"question:{question_id}"
        cached = await RedisCacheClient.get(cache_key)

        if cached:
            return QuestionResponseSchema(**cached)

        result = await db.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        question = result.scalar_one_or_none()

        if question:
            schema = QuestionResponseSchema.model_validate(question)
            await RedisCacheClient.set(
                cache_key, schema.model_dump(mode="json"), ttl_seconds=600
            )
            return schema

        return None

    @staticmethod
    async def get_by_id_with_options_or_404(
        db: AsyncSession,
        question_id: int,
    ) -> QuestionResponseSchema:
        """Получить вопрос с опциями или выбросить 404"""
        question = await QuestionService.get_by_id_with_options(db, question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question

    @staticmethod
    async def get_by_id_student(
        db: AsyncSession,
        question_id: int,
    ) -> Optional[QuestionStudentSchema]:
        """Получить вопрос для студента (без правильных ответов)."""
        cache_key = f"question:student:{question_id}"
        cached = await RedisCacheClient.get(cache_key)

        if cached:
            return QuestionStudentSchema(**cached)

        result = await db.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        question = result.scalar_one_or_none()

        if question:
            schema = QuestionStudentSchema.from_question(question)
            await RedisCacheClient.set(
                cache_key,
                schema.model_dump(mode="json"),
                ttl_seconds=600,
            )
            return schema

        return None

    @staticmethod
    async def create(
        db: AsyncSession,
        task_id: UUID,
        payload: QuestionCreateSchema,
    ) -> QuestionResponseSchema:
        task = await TaskService.get_by_id(db, task_id, as_orm=True)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.task_type != TaskType.TEST:
            raise ValueError("Questions allowed only for TEST tasks")

        question = Question(
            task_id=task_id,
            text=payload.text,
            order=payload.order,
            question_type=payload.question_type,
            correct_answers=payload.correct_answers,
        )

        db.add(question)
        await db.flush()

        if payload.options:
            if payload.question_type == QuestionType.SINGLE_CHOICE:
                correct_count = sum(1 for opt in payload.options if opt.is_correct)
                if correct_count != 1:
                    raise HTTPException(
                        status_code=400,
                        detail="SINGLE_CHOICE questions must have exactly one correct option",
                    )

            for opt in payload.options:
                answer_option = AnswerOption(
                    question_id=question.id,
                    text=opt.text,
                    is_correct=opt.is_correct,
                )
                db.add(answer_option)

        await db.commit()
        await db.refresh(question, ["options"])

        return QuestionResponseSchema.model_validate(question)

    @staticmethod
    async def update(
        db: AsyncSession,
        question_id: int,
        data: QuestionUpdateSchema,
    ) -> QuestionResponseSchema:
        question = await QuestionService.get_by_id_with_options(
            db, question_id, as_orm=True
        )

        if not question:
            raise HTTPException(404, "Question not found")

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "options":
                await db.execute(
                    AnswerOption.__table__.delete().where(
                        AnswerOption.question_id == question.id
                    )
                )
                for opt in value:
                    db.add(
                        AnswerOption(
                            question_id=question.id,
                            text=opt.text,
                            is_correct=opt.is_correct,
                        )
                    )
            else:
                setattr(question, field, value)

        await db.commit()
        await db.refresh(question)
        return QuestionResponseSchema.model_validate(question)

    @staticmethod
    async def delete(db: AsyncSession, question_id: int) -> None:
        result = await db.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        question = result.scalar_one_or_none()

        if not question:
            raise HTTPException(404, "Question not found")

        await db.delete(question)
        await db.commit()
