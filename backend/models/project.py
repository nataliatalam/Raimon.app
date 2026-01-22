from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class StakeholderSchema(BaseModel):
    name: str
    role: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class ResourceSchema(BaseModel):
    type: str  # document, link, file
    title: str
    url: str
    added_at: Optional[datetime] = None


# Request Schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=10)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    details: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[int] = Field(default=None, ge=0, le=10)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None


# Project Details Update Schemas
class ProjectProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class ProjectGoalsUpdate(BaseModel):
    goals: List[str]


class ProjectResourcesUpdate(BaseModel):
    resources: List[ResourceSchema]


class ProjectTimelineUpdate(BaseModel):
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    milestones: Optional[List[Dict[str, Any]]] = None


class ProjectStakeholdersUpdate(BaseModel):
    stakeholders: List[StakeholderSchema]


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
