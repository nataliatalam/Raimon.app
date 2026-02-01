"""
Data contracts (Pydantic models) for agent MVP.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class TaskCandidate(BaseModel):
    """A candidate task for selection."""
    id: str = Field(..., description="Task UUID")
    title: str = Field(..., min_length=1, max_length=500)
    priority: str = "medium" #Default
    status: str = Field(default="todo", description="todo, in_progress, paused, blocked, completed")
    estimated_duration: Optional[int] = Field(default=None, ge=1, le=1440, description="minutes")
    due_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class SelectionConstraints(BaseModel):
    """Constraints for task selection."""
    max_minutes: int = Field(default=120, ge=5, le=1440)
    mode: str = Field(default="balanced", description="focus, quick, learning, balanced")
    current_energy: int = Field(default=5, ge=1, le=10, description="1-10 energy level")
    avoid_tags: Optional[List[str]] = None
    prefer_priority: Optional[str] = None  # prioritize urgent/high if available


class DoSelectorInput(BaseModel):
    """Input to DoSelector agent."""
    user_id: str
    candidates: List[TaskCandidate] = Field(min_items=1, max_items=50)
    constraints: SelectionConstraints
    recent_actions: Optional[Dict[str, Any]] = None


class DoSelectorOutput(BaseModel):
    """Output from DoSelector agent (strict JSON contract)."""
    task_id: str = Field(..., description="Must match one of candidate IDs")
    reason_codes: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="e.g., [deadline_urgent, energy_fit, priority_high]"
    )
    alt_task_ids: List[str] = Field(
        default_factory=list,
        max_length=2,
        description="1-2 alternative task IDs"
    )

    @field_validator("task_id")
    @classmethod
    def task_id_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("task_id cannot be empty")
        return v


class CoachInput(BaseModel):
    """Input to Coach agent."""
    task: TaskCandidate
    reason_codes: List[str]
    mode: str = Field(default="balanced")
    user_name: Optional[str] = None


class CoachOutput(BaseModel):
    """Output from Coach agent."""
    title: str = Field(..., min_length=1, max_length=100, description="Short encouragement title")
    message: str = Field(..., min_length=5, max_length=300, description="1-2 sentences max")
    next_step: str = Field(..., min_length=1, max_length=100, description="Micro-step under 10 words")

    @field_validator("message")
    @classmethod
    def message_length_check(cls, v):
        sentences = v.split(".")
        if len([s for s in sentences if s.strip()]) > 2:
            raise ValueError("Message must be 1-2 sentences max")
        return v

    @field_validator("next_step")
    @classmethod
    def next_step_word_count(cls, v):
        words = v.split()
        if len(words) > 10:
            raise ValueError("next_step must be under 10 words")
        return v


class ActiveDo(BaseModel):
    """Result of task selection."""
    task: TaskCandidate
    reason_codes: List[str]
    alt_task_ids: List[str]
    selected_at: datetime = Field(default_factory=datetime.utcnow)


class GraphState(BaseModel):
    """LangGraph state machine state."""
    user_id: str
    candidates: List[TaskCandidate] = Field(default_factory=list)
    constraints: Optional[SelectionConstraints] = None
    active_do: Optional[ActiveDo] = None
    coach_message: Optional[CoachOutput] = None
    error: Optional[str] = None
    opik_trace_id: Optional[str] = None


class AgentMVPResponse(BaseModel):
    """Final API response."""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
