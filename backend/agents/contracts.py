"""
Agent I/O Pydantic contracts.

Defines the input/output interfaces for all agents (LLM and deterministic).
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class AgentInput(BaseModel):
    """
    Base input model for all agents.

    All agents receive input conforming to this structure.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    user_id: str = Field(..., description="User ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO format timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the agent"
    )


class AgentOutput(BaseModel):
    """
    Base output model for all agents.

    All agents return output conforming to this structure.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    success: bool = Field(default=True, description="Whether agent execution succeeded")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent output data"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="Execution time in milliseconds"
    )
