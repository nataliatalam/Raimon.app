from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserProfile(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    onboarding_completed: bool = False
    onboarding_step: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPreferences(BaseModel):
    energy_patterns: Optional[Dict[str, Any]] = None
    work_style: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class UserPreferencesUpdate(BaseModel):
    energy_patterns: Optional[Dict[str, Any]] = None
    work_style: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class OnboardingUpdate(BaseModel):
    step: int
    data: Dict[str, Any]


class CheckInRequest(BaseModel):
    energy_level: int
    mood: str
    sleep_quality: Optional[int] = None
    blockers: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None


class CurrentState(BaseModel):
    id: str
    user_id: str
    status: str
    current_task_id: Optional[str] = None
    energy_level: Optional[int] = None
    started_at: Optional[datetime] = None
