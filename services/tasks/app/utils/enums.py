from enum import Enum


class TaskType(str, Enum):
    TEST = "test"
    FILE_UPLOAD = "file_upload"
    SANDBOX = "sandbox"


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"


class SubmissionStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class CodeLanguage(str, Enum):
    PYTHON = "python"
