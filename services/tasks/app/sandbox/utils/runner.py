from contextlib import contextmanager
import time
from typing import Dict
import docker
import tempfile
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from app.sandbox.utils.result import SandboxResult, SingleTestResult


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

    @staticmethod
    def run_python(
        code: str,
        tests: dict,
        function_name: str,
        time_limit: int,
        memory_limit: int,
        output_limit: int = 5000,
    ) -> SandboxResult:

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Генерируем runner.py из шаблона
            try:
                template_dir = Path(__file__).resolve().parent.parent / "templates"
                env = Environment(loader=FileSystemLoader(str(template_dir)))
                template = env.get_template("python_runner.py.j2")

                runner_code = template.render(
                    user_code=code,
                    tests=json.dumps(tests),
                    function_name=function_name,
                )

                runner_path = tmpdir / "runner.py"
                runner_path.write_text(runner_code)
            except Exception as e:
                return SandboxResult(
                    success=False,
                    passed=0,
                    failed=len(tests.get("tests", [])),
                    results=[],
                    raw_stdout=f"Template error: {str(e)}",
                    raw_stderr=None,
                )

            # Запускаем контейнер
            try:
                with get_docker_client() as client:
                    container = client.containers.run(
                        image="sandbox-python:latest",
                        command="python /sandbox/runner.py",
                        volumes={str(tmpdir): {"bind": "/sandbox", "mode": "ro"}},
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
                        # Прочее
                        detach=True,
                        remove=False,
                        stdout=True,
                        stderr=True,
                        environment={
                            "PYTHONPATH": "/sandbox",
                            "PYTHONDONTWRITEBYTECODE": "1",
                        },
                    )

                    try:
                        # Ждем завершения с таймаутом
                        start_time = time.time()
                        while True:
                            try:
                                container.reload()
                                if container.status in ["exited", "dead"]:
                                    break
                            except docker.errors.NotFound:
                                break

                            if time.time() - start_time > time_limit + 5:
                                container.kill()
                                return SandboxResult(
                                    success=False,
                                    passed=0,
                                    failed=len(tests.get("tests", [])),
                                    results=[],
                                    raw_stdout="Execution timeout",
                                    raw_stderr=None,
                                )

                            time.sleep(0.1)

                        # Получаем логи
                        logs = container.logs(
                            stdout=True, stderr=True, tail=1000
                        ).decode("utf-8", errors="ignore")

                        exit_code = container.attrs["State"]["ExitCode"]

                        # Парсим результат
                        if exit_code == 0:
                            # Ищем JSON в логах
                            lines = logs.split("\n")
                            json_lines = []
                            in_json = False

                            for line in lines:
                                if line.strip().startswith("{"):
                                    in_json = True
                                if in_json:
                                    json_lines.append(line)
                                if line.strip().endswith("}"):
                                    in_json = False
                                    break

                            if json_lines:
                                json_str = "\n".join(json_lines)
                                try:
                                    data = json.loads(json_str)
                                    return DockerRunner._parse_result(
                                        data, logs[:output_limit]
                                    )
                                except json.JSONDecodeError:
                                    pass

                        # Если не удалось распарсить JSON
                        return SandboxResult(
                            success=False,
                            passed=0,
                            failed=len(tests.get("tests", [])),
                            results=[],
                            raw_stdout=logs[:output_limit],
                            raw_stderr=None,
                        )

                    finally:
                        # Всегда удаляем контейнер
                        try:
                            container.remove(force=True)
                        except:
                            pass

            except TimeoutError as e:
                return SandboxResult(
                    success=False,
                    passed=0,
                    failed=len(tests.get("tests", [])),
                    results=[],
                    raw_stdout=str(e),
                    raw_stderr=None,
                )
            except Exception as e:
                return SandboxResult(
                    success=False,
                    passed=0,
                    failed=len(tests.get("tests", [])),
                    results=[],
                    raw_stdout=f"Docker error: {str(e)}",
                    raw_stderr=None,
                )

    @staticmethod
    def _parse_result(data: Dict, raw_stdout: str) -> SandboxResult:
        """Парсинг результата из JSON"""
        try:
            results = []
            for r in data.get("results", []):
                results.append(
                    SingleTestResult(
                        index=r.get("index", 0),
                        success=r.get("success", False),
                        input=r.get("input"),
                        expected=r.get("expected"),
                        result=r.get("result"),
                        error=r.get("error"),
                    )
                )

            return SandboxResult(
                success=data.get("success", False),
                passed=data.get("passed", 0),
                failed=data.get("failed", 0),
                results=results,
                raw_stdout=raw_stdout,
                raw_stderr=None,
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                passed=0,
                failed=0,
                results=[],
                raw_stdout=f"Parse error: {str(e)}\n{raw_stdout[:5000]}",
                raw_stderr=None,
            )
