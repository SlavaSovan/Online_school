from enum import Enum


class TaskType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    SHORT_ANSWER = "short_answer"
    FILE_UPLOAD = "file_upload"
    CODE = "code"


class SubmissionStatus(str, Enum):
    PENDING = "pending"
    AUTO_CHECKED = "auto_checked"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class CodeLanguage(str, Enum):
    PYTHON = "python"
