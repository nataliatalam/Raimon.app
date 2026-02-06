"""
Base class for LLM-powered agents.

All LLM agents inherit from this class and follow the pattern:
1. Primary: LLM call
2. Fallback 1: Validation
3. Fallback 2: Deterministic fallback
4. Fallback 3: Safe defaults
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


class BaseLLMAgent(ABC):
    """
    Abstract base class for LLM-powered agents.

    Enforces pattern:
    - Pydantic I/O contracts
    - @track decorator for Opik
    - Error handling with fallbacks
    """

    def __init__(self, llm_service=None, opik_tracker=None):
        """
        Initialize LLM agent.

        Args:
            llm_service: LLM service (Gemini, Claude, etc.)
            opik_tracker: Optional Opik tracker instance
        """
        self.llm_service = llm_service
        self.opik_tracker = opik_tracker

    @track(name="agent_process")
    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Process input through LLM agent.

        Must be overridden by subclasses.

        Args:
            input: Pydantic input model

        Returns:
            Pydantic output model
        """
        raise NotImplementedError("Subclasses must implement process()")

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate LLM output structure.

        Override in subclass for custom validation.

        Args:
            output: LLM output dict

        Returns:
            True if output is valid, False otherwise
        """
        return True

    def get_fallback_output(self, input: AgentInput) -> AgentOutput:
        """
        Get fallback output when LLM fails.

        Override in subclass for custom fallback.

        Args:
            input: Agent input

        Returns:
            Safe default output
        """
        return AgentOutput(
            success=False,
            error="Agent processing failed, using fallback",
        )
