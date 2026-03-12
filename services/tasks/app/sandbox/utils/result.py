from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class SingleTestResult:
    index: int
    success: bool
    input: Optional[list] = None
    expected: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class SandboxResult:
    success: bool
    passed: int
    failed: int
    results: List[SingleTestResult]
    raw_stdout: str
    raw_stderr: Optional[str] = None
