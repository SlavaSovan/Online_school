import json
from app.core.redis import RedisClient

QUEUE_KEY = "tasks_service:sandbox:queue"


async def enqueue_sandbox_task(submission_id: int):
    redis_client = await RedisClient.get_client()
    redis_client.rpush(
        QUEUE_KEY,
        json.dumps({"submission_id": submission_id}),
    )
