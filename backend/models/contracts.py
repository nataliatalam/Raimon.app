"""
Data contracts (Pydantic models) for agent MVP.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone


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
    candidates: List[TaskCandidate] = Field(min_length=1, max_length=50)
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
    selected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GraphState(BaseModel):
    """LangGraph state machine state."""
    model_config = {"arbitrary_types_allowed": True}

    user_id: str
    current_event: Optional[Any] = None
    candidates: List[TaskCandidate] = Field(default_factory=list)
    constraints: Optional[SelectionConstraints] = None
    active_do: Optional[Any] = None  # Can be dict or ActiveDo
    coach_message: Optional[CoachOutput] = None
    error: Optional[str] = None
    opik_trace_id: Optional[str] = None
    success: bool = Field(default=True)

    # Additional fields for orchestrator handlers
    context_resumption: Optional[Any] = None
    selection_constraints: Optional[Any] = None
    user_profile: Optional[Any] = None
    motivation_message: Optional[Any] = None
    stuck_analysis: Optional[Any] = None
    microtasks: Optional[List[Any]] = None
    day_insights: Optional[List[Any]] = None


class AgentMVPResponse(BaseModel):
    """Final API response."""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


# New models for full agent flow

class UserProfileAnalyzeRequest(BaseModel):
    """Request to analyze user profile."""
    include_tasks: bool = True
    include_sessions: bool = True
    include_patterns: bool = True


class UserProfileAnalysis(BaseModel):
    """Analysis of user profile."""
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    work_patterns: Dict[str, Any] = Field(default_factory=dict)
    task_preferences: Dict[str, Any] = Field(default_factory=dict)
    energy_patterns: Dict[str, Any] = Field(default_factory=dict)


class UserProfile(BaseModel):
    """User profile with learned patterns and preferences."""
    user_id: str
    energy_patterns: Dict[str, Any] = Field(default_factory=dict)
    focus_preferences: List[str] = Field(default_factory=list)
    time_preferences: Dict[str, Any] = Field(default_factory=dict)
    productivity_patterns: Dict[str, Any] = Field(default_factory=dict)
    task_completion_history: List[Dict[str, Any]] = Field(default_factory=list)


class WorkSession(BaseModel):
    """Work session data."""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    duration_minutes: Optional[int] = None
    focus_quality: Optional[int] = Field(None, ge=1, le=10, description="1-10 quality rating")
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class XpTransaction(BaseModel):
    """XP transaction record (alias for XpLedgerEntry compatibility)."""
    event_id: str
    xp_change: int
    reason: str
    user_id: Optional[str] = None
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProjectProfileRequest(BaseModel):
    """Request to create project profile."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    deadline: Optional[datetime] = None
    importance: Optional[int] = Field(None, ge=1, le=10)
    why: Optional[str] = Field(None, max_length=500)
    constraints: Optional[List[str]] = None


class ProjectSuggestion(BaseModel):
    """Suggestion for project improvement."""
    category: str = Field(..., max_length=50)
    suggestion: str = Field(..., min_length=1, max_length=100)
    impact: str = Field(default="medium", description="high, medium, or low")


class ProjectProfile(BaseModel):
    """Normalized project profile."""
    project_id: str
    normalized_fields: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    suggested_milestones: Optional[List[Dict[str, Any]]] = None


class PriorityAnalyzeRequest(BaseModel):
    """Request to analyze priorities."""
    project_id: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class TaskCandidateScored(BaseModel):
    """Scored task candidate."""
    task: TaskCandidate
    score: float = Field(ge=0.0, le=100.0)
    reason_codes: List[str] = Field(default_factory=list)


# Alias for backward compatibility
TaskCandidateWithScore = TaskCandidateScored


class DoSelectionRequest(BaseModel):
    """Request for task selection."""
    scored_candidates: List[TaskCandidateScored] = Field(..., min_length=1)
    constraints: "SelectionConstraints"


class DoSelection(BaseModel):
    """Result of task selection."""
    selected_task: TaskCandidateScored
    selection_reason: str = Field(..., description="Why this task was selected")


class PriorityCandidates(BaseModel):
    """Priority analysis result."""
    candidates: List[Union[TaskCandidate, TaskCandidateScored]]


# Alias for backward compatibility
PriorityScoredCandidates = PriorityCandidates


class DailyCheckinRequest(BaseModel):
    """Daily check-in request."""
    date: str  # YYYY-MM-DD
    energy_level: int = Field(ge=1, le=10)
    mood: Optional[str] = Field(None, max_length=50)
    sleep_quality: Optional[int] = Field(None, ge=1, le=10)
    focus_minutes: Optional[int] = Field(None, ge=0, le=1440)
    context: Optional[str] = Field(None, max_length=500)
    priorities: List[str] = Field(default_factory=list)
    day_of_week: int = Field(default_factory=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc).weekday())


