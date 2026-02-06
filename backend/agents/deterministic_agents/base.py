"""
Base class for deterministic agents.

Deterministic agents contain pure logic with no LLM calls.
They are guaranteed to return the same output for the same input.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from pydantic import BaseModel
from opik import track
import logging

logger = logging.getLogger(__name__)


class AgentInput(BaseModel):
    """Base input for all agents."""
    user_id: str
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentOutput(BaseModel):
    """Base output for all agents."""
    success: bool = True
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class BaseDeterministicAgent(ABC):
    """
    Abstract base class for deterministic agents.

    Enforces pattern:
    - Pydantic I/O contracts
    - @track decorator for Opik
    - Pure logic (no LLM calls)
    - Deterministic output (same input = same output)
    """

    def __init__(self):
        """Initialize deterministic agent."""
        pass

    @track(name="agent_process")
    @abstractmethod
    def process(self, input: AgentInput) -> AgentOutput:
        """
        Process input with deterministic logic.

        Must be overridden by subclasses.

        Args:
            input: Pydantic input model

        Returns:
            Pydantic output model
        """
        raise NotImplementedError("Subclasses must implement process()")

    def validate_input(self, input: AgentInput) -> bool:
        """
        Validate input before processing.

        Override in subclass for custom validation.

        Args:
            input: Agent input

        Returns:
            True if input is valid, False otherwise
        """
        return True

    def get_error_output(self, error: str) -> AgentOutput:
        """
        Get error output.

        Override in subclass for custom error handling.

        Args:
            error: Error message

        Returns:
            Error output
        """
        return AgentOutput(
            success=False,
            error=error,
        )
