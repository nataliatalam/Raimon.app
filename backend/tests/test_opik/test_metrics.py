"""
Test Opik custom metrics.

Tests for agent performance, task selection, and user engagement metrics.
"""

import pytest
from datetime import datetime, timedelta
from opik_utils.metrics import (
    AgentMetrics,
    AgentMetricsCollector,
    get_metrics_collector,
    TaskSelectionMetrics,
    get_task_selection_metrics,
    UserEngagementMetrics,
    get_engagement_metrics,
)


@pytest.mark.unit
@pytest.mark.agent
class TestAgentMetrics:
    """Tests for AgentMetrics."""

    def test_agent_metrics_initialization(self):
        """Test AgentMetrics initialization."""
        metrics = AgentMetrics("test_agent")

        assert metrics.agent_name == "test_agent"
        assert metrics.metrics["execution_count"] == 0

    def test_record_successful_execution(self):
        """Test recording successful agent execution."""
        metrics = AgentMetrics("test_agent")

        metrics.record_execution(latency_ms=150.0, success=True)

        assert metrics.metrics["execution_count"] == 1
        assert metrics.metrics["success_count"] == 1
        assert metrics.metrics["total_latency_ms"] == 150.0

    def test_record_failed_execution(self):
        """Test recording failed agent execution."""
        metrics = AgentMetrics("test_agent")

        metrics.record_execution(
            latency_ms=5000.0,
            success=False,
            error="Timeout"
        )

        assert metrics.metrics["execution_count"] == 1
        assert metrics.metrics["error_count"] == 1
        assert metrics.metrics["success_count"] == 0

    def test_record_recovered_execution(self):
        """Test recording recovered execution."""
        metrics = AgentMetrics("test_agent")

        metrics.record_execution(
            latency_ms=2000.0,
            success=True,
            error="Initial timeout, recovered",
            recovered=True
        )

        assert metrics.metrics["recovery_count"] == 1

    def test_latency_tracking(self):
        """Test latency min/max/avg tracking."""
        metrics = AgentMetrics("test_agent")

        metrics.record_execution(latency_ms=100.0, success=True)
        metrics.record_execution(latency_ms=200.0, success=True)
        metrics.record_execution(latency_ms=150.0, success=True)

        agg = metrics.get_metrics()

        assert agg["min_latency_ms"] == 100.0
        assert agg["max_latency_ms"] == 200.0
        assert agg["avg_latency_ms"] == 150.0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = AgentMetrics("test_agent")

        metrics.record_execution(latency_ms=100.0, success=True)
        metrics.record_execution(latency_ms=100.0, success=True)
        metrics.record_execution(latency_ms=100.0, success=False)

        agg = metrics.get_metrics()

        assert agg["success_rate"] == pytest.approx(2/3)

    def test_fallback_rate(self):
        """Test fallback rate tracking."""
        metrics = AgentMetrics("test_agent")

        metrics.record_execution(latency_ms=100.0, success=True)
        metrics.record_execution(latency_ms=100.0, success=True, used_fallback=True)
        metrics.record_execution(latency_ms=100.0, success=True, used_fallback=True)

        agg = metrics.get_metrics()

        assert agg["fallback_rate"] == pytest.approx(2/3)

    def test_get_recent_metrics(self):
        """Test getting recent metrics."""
        metrics = AgentMetrics("test_agent")

        # Record with old timestamp
        metrics.record_execution(latency_ms=100.0, success=True)

        recent = metrics.get_recent_metrics(minutes=1)

        # Recent should be empty or small
        assert recent["recent_executions"] <= 1