# Alias for backward compatibility
DailyCheckIn = DailyCheckinRequest


class TimeLearningRequest(BaseModel):
    """Request for time learning."""
    lookback_days: int = Field(default=30, ge=1, le=365)


class TimeModel(BaseModel):
    """Learned time model."""
    peak_hours: List[int] = Field(default_factory=list)  # 0-23
    peak_days: List[int] = Field(default_factory=list)  # 0-6 (Monday=0)
    success_curve: Optional[Dict[str, Any]] = None

class TimePatterns(BaseModel):
    """Learned time patterns."""
    peak_hours: List[int] = Field(default_factory=list)
    optimal_durations: Dict[str, int] = Field(default_factory=dict)
    day_patterns: Dict[str, Any] = Field(default_factory=dict)
    time_efficiency: float = Field(default=0.0, ge=0.0, le=1.0)


class AppOpenRequest(BaseModel):
    """App open request."""
    now: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device: Optional[str] = Field(None, max_length=100)
    first_open_today: bool = False


class AppOpenDecision(BaseModel):
    """Decision on app open."""
    next_ui_state: str  # e.g., "checkin", "next_do", "dashboard"
    active_do: Optional["ActiveDo"] = None
    needs_checkin: bool = False


class ContextResumption(BaseModel):
    """Context resumption data."""
    previous_session: Optional[Dict[str, Any]] = None
    suggested_continuation: Optional[str] = None
    context_hints: List[str] = Field(default_factory=list)


class Microtask(BaseModel):
    """A microtask for helping users unstick."""
    description: str = Field(..., min_length=1, max_length=100)
    estimated_minutes: int = Field(default=2, ge=1, le=10)
    category: str = Field(default="unstuck_help", max_length=50)


class Insight(BaseModel):
    """A single insight about user behavior or progress."""
    content: Optional[str] = Field(default=None, min_length=1, max_length=200)
    category: Optional[str] = Field(default=None, max_length=50)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1, max_length=300)
    evidence_keys: List[str] = Field(default_factory=list)


class InsightCard(BaseModel):
    """Insight card."""
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=300)
    evidence_keys: List[str] = Field(default_factory=list)


class InsightPack(BaseModel):
    """Pack of insights."""
    insights: List[InsightCard] = Field(max_length=3)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectInsightRequest(BaseModel):
    """Request for project insights."""
    project_id: str
    insight_type: str = Field(default="progress", max_length=50)
    time_range: str = Field(default="week", max_length=50)


class ProjectInsights(BaseModel):
    """Project insights response."""
    insights: List[Insight] = Field(default_factory=list, max_length=5)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StuckDetectRequest(BaseModel):
    """Request to detect stuck patterns."""
    task_id: Optional[str] = None
    reason: Optional[str] = Field(None, max_length=200)
    recent_actions: List[Dict[str, Any]] = Field(default_factory=list)


class StuckIntervention(BaseModel):
    """Stuck intervention decision."""
    type: str  # "break", "microtask", "alt_task", "coach"
    microtasks: Optional[List[str]] = None
    alt_task_id: Optional[str] = None
    schedule_for: Optional[datetime] = None


class InsightRequest(BaseModel):
    """Request for insights."""
    project_id: Optional[str] = None
    window_days: int = Field(default=7, ge=1, le=90)


class MotivationRequest(BaseModel):
    """Request for motivation."""
    trigger: str  # "completion", "streak", "level_up"
    gamification_state: "GamificationState"
    coaching_style: Optional[str] = None


class MotivationMessage(BaseModel):
    """Motivational message."""
    title: str = Field(..., min_length=1, max_length=50)
    body: str = Field(..., min_length=1, max_length=240)
    cta: Optional[str] = Field(None, max_length=50)


class MotivationResponse(BaseModel):
    """Motivation response."""
    message: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="general", max_length=50)


class DoSelectInput(BaseModel):
    """Input for Do Selector."""
    candidates: List[TaskCandidate]
    constraints: SelectionConstraints
    time_model: Optional[TimeModel] = None
    continuity_state: Optional[Dict[str, Any]] = None


class OrchestratorEvent(BaseModel):
    """Event for orchestrator."""
    type: str  # "APP_OPEN", "CHECKIN_SUBMITTED", "DO_NEXT", "DO_ACTION"
    payload: Dict[str, Any] = Field(default_factory=dict)


