"""
Agent management and health endpoints for REST API.

Provides endpoints for monitoring and managing agent health, performance,
and operational status.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agents",
    tags=["agent-management"],
    responses={404: {"description": "Agent not found"}},
)


@router.get("/health", tags=["health"])
async def get_agent_health() -> Dict[str, Any]:
    """
    Get overall agent system health status.

    Returns:
        Dictionary with health metrics:
        - status: "healthy", "degraded", or "critical"
        - total_agents: Number of tracked agents
        - healthy_agents: Count of agents with good metrics
        - agents_with_issues: Count of agents below threshold
        - avg_success_rate: Average success rate across agents
    """
    from opik_utils.metrics import get_metrics_collector

    collector = get_metrics_collector()
    health = collector.get_health_summary()

    # Determine overall status
    if health.get("overall_success_rate", 0) >= 0.95:
        status = "healthy"
    elif health.get("overall_success_rate", 0) >= 0.85:
        status = "degraded"
    else:
        status = "critical"

    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **health,
    }


@router.get("/status", tags=["status"])
async def get_agent_status(
    agent_name: Optional[str] = Query(None, description="Filter by agent name")
) -> Dict[str, Any]:
    """
    Get agent operational status and metrics.

    Args:
        agent_name: Optional agent name to filter by

    Returns:
        Agent status information with current metrics
    """
    from opik_utils.metrics import get_metrics_collector

    collector = get_metrics_collector()

    if agent_name:
        metrics = collector.get_agent_metrics(agent_name)
        if "message" in metrics and "No data" in metrics.get("message", ""):
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        return {
            "agent_name": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **metrics,
        }
    else:
        all_metrics = collector.get_all_metrics()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_count": len(all_metrics),
            "agents": all_metrics,
        }


@router.get("/performance", tags=["metrics"])
async def get_agent_performance(
    time_window_minutes: int = Query(5, description="Time window in minutes"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name")
) -> Dict[str, Any]:
    """
    Get recent agent performance metrics.

    Args:
        time_window_minutes: Time window for metrics (default 5 minutes)
        agent_name: Optional agent name to filter by

    Returns:
        Performance metrics for recent period
    """
    from opik_utils.metrics import get_metrics_collector

    collector = get_metrics_collector()

    if agent_name:
        if agent_name not in collector.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

        agent_metrics = collector.agents[agent_name]
        recent = agent_metrics.get_recent_metrics(minutes=time_window_minutes)

        return {
            "agent_name": agent_name,
            "time_window_minutes": time_window_minutes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **recent,
        }
    else:
        all_metrics = {}
        for agent_name, agent_metrics in collector.agents.items():
            recent = agent_metrics.get_recent_metrics(minutes=time_window_minutes)
            all_metrics[agent_name] = recent

        return {
            "time_window_minutes": time_window_minutes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": all_metrics,
        }


@router.get("/errors", tags=["errors"])
async def get_agent_errors(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    limit: int = Query(10, description="Maximum errors to return"),
) -> Dict[str, Any]:
    """
    Get recent agent errors.

    Args:
        agent_name: Optional agent name to filter by
        limit: Maximum number of errors to return

    Returns:
        Recent errors for agents
    """
    from opik_utils.metrics import get_metrics_collector

    collector = get_metrics_collector()

    errors_by_agent = {}

    if agent_name:
        if agent_name not in collector.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

        agent_metrics = collector.agents[agent_name]
        executions = agent_metrics.metrics.get("executions", [])
        agent_errors = [
            {
                "timestamp": e["timestamp"],
                "error": e["error"],
                "recovered": e["recovered"],
                "latency_ms": e["latency_ms"],
            }
            for e in executions
            if e.get("error") is not None
        ]
        errors_by_agent[agent_name] = agent_errors[-limit:]
    else:
        for name, agent_metrics in collector.agents.items():
            executions = agent_metrics.metrics.get("executions", [])
            agent_errors = [
                {
                    "timestamp": e["timestamp"],
                    "error": e["error"],
                    "recovered": e["recovered"],
                }
                for e in executions
                if e.get("error") is not None
            ]
            if agent_errors:
                errors_by_agent[name] = agent_errors[-limit:]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents_with_errors": len(errors_by_agent),
        "errors": errors_by_agent,
    }


@router.post("/reset/{agent_name}", tags=["control"])
async def reset_agent_metrics(agent_name: str) -> Dict[str, Any]:
    """
    Reset metrics for an agent.

    Args:
        agent_name: Name of agent to reset

    Returns:
        Confirmation of reset
    """
    from opik_utils.metrics import get_metrics_collector

    collector = get_metrics_collector()

    if agent_name not in collector.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    collector.agents[agent_name].reset()

    logger.info(f"Reset metrics for agent: {agent_name}")

    return {
        "agent_name": agent_name,
        "status": "reset",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/evaluators", tags=["quality"])
async def get_available_evaluators() -> Dict[str, Any]:
    """
    Get list of available quality evaluators.

    Returns:
        Dictionary of available evaluators with descriptions
    """
    from opik_utils.evaluators import (
        HallucinationEvaluator,
        MotivationRubricEvaluator,
        SelectionAccuracyEvaluator,
        StuckDetectionEvaluator,
    )

    evaluators = {
        "hallucination_evaluator": {
            "name": "Hallucination Evaluator",
            "description": "Detects hallucinations in LLM agent outputs",
            "dimensions": ["factual_accuracy", "consistency"],
        },
        "motivation_rubric": {
            "name": "Motivation Rubric Evaluator",
            "description": "Evaluates motivation message quality",
            "dimensions": ["empathy", "actionability", "personalization", "tone", "relevance"],
        },
        "selection_accuracy": {
            "name": "Selection Accuracy Evaluator",
            "description": "Validates task selection against constraints",
            "dimensions": ["constraint_satisfaction", "priority_alignment", "optimality"],
        },
        "stuck_detection": {
            "name": "Stuck Detection Evaluator",
            "description": "Evaluates stuck state detection and interventions",
            "dimensions": ["detection_accuracy", "intervention_quality"],
        },
    }

    return {
        "evaluators": evaluators,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/task-selection/stats", tags=["task-selection"])
async def get_task_selection_stats(
    time_window_hours: int = Query(24, description="Time window in hours")
) -> Dict[str, Any]:
    """
    Get task selection statistics.

    Args:
        time_window_hours: Time window for statistics

    Returns:
        Task selection performance metrics
    """
    from opik_utils.metrics import get_task_selection_metrics

    metrics = get_task_selection_metrics()
    recent = metrics.get_recent_metrics(minutes=time_window_hours * 60)

    return {
        "time_window_hours": time_window_hours,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **recent,
    }


@router.get("/engagement/stats", tags=["engagement"])
async def get_engagement_stats(
    time_window_hours: int = Query(24, description="Time window in hours")
) -> Dict[str, Any]:
    """
    Get user engagement statistics.

    Args:
        time_window_hours: Time window for statistics

    Returns:
        User engagement metrics
    """
    from opik_utils.metrics import get_engagement_metrics

    metrics = get_engagement_metrics()
    recent = metrics.get_recent_metrics(hours=time_window_hours)

    return {
        "time_window_hours": time_window_hours,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **recent,
    }


@router.get("/user/{user_id}/engagement", tags=["engagement"])
async def get_user_engagement(user_id: str) -> Dict[str, Any]:
    """
    Get engagement metrics for a specific user.

    Args:
        user_id: User ID

    Returns:
        User-specific engagement metrics
    """
    from opik_utils.metrics import get_engagement_metrics

    metrics = get_engagement_metrics()
    user_metrics = metrics.get_user_engagement(user_id)

    if "message" in user_metrics:
        raise HTTPException(status_code=404, detail=f"No engagement data for user {user_id}")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **user_metrics,
    }
