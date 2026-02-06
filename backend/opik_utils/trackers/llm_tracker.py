"""
Specialized tracker for LLM calls and token usage
"""
from typing import Dict, Any, Optional
import time
from datetime import datetime, timezone
from opik_utils.client import get_opik_client


class LLMTracker:
    """
    Track LLM calls and token usage

    Usage:
        tracker = LLMTracker(model_name="gemini-2.0-flash")
        await tracker.track_generation(
            prompt="Hello, world!",
            response="Hi there!",
            tokens_used=150,
            metadata={"temperature": 0.7}
        )

    Example:
        async def generate_text(prompt: str):
            tracker = LLMTracker("gemini-2.0-flash")

            response = await llm_service.generate(prompt)

            await tracker.track_generation(
                prompt=prompt,
                response=response.text,
                tokens_used=response.usage.total_tokens,
                metadata={"model": "gemini-2.0-flash"}
            )

            return response.text
    """

    def __init__(self, model_name: str):
        """
        Initialize the LLM tracker

        Args:
            model_name: Name of the LLM model being used
        """
        self.model_name = model_name
        self.opik_client = get_opik_client()
        self.total_tokens = 0
        self.total_cost = 0.0

    async def track_generation(
        self,
        prompt: str,
        response: str,
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track an LLM generation

        Args:
            prompt: The input prompt
            response: The LLM response
            tokens_used: Number of tokens used (if available)
            metadata: Additional metadata (temperature, top_p, etc.)
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        if tokens_used:
            self.total_tokens += tokens_used
            estimated_cost = self._estimate_cost(tokens_used)
            self.total_cost += estimated_cost
        else:
            estimated_cost = None

        print(
            f"📝 LLM generation tracked: {self.model_name} - "
            f"Tokens: {tokens_used or 'N/A'} - "
            f"Cost: ${estimated_cost:.4f}" if estimated_cost else "Cost: N/A"
        )

        # You can add actual Opik tracking here
        # self.opik_client.opik.log_llm_call(...)

    async def track_streaming(
        self,
        prompt: str,
        chunks: list[str],
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track a streaming LLM generation

        Args:
            prompt: The input prompt
            chunks: List of response chunks
            tokens_used: Number of tokens used (if available)
            metadata: Additional metadata
        """
        full_response = "".join(chunks)
        await self.track_generation(
            prompt=prompt,
            response=full_response,
            tokens_used=tokens_used,
            metadata={**(metadata or {}), "streaming": True, "chunks": len(chunks)}
        )

    def _estimate_cost(self, tokens: int) -> float:
        """
        Estimate the cost based on token usage

        Args:
            tokens: Number of tokens used

        Returns:
            float: Estimated cost in dollars
        """
        # Rough estimate - adjust based on actual model pricing
        cost_per_1k = {
            "gemini-2.0-flash": 0.001,
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
        }

        rate = cost_per_1k.get(self.model_name, 0.001)
        return (tokens / 1000) * rate

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregated statistics for all tracked calls

        Returns:
            Dict: Statistics including total tokens, cost, etc.
        """
        return {
            "model_name": self.model_name,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def reset(self) -> None:
        """Reset the tracker statistics"""
        self.total_tokens = 0
        self.total_cost = 0.0
