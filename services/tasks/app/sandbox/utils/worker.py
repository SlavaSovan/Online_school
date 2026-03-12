import asyncio
import json
import signal
import sys
import logging
import app.core.database as db
from app.core.redis import RedisClient
from app.sandbox.services import SandboxService

logger = logging.getLogger(__name__)

QUEUE_KEY = "sandbox:queue"
worker_stop = False


def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global worker_stop
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    worker_stop = True


async def process_task(submission_id: int):
    """Обработка одной задачи"""
    logger.info(f"Processing submission {submission_id}")

    db.init_db()

    async with db.async_session_maker() as session:
        try:
            await SandboxService.process_submission(session, submission_id)
            logger.info(f"Submission {submission_id} processed")
            return True
        except Exception as e:
            logger.error(f"Error processing submission {submission_id}: {e}")
            import traceback

            logger.debug(f"Traceback: {traceback.format_exc()}")
            return False
        finally:
            await session.close()


async def run_worker_async():
    """Асинхронный воркер"""
    logger.info("Sandbox async worker started")

    while not worker_stop:
        try:
            redis_client = await RedisClient.get_client()
            result = await redis_client.blpop(QUEUE_KEY, timeout=1)

            if result:
                _, raw = result
                payload = json.loads(raw)
                submission_id = payload["submission_id"]

                await process_task(submission_id)

        except Exception as e:
            if not worker_stop:  # Не логируем, если это остановка
                logger.error(f"Worker error: {e}")
                import traceback

                logger.debug(f"Traceback: {traceback.format_exc()}")

            await asyncio.sleep(1)  # Защита от busy loop

    logger.info("Worker stopped")


def run_worker():
    """Синхронная обертка для асинхронного воркера"""
    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Запуск асинхронного воркера
    try:
        asyncio.run(run_worker_async())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in worker: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_worker()
