"""
LLM Service module - Unified interface for LLM operations.

This module provides:
- BaseLLMClient: Abstract interface for all LLM providers
- GeminiClient: Google Gemini API implementation
- LLMService: Facade wrapper for easy use in agents
- get_gemini_client(): Singleton access to Gemini client
"""

from .base_llm_client import BaseLLMClient
from .gemini_client import GeminiClient, get_gemini_client
from .llm_service import LLMService

__all__ = [
    "BaseLLMClient",
    "GeminiClient",
    "LLMService",
    "get_gemini_client",
]
