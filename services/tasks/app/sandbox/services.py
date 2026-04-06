import asyncio
import logging
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sandbox.models import CodeTask
from app.sandbox.schemas import CodeRunResponseSchema, CodeTaskResponseSchema
from app.sandbox.runner import DockerRunner
from app.utils.enums import CodeLanguage


logger = logging.getLogger(__name__)


class SandboxService:

    @staticmethod
    async def get_code_task(
        db: AsyncSession,
        task_id: UUID,
    ) -> CodeTaskResponseSchema:
        """Получение кодовой задачи по ID задания"""
        result = await db.execute(select(CodeTask).where(CodeTask.task_id == task_id))
        code_task = result.scalar_one_or_none()

        if not code_task:
            raise HTTPException(
                status_code=404, detail="Code task not found for this task"
            )

        return CodeTaskResponseSchema.model_validate(code_task)

    @staticmethod
    async def execute_code(
        code: str,
        language: str,
    ) -> CodeRunResponseSchema:
        """
        Выполнение кода (без сохранения, без проверки прав).
        Использует фиксированные ограничения ресурсов.
        """
        try:
            if len(code) > 10000:
                return CodeRunResponseSchema(
                    success=False,
                    output="",
                    error="Code size exceeds limit (10KB)",
                )

            try:
                lang = CodeLanguage(language.lower())
            except ValueError:
                return CodeRunResponseSchema(
                    success=False,
                    output="",
                    error=f"Language {language} is not supported.",
                )

            # Пока поддерживаем только Python
            if lang != CodeLanguage.PYTHON:
                return CodeRunResponseSchema(
                    success=False,
                    output="",
                    error=f"Language {lang.value} is not yet implemented.",
                )

            result = await asyncio.wait_for(
                asyncio.to_thread(DockerRunner.run_python, code),
                timeout=7,
            )

            return CodeRunResponseSchema(
                success=result.success,
                output=result.output,
                error=result.error,
            )

        except asyncio.TimeoutError:
            return CodeRunResponseSchema(
                success=False,
                output="",
                error="Execution timeout (exceeded 7 seconds)",
            )
        except Exception as e:
            logger.error(f"Error executing code: {e}")
            return CodeRunResponseSchema(
                success=False,
                output="",
                error=f"Execution error",
            )
