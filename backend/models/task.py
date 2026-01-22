from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


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
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration: Optional[int] = Field(default=None, ge=1, description="Duration in minutes")
    deadline: Optional[datetime] = None
    tags: Optional[List[str]] = None
    parent_task_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    estimated_duration: Optional[int] = Field(default=None, ge=1)
    deadline: Optional[datetime] = None
    tags: Optional[List[str]] = None
    parent_task_id: Optional[str] = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskPriorityUpdate(BaseModel):
    priority: TaskPriority


# Task Action Schemas
class TaskStartRequest(BaseModel):
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = None


class TaskPauseRequest(BaseModel):
    reason: Optional[str] = None
    notes: Optional[str] = None


class TaskCompleteRequest(BaseModel):
    energy_after: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = None
    actual_duration: Optional[int] = Field(default=None, ge=1, description="Actual duration in minutes")


class TaskBreakRequest(BaseModel):
    break_type: str = Field(default="short", description="short, long, or custom")
    duration: Optional[int] = Field(default=None, ge=1, description="Break duration in minutes")
    reason: Optional[str] = None


class TaskInterventionRequest(BaseModel):
    intervention_type: str = Field(..., description="stuck, interrupted, blocked, overwhelmed")
    description: Optional[str] = None
    blockers: Optional[List[str]] = None


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
