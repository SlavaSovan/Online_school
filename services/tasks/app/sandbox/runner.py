import io
import os
import logging
import tarfile
import docker
import tempfile
import docker.errors
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Результат выполнения кода"""

    success: bool
    output: str
    error: Optional[str] = None


@contextmanager
def get_docker_client():
    """Контекстный менеджер для docker клиента"""
    client = None
    try:
        client = docker.from_env(timeout=10)
        yield client
    except docker.errors.DockerException as e:
        raise RuntimeError(f"Docker error: {str(e)}")
    finally:
        if client:
            client.close()


class DockerRunner:
    TIME_LIMIT = 5  # секунд
    MEMORY_LIMIT = 256  # MB

    @staticmethod
    def run_python(
        code: str,
        time_limit: int = TIME_LIMIT,
        memory_limit: int = MEMORY_LIMIT,
    ) -> ExecutionResult:
        try:
            with get_docker_client() as client:
                container = client.containers.run(
                    image="sandbox-python:latest",
                    command=["python3", "-c", code],
                    # Ограничение ресурсов
                    mem_limit=f"{memory_limit}m",
                    memswap_limit=f"{memory_limit}m",  # Отключаем swap
                    cpu_period=100000,  # 0.1 CPU
                    cpu_quota=30000,  # 30% от периода
                    # Безопасность
                    network_mode="none",
                    read_only=True,
                    cap_drop=["ALL"],
                    security_opt=["no-new-privileges"],
                    user="1000:1000",
                    # Прочее
                    detach=True,
                    stdout=True,
                    stderr=True,
                )

                try:
                    result = container.wait(timeout=time_limit + 2)
                    logs = container.logs(
                        stdout=True,
                        stderr=True,
                    ).decode("utf-8", errors="ignore")

                    if result["StatusCode"] == 0:
                        return ExecutionResult(
                            success=True,
                            output=logs.rstrip(),
                            error=None,
                        )
                    else:
                        return ExecutionResult(
                            success=False,
                            output="",
                            error=logs or "Execution failed",
                        )
                finally:
                    try:
                        container.remove(force=True)
                    except:
                        pass

        except docker.errors.APIError as e:
            logger.warning(f"Docker error: {str(e)}")
            return ExecutionResult(
                success=False,
                output="",
                error="Docker error",
            )
        except Exception as e:
            logger.warning(f"Execution error: {str(e)}")
            return ExecutionResult(
                success=False,
                output="",
                error="Execution error",
            )