@pytest.mark.unit
@pytest.mark.agent
class TestAgentMetricsCollector:
    """Tests for AgentMetricsCollector."""

    def test_collector_initialization(self):
        """Test collector initialization."""
        collector = AgentMetricsCollector()

        assert len(collector.agents) == 0

    def test_get_or_create_agent(self):
        """Test getting or creating agent metrics."""
        collector = AgentMetricsCollector()

        metrics1 = collector.get_or_create_agent("agent-1")
        metrics2 = collector.get_or_create_agent("agent-1")

        assert metrics1 is metrics2  # Same instance

    def test_record_agent_execution(self):
        """Test recording execution through collector."""
        collector = AgentMetricsCollector()

        collector.record_agent_execution(
            agent_name="agent-1",
            latency_ms=150.0,
            success=True
        )

        metrics = collector.get_agent_metrics("agent-1")

        assert metrics["execution_count"] == 1
        assert metrics["success_rate"] == 1.0

    def test_get_all_metrics(self):
        """Test getting metrics for all agents."""
        collector = AgentMetricsCollector()

        collector.record_agent_execution("agent-1", 100.0, True)
        collector.record_agent_execution("agent-2", 200.0, True)

        all_metrics = collector.get_all_metrics()

        assert "agent-1" in all_metrics
        assert "agent-2" in all_metrics

    def test_get_health_summary(self):
        """Test getting overall health summary."""
        collector = AgentMetricsCollector()

        collector.record_agent_execution("agent-1", 100.0, True)
        collector.record_agent_execution("agent-1", 100.0, True)
        collector.record_agent_execution("agent-2", 100.0, False)

        summary = collector.get_health_summary()

        assert summary["total_agents"] == 2
        assert summary["total_executions"] == 3
        assert summary["overall_success_rate"] == pytest.approx(2/3)


