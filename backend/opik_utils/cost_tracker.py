"""
Cost tracking for LLM usage across agents
"""
from opik_utils import get_opik_client
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CostTracker:
    """
    Tracks LLM costs per agent and user

    Usage:
        cost_tracker = CostTracker()
        cost_tracker.log_usage(
            agent_name="priority_engine",
            user_id="user_123",
            tokens={"input": 420, "output": 180},
            model="gemini-2.0-flash"
        )
    """

    # Gemini pricing as of 2026 ($/1K tokens)
    GEMINI_PRICING = {
        "gemini-2.0-flash": {
            "input": 0.00001,   # $0.01 per 1M tokens
            "output": 0.00003   # $0.03 per 1M tokens
        },
        "gemini-2.5-flash": {
            "input": 0.000015,  # $0.015 per 1M tokens
            "output": 0.000045  # $0.045 per 1M tokens
        },
        "gemini-1.5-flash": {
            "input": 0.0000075,  # $0.0075 per 1M tokens
            "output": 0.00003    # $0.03 per 1M tokens
        },
        "gemini-1.5-flash-001": {
            "input": 0.0000075,
            "output": 0.00003
        }
    }

    def __init__(self):
        self.opik_client = get_opik_client()

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost for a single LLM call

        Args:
            model: Model name (e.g., "gemini-2.0-flash")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            float: Total cost in USD
        """
        pricing = self.GEMINI_PRICING.get(
            model,
            self.GEMINI_PRICING["gemini-2.0-flash"]  # Default fallback
        )

        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]

        return input_cost + output_cost

    def log_usage(
        self,
        agent_name: str,
        user_id: str,
        tokens: Dict[str, int],
        model: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Log LLM usage to Opik

        Args:
            agent_name: Name of the agent making the call
            user_id: User ID
            tokens: Dict with "input" and "output" keys
            model: Model name
            trace_id: Optional trace ID to link to
            metadata: Additional metadata to log

        Returns:
            Dict with cost information
        """
        cost = self.calculate_cost(model, tokens["input"], tokens["output"])

        log_data = {
            "agent": agent_name,
            "user_id": user_id,
            "model": model,
            "input_tokens": tokens["input"],
            "output_tokens": tokens["output"],
            "total_tokens": tokens["input"] + tokens["output"],
            "cost_usd": round(cost, 6),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if trace_id:
            log_data["trace_id"] = trace_id

        if metadata:
            log_data.update(metadata)

        # Log to Opik
        try:
            self.opik_client.opik.log_metric(
                metric_name="llm_cost",
                value=cost,
                metadata=log_data
            )

            logger.info(
                f"💰 LLM Cost: {agent_name} - "
                f"${cost:.6f} ({tokens['input']}→{tokens['output']} tokens)"
            )

        except Exception as e:
            logger.error(f"Failed to log cost to Opik: {e}")

        return log_data

    def get_user_daily_cost(self, user_id: str, date: Optional[str] = None) -> float:
        """
        Get total cost for a user on a specific date

        Args:
            user_id: User ID
            date: Date in ISO format (defaults to today)

        Returns:
            float: Total cost in USD
        """
        if date is None:
            date = datetime.utcnow().date().isoformat()

        # Query Opik for metrics
        # This is a placeholder - actual implementation depends on Opik API
        try:
            # Example query (adjust based on actual Opik SDK)
            metrics = self.opik_client.opik.get_metrics(
                metric_name="llm_cost",
                start_date=date,
                end_date=date,
                filters={"user_id": user_id}
            )

            total_cost = sum(m.value for m in metrics)
            return round(total_cost, 4)

        except Exception as e:
            logger.error(f"Failed to get user daily cost: {e}")
            return 0.0

    def get_agent_statistics(
        self,
        agent_name: str,
        days: int = 7
    ) -> Dict[str, any]:
        """
        Get statistics for a specific agent over N days

        Args:
            agent_name: Name of the agent
            days: Number of days to look back

        Returns:
            Dict with statistics
        """
        # Placeholder - implement based on Opik API
        return {
            "agent_name": agent_name,
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_cost_per_call": 0.0,
            "period_days": days
        }


# Global instance for easy import
cost_tracker = CostTracker()
