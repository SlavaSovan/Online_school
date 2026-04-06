import json
import logging
from uuid import UUID
from typing import Any, Dict, Optional
from app.core.redis import RedisClient


logger = logging.getLogger(__name__)


async def _publish(queue_key: str, event_type: str, data: Dict[str, Any]):
    """
    Публикация события в Redis.
    """
    try:
        event_data = {
            "type": event_type,
            "data": data,
        }

        message = json.dumps(event_data)
        logger.info(
            f"Publishing event to queue '{queue_key}': {event_type}, data: {data}"
        )

        redis_client = await RedisClient.get_client()

        if not redis_client:
            logger.error("Redis client is None")
            return False

        result = await redis_client.rpush(queue_key, message)

        if result:
            logger.debug(f"Pushed event to list '{queue_key}': {event_type}")
            return True
        else:
            logger.error(f"Failed to push event to Redis list: '{queue_key}'")
            return False
    except Exception as e:
        logger.error(f"Failed to push event to Redis list: '{e}'")
        return False


async def publish_task_created(
    task_id: UUID,
    lesson_id: int,
    title: str,
    order: Optional[int] = None,
    queue_key: str = "tasks_events_queue",
):
    task_id_str = str(task_id)
    return await _publish(
        queue_key=queue_key,
        event_type="task.created",
        data={
            "task_id": task_id_str,
            "lesson_id": lesson_id,
            "title": title,
            "order": order or 1,
        },
    )


async def publish_task_updated(
    task_id: UUID,
    update_data: Dict[str, Any],
    queue_key: str = "tasks_events_queue",
):
    task_id_str = str(task_id)
    return await _publish(
        queue_key=queue_key,
        event_type="task.updated",
        data={
            "task_id": task_id_str,
            **update_data,
        },
    )


async def publish_task_deleted(task_id: UUID, queue_key: str = "tasks_events_queue"):
    task_id_str = str(task_id)
    return await _publish(
        queue_key=queue_key,
        event_type="task.deleted",
        data={"task_id": task_id_str},
    )