class OrchestratorEvent(BaseModel):
    """Event for orchestrator."""
    type: str  # "APP_OPEN", "CHECKIN_SUBMITTED", "DO_NEXT", "DO_ACTION"
    payload: Dict[str, Any] = Field(default_factory=dict)


class AppOpenEvent(BaseModel):
    """App open event."""
    user_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    device: Optional[str] = None
    current_time: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckInSubmittedEvent(BaseModel):
    """Check-in submitted event."""
    user_id: str
    energy_level: int = Field(ge=1, le=10)
    mood: Optional[str] = None
    focus_areas: List[str] = Field(default_factory=list)
    time_available: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CheckInConstraints(BaseModel):
    """Check-in converted to constraints."""
    energy_level: int = Field(ge=1, le=10)
    focus_areas: List[str] = Field(default_factory=list)
    time_available: int = Field(default=120, ge=5, le=1440)
    current_context: Optional[str] = None


class CheckInToConstraintsRequest(BaseModel):
    """Request to convert check-in to constraints."""
    user_id: str
    energy_level: int = Field(ge=1, le=10)
    focus_areas: List[str] = Field(default_factory=list)
    time_available: Optional[int] = None
    check_in_data: Optional['DailyCheckIn'] = None
    user_profile: Optional['UserProfileAnalysis'] = None


class DoNextEvent(BaseModel):
    """Do next event."""
    user_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    context: str = Field(default="task_selection", description="Context for task selection")


class DoActionEvent(BaseModel):
    """Do action event (start, complete, stuck)."""
    user_id: str
    action: str  # "start", "complete", "stuck", "pause"
    task_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    current_session: Optional[Dict[str, Any]] = None  # For stuck detection
    time_stuck: Optional[int] = None  # Minutes stuck on task


class DayEndEvent(BaseModel):
    """Day end event."""
    user_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentEvent(BaseModel):
    """Agent event for logging."""
    event_type: str
    user_id: Optional[str] = None
    event_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OrchestratorResult(BaseModel):
    """Result from orchestrator."""
    active_do: Optional["ActiveDo"] = None
    messages: Optional[List[Dict[str, Any]]] = None
    next_ui_state: Optional[str] = None
    insights: Optional[InsightPack] = None
    gamification: Optional["GamificationState"] = None


class GamificationEvent(BaseModel):
    """Gamification event."""
    type: str  # "task_done", "streak_maintain", "level_up"
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    task_id: Optional[str] = None


class GamificationState(BaseModel):
    """Current gamification state."""
    user_id: Optional[str] = None
    total_xp: int = Field(default=0, ge=0)
    level: int = Field(default=1, ge=1)
    current_streak: int = Field(default=0, ge=0)
    longest_streak: int = Field(default=0, ge=0)
    last_activity_date: Optional[str] = None
    streak: int = Field(default=0, ge=0)
    xp: int = Field(default=0, ge=0)
    freezes: int = Field(default=0, ge=0)


class GamificationUpdate(BaseModel):
    """Result of a gamification update."""
    xp_gained: int = Field(default=0, ge=0)
    new_total_xp: int = Field(default=0, ge=0)
    new_level: int = Field(default=1, ge=1)
    streak_extended: bool = Field(default=False)
    current_streak: int = Field(default=0, ge=0)


class XpLedgerEntry(BaseModel):
    """XP ledger entry."""
    event_id: str
    xp_change: int
    reason: str


class CoachRequest(BaseModel):
    """Request for coach."""
    task: TaskCandidate
    constraints: SelectionConstraints
    reason_codes: List[str]
    tone: Optional[str] = "encouraging"


class CoachMessage(BaseModel):
    """Coach message."""
    title: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=300)
    next_step: str = Field(..., min_length=1, max_length=100)


class CoachingMessage(BaseModel):
    """Coaching message output."""
    message: str = Field(..., min_length=1, max_length=300)
    category: str = Field(default="general", max_length=50)


class SelectionResult(BaseModel):
    """Result from task selection."""
    task: Optional[TaskCandidate] = None
    selection_reason: str = Field(..., description="Why this task was selected")
    coaching_message: str = Field(..., description="Coach guidance for the task")


class StuckDetectionRequest(BaseModel):
    """Request for stuck pattern detection."""
    user_id: str = Field(..., description="User ID")
    current_session: "WorkSession" = Field(..., description="Current work session")
    time_stuck: int = Field(..., ge=0, description="Time stuck in minutes")


class StuckAnalysis(BaseModel):
    """Analysis result from stuck pattern detection."""
    is_stuck: bool = Field(default=False, description="Whether user is stuck")
    stuck_reason: Optional[str] = Field(default=None, description="Reason user is stuck if detected")
    microtasks: List["Microtask"] = Field(default_factory=list, description="Microtasks to help unstuck")