@pytest.mark.unit
@pytest.mark.agent
class TestTaskSelectionMetrics:
    """Tests for TaskSelectionMetrics."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = TaskSelectionMetrics()

        assert metrics.metrics["total_selections"] == 0

    def test_record_selection(self):
        """Test recording task selection."""
        metrics = TaskSelectionMetrics()

        metrics.record_selection(
            selected_task_id="task-1",
            user_id="user-123",
            constraints_satisfied=True,
            is_optimal=True,
            used_llm=True,
            alternative_count=3,
            execution_time_ms=250.0
        )

        agg = metrics.get_metrics()

        assert agg["total_selections"] == 1
        assert agg["successful_selections"] == 1

    def test_llm_vs_deterministic_comparison(self):
        """Test LLM vs deterministic selection comparison."""
        metrics = TaskSelectionMetrics()

        metrics.record_selection(
            selected_task_id="task-1",
            user_id="user-123",
            constraints_satisfied=True,
            is_optimal=True,
            used_llm=True,
            alternative_count=3,
            execution_time_ms=250.0
        )

        metrics.record_selection(
            selected_task_id="task-2",
            user_id="user-123",
            constraints_satisfied=True,
            is_optimal=False,
            used_llm=False,
            alternative_count=1,
            execution_time_ms=50.0
        )

        agg = metrics.get_metrics()

        assert agg["llm_selection_count"] == 1
        assert agg["fallback_selection_count"] == 1

    def test_constraint_violation_tracking(self):
        """Test constraint violation tracking."""
        metrics = TaskSelectionMetrics()

        metrics.record_selection(
            selected_task_id="task-1",
            user_id="user-123",
            constraints_satisfied=False,  # Violates constraint
            is_optimal=False,
            used_llm=False,
            alternative_count=0,
            execution_time_ms=50.0
        )

        agg = metrics.get_metrics()

        assert agg["constraint_violation_rate"] == 1.0

    def test_get_user_metrics(self):
        """Test getting metrics for specific user."""
        metrics = TaskSelectionMetrics()

        metrics.record_selection(
            selected_task_id="task-1",
            user_id="user-123",
            constraints_satisfied=True,
            is_optimal=True,
            used_llm=True,
            alternative_count=2,
            execution_time_ms=150.0
        )

        metrics.record_selection(
            selected_task_id="task-2",
            user_id="user-456",
            constraints_satisfied=False,
            is_optimal=False,
            used_llm=False,
            alternative_count=0,
            execution_time_ms=50.0
        )

        user_metrics = metrics.get_user_metrics("user-123")

        assert user_metrics["selection_count"] == 1
        assert user_metrics["success_rate"] == 1.0


@pytest.mark.unit
@pytest.mark.agent
class TestUserEngagementMetrics:
    """Tests for UserEngagementMetrics."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = UserEngagementMetrics()

        assert metrics.metrics["total_app_opens"] == 0

    def test_record_app_open(self):
        """Test recording app open."""
        metrics = UserEngagementMetrics()

        metrics.record_app_open("user-123", "session-1")

        assert metrics.metrics["total_app_opens"] == 1
        assert "user-123" in metrics.metrics["daily_active_users"]

    def test_record_check_in(self):
        """Test recording check-in."""
        metrics = UserEngagementMetrics()

        metrics.record_app_open("user-123", "session-1")
        metrics.record_check_in("user-123", "session-1")

        assert metrics.metrics["total_check_ins"] == 1

    def test_record_task_action(self):
        """Test recording task actions."""
        metrics = UserEngagementMetrics()

        metrics.record_app_open("user-123", "session-1")
        metrics.record_task_action("user-123", "session-1", "start")
        metrics.record_task_action("user-123", "session-1", "complete")

        assert metrics.metrics["total_tasks_started"] == 1
        assert metrics.metrics["total_tasks_completed"] == 1

    def test_engagement_metrics_aggregation(self):
        """Test engagement metrics aggregation."""
        metrics = UserEngagementMetrics()

        metrics.record_app_open("user-123", "session-1")
        metrics.record_check_in("user-123", "session-1")
        metrics.record_task_action("user-123", "session-1", "start")
        metrics.record_task_action("user-123", "session-1", "complete")

        agg = metrics.get_metrics()

        assert agg["total_app_opens"] == 1
        assert agg["check_in_rate"] == 1.0
        assert agg["task_completion_rate"] == 1.0

    def test_get_user_engagement(self):
        """Test getting engagement for specific user."""
        metrics = UserEngagementMetrics()

        metrics.record_app_open("user-123", "session-1")
        metrics.record_check_in("user-123", "session-1")
        metrics.record_task_action("user-123", "session-1", "start")
        metrics.record_task_action("user-123", "session-1", "complete")

        user_engagement = metrics.get_user_engagement("user-123")

        assert user_engagement["session_count"] == 1
        assert user_engagement["check_in_rate"] == 1.0
        assert user_engagement["task_completion_rate"] == 1.0

    def test_daily_active_users(self):
        """Test daily active users tracking."""
        metrics = UserEngagementMetrics()

        metrics.record_app_open("user-1", "session-1")
        metrics.record_app_open("user-2", "session-2")
        metrics.record_app_open("user-3", "session-3")

        agg = metrics.get_metrics()

        assert agg["daily_active_users"] == 3


@pytest.mark.unit
@pytest.mark.agent
class TestMetricsConsistency:
    """Tests for metrics consistency and reliability."""

    def test_metrics_are_cumulative(self):
        """Test that metrics accumulate correctly."""
        metrics = AgentMetrics("agent-1")

        for i in range(10):
            metrics.record_execution(
                latency_ms=100.0 + i * 10,
                success=i < 8  # 8 successes, 2 failures
            )

        agg = metrics.get_metrics()

        assert agg["execution_count"] == 10
        assert metrics.metrics["success_count"] == 8
        assert metrics.metrics["error_count"] == 2

    def test_reset_metrics(self):
        """Test resetting metrics."""
        metrics = AgentMetrics("agent-1")

        metrics.record_execution(latency_ms=100.0, success=True)
        metrics.reset()

        assert metrics.metrics["execution_count"] == 0
        assert metrics.metrics["success_count"] == 0
