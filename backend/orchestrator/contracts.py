"""
Orchestrator GraphState and contracts.

Defines the state machine state for LangGraph orchestration.
Enhanced with mood, energy_level, and intervention_logs.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class GraphState(BaseModel):
    """
    LangGraph state machine state.

    This is the complete state that flows through the orchestrator workflow.
    Enhanced with user emotional state and intervention tracking.
    """

    model_config = {"arbitrary_types_allowed": True}

    # Core orchestration fields
    user_id: str = Field(..., description="User ID")
    current_event: Optional[Any] = Field(
        default=None,
        description="Current event being processed"
    )

    # User emotional state (NEW - Enhanced)
    mood: Optional[str] = Field(
        default=None,
        description='User mood (e.g., "motivated", "tired", "frustrated")'
    )
    energy_level: int = Field(
        default=5,
        ge=1,
        le=10,
        description="User energy level 1-10"
    )

    # Task selection fields
    candidates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Task candidate pool"
    )
    constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Selection constraints"
    )
    active_do: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Currently selected task"
    )

    # Agent outputs
    coach_message: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Coaching message from coach agent"
    )
    motivation_message: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Motivation message from motivation agent"
    )
    stuck_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Stuck pattern analysis"
    )
    microtasks: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Generated microtasks to help unstick"
    )
    day_insights: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Day completion insights"
    )

    # Context flow fields
    context_resumption: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Context resumption data"
    )
    selection_constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Derived selection constraints"
    )
    user_profile: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Analyzed user profile"
    )

    # Intervention tracking (NEW - Enhanced)
    intervention_logs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Log of user interventions (stuck, breaks, etc.)"
    )

    # Opik tracing
    opik_trace_id: Optional[str] = Field(
        default=None,
        description="Opik trace ID for observability"
    )

    # Execution status
    success: bool = Field(
        default=True,
        description="Whether orchestration succeeded"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )
