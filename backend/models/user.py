from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


def sanitize_string(v: Optional[str]) -> Optional[str]:
    """Strip HTML tags from string input."""
    if v:
        return re.sub(r"<[^>]+>", "", v).strip()
    return v


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
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v):
        return sanitize_string(v)

    @field_validator("avatar_url")
    @classmethod
    def validate_url(cls, v):
        if v and not v.startswith(("https://", "http://")):
            raise ValueError("Invalid URL format")
        return v


class UserPreferences(BaseModel):
    energy_patterns: Optional[Dict[str, Any]] = None
    work_style: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class UserPreferencesUpdate(BaseModel):
    energy_patterns: Optional[Dict[str, Any]] = None
    work_style: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class OnboardingUpdate(BaseModel):
    step: int = Field(..., ge=0, le=10)
    data: Dict[str, Any]


class CheckInRequest(BaseModel):
    energy_level: int = Field(..., ge=1, le=10)
    mood: str = Field(..., min_length=1, max_length=50)
    sleep_quality: Optional[int] = Field(default=None, ge=1, le=10)
    blockers: Optional[List[str]] = Field(default=None, max_length=10)
    focus_areas: Optional[List[str]] = Field(default=None, max_length=10)

    @field_validator("mood")
    @classmethod
    def sanitize_mood(cls, v):
        return sanitize_string(v)

    @field_validator("blockers", "focus_areas")
    @classmethod
    def validate_list_items(cls, v):
        if v:
            return [sanitize_string(item)[:200] for item in v if item]
        return v


class CurrentState(BaseModel):
    id: str
    user_id: str
    status: str
    current_task_id: Optional[str] = None
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    started_at: Optional[datetime] = None


# ============================================
# FLOWER POINTS MODELS
# ============================================


class FlowerPointsUpdate(BaseModel):
    amount: int = Field(..., ge=1)
    type: str = Field(..., pattern="^(earned|spent)$")
    reason: str = Field(..., min_length=1, max_length=100)
    project_id: Optional[str] = None

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, v):
        return sanitize_string(v)


class FlowerTransaction(BaseModel):
    id: str
    amount: int
    type: str
    reason: str
    project_id: Optional[str] = None
    created_at: datetime


class FlowerPointsResponse(BaseModel):
    balance: int
    transactions: Optional[List[FlowerTransaction]] = None


# ============================================
# GRAVEYARD MODELS
# ============================================


class FlowerPlacement(BaseModel):
    id: str
    name: str
    emoji: str
    cost: int = Field(..., ge=0)
    days_added: int = Field(..., ge=0)
    placed_at: Optional[datetime] = None


class GraveyardMetaUpdate(BaseModel):
    flowers: List[FlowerPlacement] = Field(default_factory=list)
    epitaph: Optional[str] = Field(default=None, max_length=500)
    expiry_date: datetime

    @field_validator("epitaph")
    @classmethod
    def sanitize_epitaph(cls, v):
        return sanitize_string(v)


class GraveyardMetaResponse(BaseModel):
    project_id: str
    flowers: List[FlowerPlacement]
    epitaph: Optional[str] = None
    expiry_date: datetime
