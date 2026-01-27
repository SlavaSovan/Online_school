import json
from uuid import UUID
import redis
import logging
from django.db import transaction, DatabaseError
from django.db.utils import IntegrityError
from django.conf import settings

from .models import Lesson, LessonTask


logger = logging.getLogger(__name__)


def process_redis_event():
    """Celery задача для обработки событий Redis"""
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

        event_data = redis_client.blpop("task_events_queue", timeout=30)

        if event_data:
            _, message = event_data
            try:
                event = json.loads(message)
                handle_event(event)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in message")

    except Exception as e:
        logger.error(f"Error in process_redis_event: {e}")


def handle_event(event_data):
    """Обработка событий"""
    event_type = event_data.get("type")
    data = event_data.get("data", {})

    event_handlers = {
        "task.created": handle_task_created,
        "task.updated": handle_task_updated,
        "task.deleted": handle_task_deleted,
    }

    handler = event_handlers.get(event_type)
    if handler:
        handler(data)
    else:
        logger.debug(f"Unhandled event type: {event_type}")


def handle_task_created(data):
    try:
        required_fields = ["title", "task_id", "lesson_id"]
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return
        lesson_id = data["lesson_id"]
        lesson = None

        if isinstance(lesson_id, int):
            lesson = Lesson.objects.filter(id=lesson_id).first()
        if not lesson:
            logger.error(f"Lesson not found for id: {lesson_id}")
            return

        try:
            task_uuid = UUID(data["task_id"])
        except (ValueError, TypeError):
            logger.error(f"Invalid UUID format: {data['task_id']}")
            return

        existing = LessonTask.objects.filter(
            task_uuid=task_uuid, lesson=lesson
        ).exists()

        if existing:
            logger.info(f"Task {task_uuid} already exists for lesson {lesson_id}")
            return

        with transaction.atomic():
            lesson_task = LessonTask.objects.create(
                title=data.get("title"),
                lesson=lesson,
                task_uuid=task_uuid,
                order=data.get("order", 1),
            )

            logger.info(f"Created LessonTask: {lesson_task.id} for task {task_uuid}")
            return lesson_task

    except IntegrityError as e:
        logger.error(f"Database integrity error: {e}")
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in handle_task_created: {e}")


def handle_task_updated(data):
    try:
        task_id = data.get("task_id")
        if not task_id:
            return

        try:
            task_uuid = UUID(task_id)
        except (ValueError, TypeError):
            return

        lesson_task = LessonTask.objects.filter(task_uuid=task_uuid).first()

        if not lesson_task:
            logger.warning(f"LessonTask not found for update: {task_id}")
            return

        update_fields = {}
        if "lesson_id" in data:
            lesson = None
            if isinstance(data["lesson_id"], int):
                lesson = Lesson.objects.filter(id=data["lesson_id"]).first()
            if not lesson:
                logger.error(f"Lesson not found for id: {data["lesson_id"]}")
                return
            update_fields["lesson"] = lesson
        if "title" in data:
            update_fields["title"] = data["title"]
        if "order" in data:
            update_fields["order"] = data["order"]

        if update_fields:
            for field, value in update_fields.items():
                setattr(lesson_task, field, value)
            lesson_task.save()
            logger.info(f"Updated LessonTask: {lesson_task.id}")
    except Exception as e:
        logger.error(f"Error updating task: {e}")


def handle_task_deleted(data):
    try:
        task_id = data.get("task_id")
        if not task_id:
            return

        try:
            task_uuid = UUID(task_id)
        except (ValueError, TypeError):
            return

        deleted_count, _ = LessonTask.objects.filter(task_uuid=task_uuid).delete()

        if deleted_count > 0:
            logger.info(f"Deleted LessonTask for task: {task_id}")
        else:
            logger.warning(f"LessonTask not found for deletion: {task_id}")

    except Exception as e:
        logger.error(f"Error deleting task: {e}")
