from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NextDoFeedback(BaseModel):
    task_id: str
    feedback: str = Field(..., description="good, bad, or meh")
    reason: Optional[str] = None


class NextDoSkip(BaseModel):
    task_id: str
    reason: Optional[str] = None


class TaskRecommendation(BaseModel):
    task_id: str
    title: str
    project_name: Optional[str] = None
    priority: str
    score: float
    reasons: List[str]
    estimated_duration: Optional[int] = None
    deadline: Optional[datetime] = None


class NextDoResponse(BaseModel):
    success: bool = True
    data: dict
