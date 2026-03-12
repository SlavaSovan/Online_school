from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReviewResponseSchema(BaseModel):
    id: int
    submission_id: int
    mentor_id: int

    score: int
    comment: Optional[str]

    reviewed_at: datetime

    class Config:
        from_attributes = True


class ReviewCreateSchema(BaseModel):
    score: int = Field(..., ge=0)
    comment: Optional[str] = None


class ReviewUpdateSchema(BaseModel):
    score: Optional[int] = Field(None, ge=0)
    comment: Optional[str] = None


class ReviewCreateByAdminSchema(BaseModel):
    submission_id: int
    mentor_id: int
    score: int = Field(..., ge=0)
    comment: Optional[str] = None
