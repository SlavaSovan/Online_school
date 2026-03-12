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
    QuestionUpdateSchema,
)
from app.tasks.services import TaskService
from app.utils.enums import TaskType, QuestionType


class QuestionService:
    @staticmethod
    async def get_for_task(db: AsyncSession, task_id: UUID) -> List[Question]:
        """Получение вопросов для задачи с кэшированием"""
        cache_key = f"questions:task:{task_id}"

        cached = await RedisCacheClient.get(cache_key)
        if cached:
            questions = []
            for q_data in cached:
                question = Question(**q_data)
                if "options" in q_data:
                    question.options = [
                        AnswerOption(**opt_data) for opt_data in q_data["options"]
                    ]
                questions.append(question)
            return questions

        result = await db.execute(
            select(Question)
            .where(Question.task_id == task_id)
            .order_by(Question.order)
            .options(selectinload(Question.options))
        )
        questions = result.scalars().all()

        if questions:
            questions_data = [q.to_dict() for q in questions]
            await RedisCacheClient.set(cache_key, questions_data, ttl_seconds=600)

        return list(questions)

    @staticmethod
    async def get_by_id_with_options(
        db: AsyncSession, question_id: int
    ) -> Optional[Question]:
        """Получить вопрос с загруженными опциями ответов"""
        cache_key = f"question:{question_id}"

        cached = await RedisCacheClient.get(cache_key)
        if cached:
            question = Question(**cached)
            if "options" in cached:
                question.options = [
                    AnswerOption(**opt_data) for opt_data in cached["options"]
                ]
            return question

        result = await db.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        question = result.scalar_one_or_none()
        if question:
            await RedisCacheClient.set(
                cache_key, question.to_dict(include_options=True), ttl_seconds=600
            )
        return question

    @staticmethod
    async def get_by_id_with_options_or_404(
        db: AsyncSession, question_id: int
    ) -> Question:
        """Получить вопрос с опциями или выбросить 404"""
        question = await QuestionService.get_by_id_with_options(db, question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question

    @staticmethod
    async def create(
        db: AsyncSession, task_id: UUID, payload: QuestionCreateSchema
    ) -> Question:
        task = await TaskService.get_by_id(db, task_id)

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

        if "options" in payload and payload["options"]:
            if payload.question_type == QuestionType.SINGLE_CHOICE:
                correct_count = sum(1 for opt in payload.options if opt.is_correct)
                if correct_count != 1:
                    raise ValueError(
                        "SINGLE_CHOICE questions must have exactly one correct option"
                    )

            for opt in payload.options:
                db.add(
                    AnswerOption(
                        question_id=question.id,
                        text=opt.text,
                        is_correct=opt.is_correct,
                    )
                )

        await db.commit()
        await db.refresh(question, ["options"])
        return question

    @staticmethod
    async def update(
        db: AsyncSession,
        question_id: int,
        data: QuestionUpdateSchema,
    ) -> Question:
        question = await QuestionService.get_by_id_with_options_or_404(db, question_id)
        for field, value in data.items():
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
            elif field == "question_type":
                # При изменении типа вопроса очищаем ненужные данные
                setattr(question, field, value)
                if value not in [
                    QuestionType.SINGLE_CHOICE,
                    QuestionType.MULTIPLE_CHOICE,
                ]:
                    # Очищаем опции для не-выборных типов
                    await db.execute(
                        AnswerOption.__table__.delete().where(
                            AnswerOption.question_id == question.id
                        )
                    )
            else:
                setattr(question, field, value)

        await db.commit()
        await db.refresh(question)
        return question

    @staticmethod
    async def delete(db: AsyncSession, question_id: int):
        question = await QuestionService.get_by_id_with_options_or_404(db, question_id)
        await db.delete(question)
        await db.commit()
