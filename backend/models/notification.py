from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    TASK_REMINDER = "task_reminder"
    DEADLINE_WARNING = "deadline_warning"
    STREAK_MILESTONE = "streak_milestone"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    BREAK_REMINDER = "break_reminder"
    DAILY_SUMMARY = "daily_summary"
    INSIGHT = "insight"
    SYSTEM = "system"


class ReminderFrequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class ReminderCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: Optional[str] = None
    remind_at: datetime
    frequency: ReminderFrequency = ReminderFrequency.ONCE
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    message: Optional[str] = None
    remind_at: Optional[datetime] = None
    frequency: Optional[ReminderFrequency] = None
    is_active: Optional[bool] = None
