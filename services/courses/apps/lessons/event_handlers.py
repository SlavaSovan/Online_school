import json
from uuid import UUID
import redis
import logging
from django.db import transaction, DatabaseError
from django.db.utils import IntegrityError
from django.conf import settings

from apps.utils.cache_invalidator import CacheInvalidator

from .models import Lesson, LessonTask


logger = logging.getLogger(__name__)


def process_redis_event():
    """Обработка событий Redis"""
    try:
        redis_client = redis.from_url(
            url=settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )

        event_data = redis_client.blpop("task_events_queue", timeout=10)

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


def _invalidate_lesson_cache(lesson_id):
    """
    Инвалидирует кэш урока и всех связанных данных
    """
    try:
        lesson = (
            Lesson.objects.filter(id=lesson_id).select_related("module__course").first()
        )
        if lesson and hasattr(lesson, "module") and hasattr(lesson.module, "course"):
            course_slug = lesson.module.course.slug
            module_slug = lesson.module.slug
            lesson_slug = lesson.slug

            CacheInvalidator.invalidate_lesson_cache(
                course_slug=course_slug,
                module_slug=module_slug,
                lesson_slug=lesson_slug,
            )

            CacheInvalidator.invalidate_module_cache(
                course_slug=course_slug, module_slug=module_slug
            )

            CacheInvalidator.invalidate_course_cache(course_slug=course_slug)

            logger.info(
                f"Invalidated cache for lesson {lesson_id} (course: {course_slug}, module: {module_slug})"
            )

    except Exception as e:
        logger.error(f"Error invalidating cache for lesson {lesson_id}: {e}")


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
            _invalidate_lesson_cache(lesson_id)
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

        lesson_task = (
            LessonTask.objects.select_related("lesson__module__course")
            .filter(task_uuid=task_uuid)
            .first()
        )

        if not lesson_task:
            logger.warning(f"LessonTask not found for update: {task_id}")
            return

        old_lesson_id = lesson_task.lesson_id
        lesson_id_changed = False

        update_fields = {}

        if "lesson_id" in data:
            lesson = None
            if isinstance(data["lesson_id"], int):
                lesson = Lesson.objects.filter(id=data["lesson_id"]).first()
            if not lesson:
                logger.error(f"Lesson not found for id: {data["lesson_id"]}")
                return
            update_fields["lesson"] = lesson
            lesson_id_changed = old_lesson_id != lesson.id

        if "title" in data:
            update_fields["title"] = data["title"]
        if "order" in data:
            update_fields["order"] = data["order"]

        if update_fields:
            for field, value in update_fields.items():
                setattr(lesson_task, field, value)
            lesson_task.save()

            logger.info(f"Updated LessonTask: {lesson_task.id}")

            if lesson_id_changed:
                _invalidate_lesson_cache(old_lesson_id)
            _invalidate_lesson_cache(lesson_task.lesson_id)

    except Exception as e:
        logger.error(f"Error updating task: {e}")


def handle_task_deleted(data):
    try:
        task_id = data.get("task_id")
        if not task_id:
            logger.warning("No task_id in delete data")
            return

        try:
            task_uuid = UUID(task_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid UUID format: {task_id}")
            return

        lesson_task = (
            LessonTask.objects.select_related("lesson__module__course")
            .filter(task_uuid=task_uuid)
            .first()
        )

        if not lesson_task:
            logger.warning(f"LessonTask not found for deletion: {task_id}")
            return

        lesson_id = lesson_task.lesson_id

        with transaction.atomic():
            deleted_count, _ = LessonTask.objects.filter(task_uuid=task_uuid).delete()

            if deleted_count > 0:
                logger.info(f"Deleted LessonTask for task: {task_id}")

                _invalidate_lesson_cache(lesson_id)
            else:
                logger.warning(f"LessonTask not found for deletion: {task_id}")

    except Exception as e:
        logger.error(f"Error deleting task: {e}")
