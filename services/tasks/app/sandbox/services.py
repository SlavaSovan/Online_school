import asyncio
import json
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.submissions.models import Submission
from app.tasks.models import Task
from app.sandbox.models import CodeTask, SandboxExecution
from app.sandbox.utils.runner import DockerRunner
from app.tasks.services import TaskService
from app.utils.enums import SubmissionStatus, CodeLanguage, TaskType


class SandboxService:

    @staticmethod
    async def get_by_id_and_task_id(db: AsyncSession, code_task_id: int, task_id: UUID):
        code_task = await db.execute(
            select(CodeTask).where(
                CodeTask.id == code_task_id, CodeTask.task_id == task_id
            )
        )
        result = code_task.scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=404, detail="CodeTask not found")

        return result

    @staticmethod
    async def create_code_task(
        db: AsyncSession,
        task_id: UUID,
        language: CodeLanguage,
        template_code: str,
        tests_definition: dict,
        time_limit: int,
        memory_limit: int,
    ) -> CodeTask:
        task = await TaskService.get_by_id(db, task_id)

        existing = await db.execute(select(CodeTask).where(CodeTask.task_id == task_id))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="Code task already exists for this task"
            )

        if task.task_type != TaskType.SANDBOX:
            raise HTTPException(
                status_code=400,
                detail="Code tasks can only be created for SANDBOX tasks",
            )

        code_task = CodeTask(
            task_id=task_id,
            language=language,
            template_code=template_code,
            tests_definition=json.dumps(tests_definition),
            time_limit=time_limit,
            memory_limit=memory_limit,
        )

        db.add(code_task)
        await db.commit()
        await db.refresh(code_task)
        return code_task

    @staticmethod
    async def update_code_task(
        db: AsyncSession,
        code_task_id: int,
        task_id: UUID,
        data: dict,
    ) -> CodeTask:
        code_task = await SandboxService.get_by_id_and_task_id(
            db, code_task_id, task_id
        )
        for field, value in data.items():
            if field == "tests_definition" and value is not None:
                value = json.dumps(value)
            if value is not None:
                setattr(code_task, field, value)

        await db.commit()
        await db.refresh(code_task)
        return code_task

    @staticmethod
    async def delete_code_task(
        db: AsyncSession,
        code_task_id: int,
        task_id: UUID,
    ) -> None:
        code_task = await SandboxService.get_by_id_and_task_id(
            db, code_task_id, task_id
        )
        await db.delete(code_task)
        await db.commit()

    @staticmethod
    async def process_submission(
        db: AsyncSession,
        submission_id: int,
    ) -> None:
        """Обработка отправки кода в песочнице"""
        try:
            submission = await db.get(Submission, submission_id, with_for_update=True)
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")

            code_task_result = await db.execute(
                select(CodeTask).join(Task).where(Task.id == submission.task_id)
            )
            code_task = code_task_result.scalar_one_or_none()

            if not code_task:
                raise ValueError(f"Code task not found for submission {submission_id}")

            if code_task.language != CodeLanguage.PYTHON:
                submission.status = SubmissionStatus.FAILED
                submission.feedback = {
                    "error": f"Unsupported language: {code_task.language}"
                }
                await db.commit()
                return

            payload = submission.payload
            if payload.get("type") != "sandbox" or "code" not in payload:
                submission.status = SubmissionStatus.FAILED
                submission.feedback = {"error": "Invalid payload for sandbox task"}
                await db.commit()
                return

            user_code = payload["code"]

            if len(user_code) > 10000:
                submission.status = SubmissionStatus.FAILED
                submission.feedback = {"error": "Code size exceeds limit (10KB)"}
                await db.commit()
                return

            try:
                tests_definition = json.loads(code_task.tests_definition)
                function_name = tests_definition.get("function_name", "solution")
            except json.JSONDecodeError:
                submission.status = SubmissionStatus.FAILED
                submission.feedback = {"error": "Invalid tests definition"}
                await db.commit()
                return

            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        DockerRunner.run_python,
                        code=user_code,
                        tests=tests_definition,
                        function_name=function_name,
                        time_limit=code_task.time_limit,
                        memory_limit=code_task.memory_limit,
                    ),
                    timeout=code_task.time_limit + 5,  # Дополнительное время на запуск
                )

                submission.status = (
                    SubmissionStatus.PASSED
                    if result.success
                    else SubmissionStatus.FAILED
                )
                submission.feedback = {
                    "success": result.success,
                    "passed": result.passed,
                    "failed": result.failed,
                    "results": [r.__dict__ for r in result.results],
                }

                # Сохраняем execution
                execution = SandboxExecution(submission_id=submission.id, result=result)
                db.add(execution)

            except asyncio.TimeoutError:
                submission.status = SubmissionStatus.FAILED
                submission.feedback = {"error": "Execution timeout"}
            except Exception as e:
                submission.status = SubmissionStatus.FAILED
                submission.feedback = {"error": f"Execution error: {str(e)}"}

            await db.commit()

        except Exception as e:
            # Логируем ошибку
            print(f"Error processing submission {submission_id}: {e}")
            # Пробуем обновить статус submission
            try:
                if submission:
                    submission.status = SubmissionStatus.FAILED
                    submission.feedback = {"error": f"Processing error: {str(e)}"}
                    await db.commit()
            except:
                pass
            raise
