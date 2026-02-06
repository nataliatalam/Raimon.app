"""
Abstract base class for LLM clients.
Defines the interface that all LLM provider implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseLLMClient(ABC):
    """
    Abstract base class for all LLM clients.

    Provides a common interface for different LLM providers (Gemini, OpenAI, Claude, etc.)
    This allows easy swapping of providers without changing agent code.
    """

    @abstractmethod
    def generate_json_response(
        self,
        prompt: str,
        expected_format: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """
        Generate a JSON-formatted response from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            expected_format: Optional description of expected JSON format
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens

        Returns:
            Parsed JSON response as dictionary

        Raises:
            ValueError: If response is not valid JSON
        """
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate a plain text response from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens

        Returns:
            Plain text response

        Raises:
            Exception: If LLM call fails
        """
        pass
