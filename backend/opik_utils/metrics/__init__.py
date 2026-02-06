"""
Custom Opik metrics for Raimon.

Implements metrics for:
- Agent performance (latency, success rate, error recovery)
- Task selection accuracy
- User engagement tracking
"""

from opik_utils.metrics.agent_metrics import (
    AgentMetrics,
    AgentMetricsCollector,
    get_metrics_collector,
)
from opik_utils.metrics.task_selection_metrics import (
    TaskSelectionMetrics,
    get_task_selection_metrics,
    record_selection,
)
from opik_utils.metrics.user_engagement import (
    UserEngagementMetrics,
    get_engagement_metrics,
    record_app_open,
    record_check_in,
    record_task_action,
)

__all__ = [
    # Agent metrics
    "AgentMetrics",
    "AgentMetricsCollector",
    "get_metrics_collector",
    # Task selection metrics
    "TaskSelectionMetrics",
    "get_task_selection_metrics",
    "record_selection",
    # User engagement metrics
    "UserEngagementMetrics",
    "get_engagement_metrics",
    "record_app_open",
    "record_check_in",
    "record_task_action",
]
