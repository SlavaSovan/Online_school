from pydantic import BaseModel
from typing import Dict, List, Literal


class TestSubmissionPayload(BaseModel):
    type: Literal["test"] = "test"
    answers: Dict[str, List[str]]


class SandboxSubmissionPayload(BaseModel):
    type: Literal["sandbox"] = "sandbox"
    code: str


class FileSubmissionPayload(BaseModel):
    type: Literal["file"] = "file"
    s3_file_key: str
    original_filename: str
    file_size: int
