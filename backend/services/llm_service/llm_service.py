"""
LLM Service - Facade wrapper for LLM operations.

Provides a unified interface for all LLM interactions across the application.
Allows easy swapping of LLM providers without changing agent code.
"""

from typing import Optional, Dict, Any
from .base_llm_client import BaseLLMClient
from .gemini_client import GeminiClient
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service wrapper for LLM operations with provider abstraction.

    This service encapsulates all LLM interactions and provides a clean interface
    for agents and other components. It supports dependency injection of different
    LLM providers (Gemini, OpenAI, Claude, etc.) through the BaseLLMClient interface.

    Example:
        ```python
        # Default (uses Gemini)
        service = LLMService()

        # Custom provider
        custom_client = SomeOtherLLMClient()
        service = LLMService(client=custom_client)

        # Use in agent
        response = service.generate_json(prompt)
        ```
    """

    def __init__(self, client: Optional[BaseLLMClient] = None):
        """
        Initialize LLM Service.

        Args:
            client: LLM client implementation (defaults to GeminiClient)
        """
        self.client = client or GeminiClient()
        logger.info(f"✅ LLMService initialized with {self.client.__class__.__name__}")

    def generate_json(
        self,
        prompt: str,
        expected_format: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """
        Generate a JSON-formatted response.

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
        return self.client.generate_json_response(
            prompt=prompt,
            expected_format=expected_format,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate a plain text response.

        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens

        Returns:
            Plain text response

        Raises:
            Exception: If LLM call fails
        """
        return self.client.generate_text(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def get_client(self) -> BaseLLMClient:
        """
        Get the underlying LLM client.

        Useful for advanced use cases where you need direct access to the client.

        Returns:
            The underlying BaseLLMClient implementation
        """
        return self.client

    def set_client(self, client: BaseLLMClient) -> None:
        """
        Set a new LLM client provider.

        Allows runtime swapping of LLM providers.

        Args:
            client: New client implementing BaseLLMClient
        """
        self.client = client
        logger.info(f"✅ LLMService client changed to {client.__class__.__name__}")
