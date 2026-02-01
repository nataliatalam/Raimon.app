from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
import re


def sanitize_string(v: Optional[str]) -> Optional[str]:
    """Strip HTML tags from string input."""
    if v:
        return re.sub(r"<[^>]+>", "", v).strip()
    return v


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    ON_BREAK = "on_break"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Request Schemas
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration: Optional[int] = Field(default=None, ge=1, le=1440, description="Duration in minutes (max 24h)")
    deadline: Optional[datetime] = None
    tags: Optional[List[str]] = Field(default=None, max_length=20)
    parent_task_id: Optional[str] = Field(default=None, max_length=36)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v):
        return sanitize_string(v)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v):
        return sanitize_string(v)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v:
            sanitized = []
            for tag in v:
                tag = sanitize_string(tag)
                if tag and len(tag) <= 50:
                    sanitized.append(tag[:50])
            return sanitized
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    estimated_duration: Optional[int] = Field(default=None, ge=1, le=1440)
    deadline: Optional[datetime] = None
    tags: Optional[List[str]] = Field(default=None, max_length=20)
    parent_task_id: Optional[str] = Field(default=None, max_length=36)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v):
        return sanitize_string(v)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v):
        return sanitize_string(v)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v:
            return [sanitize_string(tag)[:50] for tag in v if tag and len(tag) <= 50]
        return v


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskPriorityUpdate(BaseModel):
    priority: TaskPriority


# Task Action Schemas
class TaskStartRequest(BaseModel):
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v):
        return sanitize_string(v)


class TaskPauseRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("reason", "notes")
    @classmethod
    def sanitize_text(cls, v):
        return sanitize_string(v)


class TaskCompleteRequest(BaseModel):
    energy_after: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = Field(default=None, max_length=2000)
    actual_duration: Optional[int] = Field(default=None, ge=1, le=1440, description="Actual duration in minutes")

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v):
        return sanitize_string(v)


class TaskBreakRequest(BaseModel):
    break_type: str = Field(default="short", max_length=20, description="short, long, or custom")
    duration: Optional[int] = Field(default=None, ge=1, le=120, description="Break duration in minutes")
    reason: Optional[str] = Field(default=None, max_length=500)

    @field_validator("break_type")
    @classmethod
    def validate_break_type(cls, v):
        allowed = {"short", "long", "custom"}
        if v not in allowed:
            raise ValueError(f"break_type must be one of: {allowed}")
        return v

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, v):
        return sanitize_string(v)


class TaskInterventionRequest(BaseModel):
    intervention_type: str = Field(..., max_length=20, description="stuck, interrupted, blocked, overwhelmed")
    description: Optional[str] = Field(default=None, max_length=2000)
    blockers: Optional[List[str]] = Field(default=None, max_length=10)

    @field_validator("intervention_type")
    @classmethod
    def validate_intervention_type(cls, v):
        allowed = {"stuck", "interrupted", "blocked", "overwhelmed"}
        if v not in allowed:
            raise ValueError(f"intervention_type must be one of: {allowed}")
        return v

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v):
        return sanitize_string(v)

    @field_validator("blockers")
    @classmethod
    def validate_blockers(cls, v):
        if v:
            return [sanitize_string(b)[:200] for b in v if b]
        return v


# Response Schemas
class TaskResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    parent_task_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    deadline: Optional[datetime] = None
    tags: Optional[List[str]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkSessionResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    energy_before: Optional[int] = None
    energy_after: Optional[int] = None
    interruptions: int = 0
    notes: Optional[str] = None


class TaskWithSession(BaseModel):
    task: TaskResponse
    session: Optional[WorkSessionResponse] = None
