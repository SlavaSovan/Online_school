from pydantic import BaseModel
from typing import Dict, List, Literal, Optional, Union


class TestSubmissionPayload(BaseModel):
    type: Literal["test"]
    answers: Dict[str, List[str]]


class SandboxSubmissionPayload(BaseModel):
    type: Literal["sandbox"]
    code: str


class FileSubmissionPayload(BaseModel):
    type: Literal["file"]
    s3_file_key: str
    file_size: Optional[int] = None


SubmissionPayload = Union[
    TestSubmissionPayload,
    SandboxSubmissionPayload,
    FileSubmissionPayload,
]
