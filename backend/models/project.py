from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import re


def sanitize_string(v: Optional[str]) -> Optional[str]:
    """Strip HTML tags from string input."""
    if v:
        return re.sub(r"<[^>]+>", "", v).strip()
    return v


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class StakeholderSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    role: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("name", "role")
    @classmethod
    def sanitize_text(cls, v):
        return sanitize_string(v)


class ResourceSchema(BaseModel):
    id: Optional[str] = None
    type: str = Field(..., max_length=50)  # document, link, file
    title: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., max_length=2048)
    added_at: Optional[datetime] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"document", "link", "file", "image", "video"}
        if v not in allowed:
            raise ValueError(f"type must be one of: {allowed}")
        return v

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v):
        return sanitize_string(v)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(("https://", "http://")):
            raise ValueError("URL must start with http:// or https://")
        return v


# Request Schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: int = Field(default=0, ge=0, le=10)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(default=None, max_length=50)
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    details: Optional[Dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v):
        return sanitize_string(v)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v):
        return sanitize_string(v)

    @field_validator("icon")
    @classmethod
    def sanitize_icon(cls, v):
        return sanitize_string(v)


class TaskUpdateSchema(BaseModel):
    id: Optional[str] = None  # None for new tasks
    title: str = Field(..., min_length=1, max_length=500)
    completed: bool = False
    due_date: Optional[str] = None
    priority: Optional[str] = None
    subtasks: Optional[List[Dict[str, Any]]] = None
    depends_on: Optional[str] = None
    blocker: Optional[str] = None
    recurring: Optional[str] = None
    note: Optional[str] = None

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, v):
        return sanitize_string(v)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[ProjectStatus] = None
    priority: Optional[int] = Field(default=None, ge=0, le=10)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(default=None, max_length=50)
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=50000)
    tasks: Optional[List[TaskUpdateSchema]] = None
    links: Optional[List[ResourceSchema]] = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v):
        return sanitize_string(v)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v):
        return sanitize_string(v)

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v):
        return sanitize_string(v)


# Project Details Update Schemas
class ProjectProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v):
        return sanitize_string(v)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v):
        return sanitize_string(v)


class ProjectGoalsUpdate(BaseModel):
    goals: List[str] = Field(..., max_length=20)

    @field_validator("goals")
    @classmethod
    def validate_goals(cls, v):
        return [sanitize_string(g)[:500] for g in v if g]


class ProjectResourcesUpdate(BaseModel):
    resources: List[ResourceSchema] = Field(..., max_length=50)


class ProjectTimelineUpdate(BaseModel):
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    milestones: Optional[List[Dict[str, Any]]] = Field(default=None, max_length=50)


class ProjectStakeholdersUpdate(BaseModel):
    stakeholders: List[StakeholderSchema] = Field(..., max_length=30)


# Response Schemas
class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    status: str = "active"
    priority: int = 0
    color: Optional[str] = None
    icon: Optional[str] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    archived_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectWithStats(ProjectResponse):
    task_count: int = 0
    completed_tasks: int = 0
    progress: float = 0.0


class ProjectListResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]


class ProjectDetailResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
