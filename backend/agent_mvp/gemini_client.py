"""
Gemini client wrapper with Opik tracing.
Provides a simple interface to call Gemini models with automatic observability.
"""

import json
import os
from typing import Optional, Dict, Any
from google import genai
from opik import track
import logging

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Wrapper around Google Gemini API with Opik tracing.
    Uses environment variable GOOGLE_API_KEY.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash-lite"):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model: Model name (default: gemini-2.5-flash-lite)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set")

        self.model = model
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"✅ GeminiClient initialized with model: {self.model}")

    @track(name="gemini_call")
    def generate_json_response(
        self,
        prompt: str,
        expected_format: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """
        Call Gemini and expect JSON-only response.
        Automatically traced by Opik.

        Args:
            prompt: Full prompt to send
            expected_format: Optional description of expected JSON format (for prompt)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Max output tokens

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If response is not valid JSON
        """
        try:
            # Ensure prompt includes JSON instruction
            if "json" not in prompt.lower():
                prompt += "\n\nRespond ONLY with valid JSON. No other text."

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )

            response_text = response.text.strip()

            # Try to extract JSON from response
            try:
                # If response is wrapped in markdown code blocks, extract it
                if response_text.startswith("```"):
                    # Extract from ```json ... ``` or just ``` ... ```
                    lines = response_text.split("\n")
                    json_lines = []
                    in_block = False
                    for line in lines:
                        if line.startswith("```"):
                            in_block = not in_block
                            continue
                        if in_block:
                            json_lines.append(line)
                    response_text = "\n".join(json_lines)

                parsed = json.loads(response_text)
                logger.info(f"✅ Valid JSON response: {parsed}")
                return parsed

            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON from Gemini: {response_text[:200]}")
                raise ValueError(f"Gemini response is not valid JSON: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Gemini API error: {str(e)}")
            raise

    @track(name="gemini_text_call")
    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Call Gemini and return raw text response.

        Args:
            prompt: Full prompt
            temperature: Sampling temperature
            max_tokens: Max output tokens

        Returns:
            Plain text response
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"❌ Gemini API error: {str(e)}")
            raise


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """
    Get or create singleton Gemini client.
    """
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
