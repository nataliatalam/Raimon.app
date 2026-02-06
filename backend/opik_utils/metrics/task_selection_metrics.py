"""
Task selection metrics for Opik observability.

Tracks selection accuracy, quality of alternatives, and constraint satisfaction.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class TaskSelectionMetrics:
    """
    Tracks task selection quality and performance.

    Metrics:
    - selection_accuracy: How often optimal task is selected
    - constraint_satisfaction: % of selections that respect constraints
    - alternative_quality: Quality of provided alternatives
    - selection_diversity: Variety in selected tasks across sessions
    - llm_vs_deterministic: Comparison of LLM vs fallback performance
    """

    def __init__(self):
        """Initialize task selection metrics."""
        self.metrics = {
            "total_selections": 0,
            "successful_selections": 0,
            "constraint_violations": 0,
            "llm_selections": 0,
            "llm_successful": 0,
            "fallback_selections": 0,
            "fallback_successful": 0,
            "selections": [],  # Detailed records
        }
        self.created_at = datetime.now(timezone.utc).isoformat()

    def record_selection(
        self,
        selected_task_id: str,
        user_id: str,
        constraints_satisfied: bool,
        is_optimal: bool,
        used_llm: bool,
        alternative_count: int,
        execution_time_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a task selection event.

        Args:
            selected_task_id: ID of selected task
            user_id: User ID
            constraints_satisfied: Whether selection satisfies constraints
            is_optimal: Whether this is optimal task
            used_llm: Whether LLM selector was used (vs deterministic)
            alternative_count: Number of alternatives provided
            execution_time_ms: Time to make selection
            metadata: Additional metadata
        """
        self.metrics["total_selections"] += 1

        if constraints_satisfied:
            self.metrics["successful_selections"] += 1
        else:
            self.metrics["constraint_violations"] += 1

        if used_llm:
            self.metrics["llm_selections"] += 1
            if constraints_satisfied:
                self.metrics["llm_successful"] += 1
        else:
            self.metrics["fallback_selections"] += 1
            if constraints_satisfied:
                self.metrics["fallback_successful"] += 1

        # Store detailed record
        selection_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "selected_task_id": selected_task_id,
            "user_id": user_id,
            "constraints_satisfied": constraints_satisfied,
            "is_optimal": is_optimal,
            "used_llm": used_llm,
            "alternative_count": alternative_count,
            "execution_time_ms": execution_time_ms,
            "metadata": metadata or {},
        }
        self.metrics["selections"].append(selection_record)

        # Keep only recent selections (last 5000)
        if len(self.metrics["selections"]) > 5000:
            self.metrics["selections"] = self.metrics["selections"][-5000:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics summary.

        Returns:
            Dictionary with aggregated metrics
        """
        total = self.metrics["total_selections"]

        if total == 0:
            return {
                "message": "No selections recorded yet",
                "created_at": self.created_at,
            }

        llm_selections = self.metrics["llm_selections"]
        fallback_selections = self.metrics["fallback_selections"]

        llm_rate = (
            self.metrics["llm_successful"] / llm_selections
            if llm_selections > 0
            else 0.0
        )
        fallback_rate = (
            self.metrics["fallback_successful"] / fallback_selections
            if fallback_selections > 0
            else 0.0
        )

        return {
            "total_selections": total,
            "successful_selections": self.metrics["successful_selections"],
            "success_rate": self.metrics["successful_selections"] / total,
            "constraint_violation_rate": self.metrics["constraint_violations"] / total,
            "llm_selection_count": llm_selections,
            "llm_success_rate": llm_rate,
            "fallback_selection_count": fallback_selections,
            "fallback_success_rate": fallback_rate,
            "llm_vs_fallback_diff": llm_rate - fallback_rate,
            "created_at": self.created_at,
        }

    def get_recent_metrics(self, minutes: int = 60) -> Dict[str, Any]:
        """
        Get metrics for recent selections.

        Args:
            minutes: Look back this many minutes

        Returns:
            Metrics for recent period
        """
        cutoff_time = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()

        recent = [
            s for s in self.metrics["selections"]
            if s["timestamp"] >= cutoff_time
        ]

        if not recent:
            return {
                "period_minutes": minutes,
                "recent_selections": 0,
            }

        successful = sum(1 for s in recent if s["constraints_satisfied"])
        llm = [s for s in recent if s["used_llm"]]
        fallback = [s for s in recent if not s["used_llm"]]

        return {
            "period_minutes": minutes,
            "recent_selections": len(recent),
            "recent_success_rate": successful / len(recent),
            "recent_constraint_violation_rate": 1 - (successful / len(recent)),
            "recent_llm_selections": len(llm),
            "recent_llm_success_rate": (
                sum(1 for s in llm if s["constraints_satisfied"]) / len(llm)
                if llm else 0.0
            ),
            "recent_fallback_selections": len(fallback),
            "recent_fallback_success_rate": (
                sum(1 for s in fallback if s["constraints_satisfied"]) / len(fallback)
                if fallback else 0.0
            ),
            "avg_execution_time_ms": sum(s["execution_time_ms"] for s in recent) / len(recent),
            "avg_alternatives": sum(s["alternative_count"] for s in recent) / len(recent),
        }

    def get_user_metrics(self, user_id: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get metrics for a specific user.

        Args:
            user_id: User ID
            limit: Maximum selections to analyze

        Returns:
            User-specific metrics
        """
        user_selections = [
            s for s in self.metrics["selections"]
            if s["user_id"] == user_id
        ][-limit:]

        if not user_selections:
            return {
                "user_id": user_id,
                "message": "No selections for this user",
            }

        successful = sum(1 for s in user_selections if s["constraints_satisfied"])
        optimal = sum(1 for s in user_selections if s["is_optimal"])

        return {
            "user_id": user_id,
            "selection_count": len(user_selections),
            "success_rate": successful / len(user_selections),
            "optimal_rate": optimal / len(user_selections),
            "avg_alternatives": sum(s["alternative_count"] for s in user_selections) / len(user_selections),
            "preferred_selector": "LLM" if sum(1 for s in user_selections if s["used_llm"]) > len(user_selections) / 2 else "Deterministic",
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "total_selections": 0,
            "successful_selections": 0,
            "constraint_violations": 0,
            "llm_selections": 0,
            "llm_successful": 0,
            "fallback_selections": 0,
            "fallback_successful": 0,
            "selections": [],
        }
        self.created_at = datetime.now(timezone.utc).isoformat()


# Global instance
_selection_metrics = TaskSelectionMetrics()


def get_task_selection_metrics() -> TaskSelectionMetrics:
    """Get the global task selection metrics instance."""
    return _selection_metrics


def record_selection(
    selected_task_id: str,
    user_id: str,
    constraints_satisfied: bool,
    is_optimal: bool,
    used_llm: bool,
    alternative_count: int,
    execution_time_ms: float,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Record a task selection event globally.

    Args:
        selected_task_id: ID of selected task
        user_id: User ID
        constraints_satisfied: Whether selection satisfies constraints
        is_optimal: Whether this is optimal task
        used_llm: Whether LLM selector was used
        alternative_count: Number of alternatives provided
        execution_time_ms: Time to make selection
        metadata: Additional metadata
    """
    _selection_metrics.record_selection(
        selected_task_id=selected_task_id,
        user_id=user_id,
        constraints_satisfied=constraints_satisfied,
        is_optimal=is_optimal,
        used_llm=used_llm,
        alternative_count=alternative_count,
        execution_time_ms=execution_time_ms,
        metadata=metadata
    )
