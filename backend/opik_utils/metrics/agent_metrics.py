"""
Agent performance metrics for Opik observability.

Tracks latency, success rate, error recovery, and performance of individual agents.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class AgentMetrics:
    """
    Tracks performance metrics for individual agents.

    Metrics:
    - execution_latency_ms: Time to execute agent
    - success_rate: Percentage of successful executions
    - error_count: Total errors encountered
    - error_recovery_rate: % of errors that were recovered
    - fallback_rate: % of times fallback was used
    """

    def __init__(self, agent_name: str):
        """
        Initialize metrics tracker for an agent.

        Args:
            agent_name: Name of the agent (e.g., "llm_do_selector")
        """
        self.agent_name = agent_name
        self.metrics = {
            "execution_count": 0,
            "success_count": 0,
            "error_count": 0,
            "recovery_count": 0,
            "fallback_count": 0,
            "total_latency_ms": 0.0,
            "min_latency_ms": float('inf'),
            "max_latency_ms": 0.0,
            "executions": [],  # List of detailed execution records
        }
        self.created_at = datetime.now(timezone.utc).isoformat()

    def record_execution(
        self,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None,
        recovered: bool = False,
        used_fallback: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a single agent execution.

        Args:
            latency_ms: Execution time in milliseconds
            success: Whether execution succeeded
            error: Error message if failed
            recovered: Whether error was recovered
            used_fallback: Whether fallback was used
            metadata: Additional execution metadata
        """
        self.metrics["execution_count"] += 1

        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["error_count"] += 1

        if recovered:
            self.metrics["recovery_count"] += 1

        if used_fallback:
            self.metrics["fallback_count"] += 1

        self.metrics["total_latency_ms"] += latency_ms
        self.metrics["min_latency_ms"] = min(self.metrics["min_latency_ms"], latency_ms)
        self.metrics["max_latency_ms"] = max(self.metrics["max_latency_ms"], latency_ms)

        # Store detailed record
        execution_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_ms": latency_ms,
            "success": success,
            "error": error,
            "recovered": recovered,
            "used_fallback": used_fallback,
            "metadata": metadata or {},
        }
        self.metrics["executions"].append(execution_record)

        # Keep only recent executions (last 1000)
        if len(self.metrics["executions"]) > 1000:
            self.metrics["executions"] = self.metrics["executions"][-1000:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics summary.

        Returns:
            Dictionary with aggregated metrics
        """
        execution_count = self.metrics["execution_count"]

        if execution_count == 0:
            return {
                "agent_name": self.agent_name,
                "execution_count": 0,
                "message": "No executions recorded yet",
            }

        return {
            "agent_name": self.agent_name,
            "execution_count": execution_count,
            "success_rate": self.metrics["success_count"] / execution_count,
            "error_rate": self.metrics["error_count"] / execution_count,
            "recovery_rate": (
                self.metrics["recovery_count"] / self.metrics["error_count"]
                if self.metrics["error_count"] > 0
                else 0.0
            ),
            "fallback_rate": self.metrics["fallback_count"] / execution_count,
            "avg_latency_ms": self.metrics["total_latency_ms"] / execution_count,
            "min_latency_ms": self.metrics["min_latency_ms"],
            "max_latency_ms": self.metrics["max_latency_ms"],
            "total_errors": self.metrics["error_count"],
            "total_recoveries": self.metrics["recovery_count"],
            "total_fallbacks": self.metrics["fallback_count"],
            "created_at": self.created_at,
        }

    def get_recent_metrics(self, minutes: int = 5) -> Dict[str, Any]:
        """
        Get metrics for recent executions.

        Args:
            minutes: Look back this many minutes

        Returns:
            Metrics for recent period
        """
        cutoff_time = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()

        recent = [
            e for e in self.metrics["executions"]
            if e["timestamp"] >= cutoff_time
        ]

        if not recent:
            return {"agent_name": self.agent_name, "recent_executions": 0}

        success_count = sum(1 for e in recent if e["success"])
        error_count = len(recent) - success_count
        recovery_count = sum(1 for e in recent if e["recovered"])
        fallback_count = sum(1 for e in recent if e["used_fallback"])
        total_latency = sum(e["latency_ms"] for e in recent)

        return {
            "agent_name": self.agent_name,
            "period_minutes": minutes,
            "recent_executions": len(recent),
            "recent_success_rate": success_count / len(recent),
            "recent_error_rate": error_count / len(recent),
            "recent_recovery_rate": recovery_count / error_count if error_count > 0 else 0.0,
            "recent_fallback_rate": fallback_count / len(recent),
            "recent_avg_latency_ms": total_latency / len(recent),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "execution_count": 0,
            "success_count": 0,
            "error_count": 0,
            "recovery_count": 0,
            "fallback_count": 0,
            "total_latency_ms": 0.0,
            "min_latency_ms": float('inf'),
            "max_latency_ms": 0.0,
            "executions": [],
        }
        self.created_at = datetime.now(timezone.utc).isoformat()


class AgentMetricsCollector:
    """
    Centralized collector for all agent metrics.

    Maintains metrics for multiple agents and provides aggregated views.
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self.agents: Dict[str, AgentMetrics] = {}

    def get_or_create_agent(self, agent_name: str) -> AgentMetrics:
        """
        Get or create metrics tracker for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentMetrics instance for this agent
        """
        if agent_name not in self.agents:
            self.agents[agent_name] = AgentMetrics(agent_name)
        return self.agents[agent_name]

    def record_agent_execution(
        self,
        agent_name: str,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None,
        recovered: bool = False,
        used_fallback: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record execution for an agent.

        Args:
            agent_name: Name of the agent
            latency_ms: Execution time in milliseconds
            success: Whether execution succeeded
            error: Error message if failed
            recovered: Whether error was recovered
            used_fallback: Whether fallback was used
            metadata: Additional metadata
        """
        agent_metrics = self.get_or_create_agent(agent_name)
        agent_metrics.record_execution(
            latency_ms=latency_ms,
            success=success,
            error=error,
            recovered=recovered,
            used_fallback=used_fallback,
            metadata=metadata
        )

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all agents.

        Returns:
            Dictionary mapping agent names to their metrics
        """
        return {
            name: metrics.get_metrics()
            for name, metrics in self.agents.items()
        }

    def get_agent_metrics(self, agent_name: str) -> Dict[str, Any]:
        """
        Get metrics for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Metrics for this agent, or empty dict if not tracked
        """
        if agent_name not in self.agents:
            return {"agent_name": agent_name, "message": "No data"}
        return self.agents[agent_name].get_metrics()

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get summary of overall agent health.

        Returns:
            Dictionary with overall health metrics
        """
        if not self.agents:
            return {"total_agents": 0, "message": "No agents tracked"}

        # Sum raw counts from agent metrics, not aggregated results
        total_executions = sum(m.metrics["execution_count"] for m in self.agents.values())
        total_success = sum(m.metrics["success_count"] for m in self.agents.values())
        total_errors = sum(m.metrics["error_count"] for m in self.agents.values())
        total_recoveries = sum(m.metrics["recovery_count"] for m in self.agents.values())
        all_metrics = self.get_all_metrics()

        return {
            "total_agents": len(self.agents),
            "total_executions": total_executions,
            "overall_success_rate": total_success / total_executions if total_executions > 0 else 0.0,
            "overall_error_rate": total_errors / total_executions if total_executions > 0 else 0.0,
            "overall_recovery_rate": (
                total_recoveries / total_errors if total_errors > 0 else 0.0
            ),
            "healthy_agents": sum(
                1 for m in all_metrics.values()
                if m.get("success_rate", 0) >= 0.95
            ),
            "agents_with_issues": sum(
                1 for m in all_metrics.values()
                if m.get("success_rate", 1) < 0.85
            ),
        }


# Global collector instance
_metrics_collector = AgentMetricsCollector()


def get_metrics_collector() -> AgentMetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector
