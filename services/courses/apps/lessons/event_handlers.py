import json
import time
import redis
import logging
from uuid import UUID
from django.conf import settings
from django.db import transaction

from apps.utils.cache_invalidator import CacheInvalidator

from .models import Lesson, LessonTask


logger = logging.getLogger(__name__)


def start_event_listener():
    logger.info("Starting Redis event listener...")

    redis_client = None

    while True:
        try:
            if redis_client is None:
                redis_client = redis.from_url(
                    url=settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=10,
                    socket_connect_timeout=10,
                    retry_on_timeout=True,
                )
                redis_client.ping()
                logger.info("Redis connection established")

            process_redis_event(redis_client)

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            redis_client = None
            time.sleep(5)

        except Exception as e:
            logger.error(f"Listener error: {e}")
            time.sleep(1)


def process_redis_event(redis_client):
    """Обработка событий Redis"""
    try:

        event_data = redis_client.blpop("tasks_events_queue", timeout=5)

        if not event_data:
            return

        _, message = event_data
        logger.info(f"Received message: {message}")

        try:
            event = json.loads(message)
            handle_event(event)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in message")

    except redis.TimeoutError:
        pass  # Ожидаемый таймаут, ничего не делаем
    except Exception as e:
        logger.error(f"Error processing event: {e}")


def handle_event(event_data):
    """Обработка событий"""
    event_type = event_data.get("type")
    data = event_data.get("data", {})

    handlers = {
        "task.created": handle_task_created,
        "task.updated": handle_task_updated,
        "task.deleted": handle_task_deleted,
    }

    handler = handlers.get(event_type)
    if handler:
        handler(data)
    else:
        logger.debug(f"Unhandled event type: {event_type}")


def _invalidate_lesson_cache(lesson_id):
    """
    Инвалидирует кэш урока и всех связанных данных
    """
    try:
        lesson = (
            Lesson.objects.filter(id=lesson_id).select_related("module__course").first()
        )

        if not lesson:
            logger.warning(f"Lesson {lesson_id} not found for cache invalidation")
            return

        if not lesson.module or not lesson.module.course:
            logger.warning(f"Lesson {lesson_id} has no module or course")
            return

        CacheInvalidator.invalidate_lesson_cache(
            course_slug=lesson.module.course.slug,
            module_slug=lesson.module.slug,
            lesson_slug=lesson.slug,
        )

        CacheInvalidator.invalidate_module_cache(
            course_slug=lesson.module.course.slug,
            module_slug=lesson.module.slug,
        )

        CacheInvalidator.invalidate_course_cache(lesson.module.course.slug)

        logger.info(f"Invalidated cache for lesson {lesson_id}")

    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")


def handle_task_created(data):
    try:
        lesson_id = data.get("lesson_id")
        title = data.get("title")
        task_id = data.get("task_id")
        order = data.get("order", 1)

        if not (lesson_id and title and task_id):
            logger.error("Missing required fields")
            return

        lesson = Lesson.objects.filter(id=lesson_id).first()

        if not lesson:
            logger.error(f"Lesson not found: {lesson_id}")
            return

        task_uuid = UUID(task_id)

        if LessonTask.objects.filter(task_uuid=task_uuid).exists():
            logger.info(f"LessonTask for task {task_uuid} already exists")
            return

        with transaction.atomic():
            lesson_task = LessonTask.objects.create(
                task_uuid=task_uuid,
                lesson=lesson,
                title=title,
                order=order,
            )

            logger.info(f"Created LessonTask: {lesson_task.id}")

        _invalidate_lesson_cache(lesson_id)

    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
    except Exception as e:
        logger.error(f"Create error: {e}")


def handle_task_updated(data):
    try:
        task_id = data.get("task_id")
        if not task_id:
            logger.error("Missing task_id in update data")
            return

        task_uuid = UUID(task_id)

        lesson_task = (
            LessonTask.objects.select_related("lesson__module__course")
            .filter(task_uuid=task_uuid)
            .first()
        )

        if not lesson_task:
            logger.warning(f"LessonTask not found")
            return

        old_lesson_id = lesson_task.lesson_id
        updated = False

        if "title" in data and data["title"]:
            lesson_task.title = data["title"]
            updated = True

        if "order" in data and data["order"]:
            lesson_task.order = data["order"]
            updated = True

        if "lesson_id" in data and data["lesson_id"]:
            lesson_id = data["lesson_id"]
            lesson = Lesson.objects.filter(id=lesson_id).first()

            if lesson:
                lesson_task.lesson = lesson
                updated = True
                logger.info(
                    f"Task {task_uuid} moved from lesson {old_lesson_id} to {lesson_id}"
                )
            else:
                logger.error(f"Target lesson {lesson_id} not found")

        if updated:
            lesson_task.save()
            logger.info(f"Updated LessonTask {lesson_task.id}")

            _invalidate_lesson_cache(old_lesson_id)
            _invalidate_lesson_cache(lesson_task.lesson_id)
        else:
            logger.debug(f"No changes for task {task_uuid}")

    except Exception as e:
        logger.error(f"Error updating task: {e}")


def handle_task_deleted(data):
    try:
        task_id = data.get("task_id")
        if not task_id:
            logger.error("Missing task_id in delete data")
            return

        task_uuid = UUID(task_id)

        lesson_task = LessonTask.objects.filter(task_uuid=task_uuid).first()

        if not lesson_task:
            logger.warning(f"LessonTask not found for task {task_uuid}")
            return

        lesson_id = lesson_task.lesson_id

        lesson_task.delete()

        logger.info(f"Deleted LessonTask {task_uuid}")

        _invalidate_lesson_cache(lesson_id)

    except Exception as e:
        logger.error(f"Error deleting task: {e}")
