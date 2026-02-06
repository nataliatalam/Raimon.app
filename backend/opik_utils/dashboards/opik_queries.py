"""
Pre-built Opik dashboard queries for Raimon observability.

Provides reusable queries for common dashboard views and reports.
These queries extract data from Opik spans and traces for visualization.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone


class OpikQueries:
    """
    Collection of pre-built Opik queries for dashboard visualization.

    Queries are designed to work with Opik's SDK and provide common metrics
    for monitoring agent performance, task selection, and user engagement.
    """

    # Agent Performance Queries
    @staticmethod
    def agent_latency_trend(
        agent_name: str,
        time_range_hours: int = 24,
        bucket_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Get agent execution latency over time.

        Args:
            agent_name: Name of agent to track
            time_range_hours: Hours to look back
            bucket_minutes: Time bucket size for aggregation

        Returns:
            Query configuration for latency trend
        """
        return {
            "query_type": "latency_trend",
            "agent_name": agent_name,
            "time_range_hours": time_range_hours,
            "bucket_minutes": bucket_minutes,
            "metric": "execution_latency_ms",
            "aggregations": ["avg", "p50", "p95", "p99", "max"],
            "visualization": "line_chart",
        }

    @staticmethod
    def agent_success_rate(
        agent_name: Optional[str] = None,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get agent success rates.

        Args:
            agent_name: Specific agent (None for all)
            time_range_hours: Hours to look back

        Returns:
            Query configuration for success rates
        """
        return {
            "query_type": "success_rate",
            "agent_name": agent_name,
            "time_range_hours": time_range_hours,
            "metric": "success_count / execution_count",
            "filters": {
                "has_success_field": True,
            },
            "visualization": "gauge",
        }

    @staticmethod
    def agent_error_distribution() -> Dict[str, Any]:
        """
        Get distribution of errors by type.

        Returns:
            Query configuration for error distribution
        """
        return {
            "query_type": "error_distribution",
            "group_by": "error_type",
            "time_range_hours": 24,
            "metric": "count",
            "order_by": "desc",
            "limit": 10,
            "visualization": "pie_chart",
        }

    @staticmethod
    def agent_comparison(
        agent_names: List[str],
        metric: str = "success_rate",
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Compare metrics across multiple agents.

        Args:
            agent_names: List of agents to compare
            metric: Metric to compare (success_rate, latency, etc.)
            time_range_hours: Hours to look back

        Returns:
            Query configuration for agent comparison
        """
        return {
            "query_type": "agent_comparison",
            "agents": agent_names,
            "metric": metric,
            "time_range_hours": time_range_hours,
            "visualization": "bar_chart",
            "comparison_type": "side_by_side",
        }

    # Task Selection Queries
    @staticmethod
    def task_selection_accuracy(
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get task selection accuracy metrics.

        Returns:
            Query configuration for selection accuracy
        """
        return {
            "query_type": "task_selection_accuracy",
            "time_range_hours": time_range_hours,
            "metrics": [
                "constraint_satisfaction_rate",
                "optimal_selection_rate",
                "alternative_quality_score",
            ],
            "visualization": "metrics_card",
        }

    @staticmethod
    def llm_vs_deterministic_selection(
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Compare LLM and deterministic task selection.

        Returns:
            Query configuration for selector comparison
        """
        return {
            "query_type": "selector_comparison",
            "selectors": ["llm_do_selector", "deterministic_selector"],
            "time_range_hours": time_range_hours,
            "metrics": [
                "success_rate",
                "avg_latency",
                "constraint_satisfaction",
                "user_satisfaction",
            ],
            "visualization": "comparison_table",
        }

    @staticmethod
    def constraint_violations_by_type(
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get breakdown of constraint violations.

        Returns:
            Query configuration for constraint violations
        """
        return {
            "query_type": "constraint_violations",
            "group_by": "constraint_type",
            "time_range_hours": time_range_hours,
            "metric": "violation_count",
            "include_severity": True,
            "visualization": "stacked_bar_chart",
        }

    # User Engagement Queries
    @staticmethod
    def daily_active_users(
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get daily active users trend.

        Args:
            time_range_days: Days to look back

        Returns:
            Query configuration for DAU trend
        """
        return {
            "query_type": "daily_active_users",
            "time_range_days": time_range_days,
            "metric": "unique_user_count",
            "bucket": "day",
            "visualization": "area_chart",
        }

    @staticmethod
    def user_retention_cohort(
        signup_date_start: Optional[str] = None,
        signup_date_end: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get user retention by cohort.

        Args:
            signup_date_start: Start date for cohorts
            signup_date_end: End date for cohorts

        Returns:
            Query configuration for retention cohort
        """
        return {
            "query_type": "retention_cohort",
            "signup_date_range": {
                "start": signup_date_start or (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
                "end": signup_date_end or datetime.now(timezone.utc).isoformat(),
            },
            "retention_days": [1, 7, 14, 30, 60],
            "visualization": "cohort_table",
        }

    @staticmethod
    def check_in_engagement(
        time_range_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get check-in engagement metrics.

        Returns:
            Query configuration for check-in engagement
        """
        return {
            "query_type": "check_in_engagement",
            "time_range_days": time_range_days,
            "metrics": [
                "total_check_ins",
                "check_in_rate",
                "avg_check_in_quality_score",
                "users_with_check_ins",
            ],
            "visualization": "metrics_card",
        }

    @staticmethod
    def task_completion_funnel(
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get task completion funnel.

        Returns:
            Query configuration for completion funnel
        """
        return {
            "query_type": "task_completion_funnel",
            "time_range_days": time_range_days,
            "stages": [
                "task_recommended",
                "task_viewed",
                "task_started",
                "task_completed",
            ],
            "visualization": "funnel_chart",
        }

    # Quality Evaluation Queries
    @staticmethod
    def hallucination_rate(
        agent_name: Optional[str] = None,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get hallucination detection rate.

        Args:
            agent_name: Specific agent (None for all)
            time_range_hours: Hours to look back

        Returns:
            Query configuration for hallucination rate
        """
        return {
            "query_type": "hallucination_rate",
            "agent_name": agent_name,
            "time_range_hours": time_range_hours,
            "metric": "hallucination_score",
            "threshold": 0.5,
            "visualization": "gauge",
        }

    @staticmethod
    def motivation_message_quality(
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get motivation message quality scores.

        Returns:
            Query configuration for motivation quality
        """
        return {
            "query_type": "motivation_quality",
            "time_range_hours": time_range_hours,
            "dimensions": [
                "empathy_score",
                "actionability_score",
                "personalization_score",
                "tone_score",
                "relevance_score",
            ],
            "visualization": "radar_chart",
        }

    @staticmethod
    def stuck_detection_accuracy(
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get stuck detection accuracy metrics.

        Returns:
            Query configuration for stuck detection
        """
        return {
            "query_type": "stuck_detection_accuracy",
            "time_range_hours": time_range_hours,
            "metrics": [
                "true_positive_rate",
                "false_positive_rate",
                "intervention_success_rate",
                "avg_intervention_quality",
            ],
            "visualization": "metrics_card",
        }

    # Dashboard Templates
    @staticmethod
    def dashboard_agent_health() -> Dict[str, Any]:
        """Get complete agent health dashboard configuration."""
        return {
            "name": "Agent Health Dashboard",
            "refresh_interval_seconds": 60,
            "panels": [
                {
                    "title": "Overall Success Rate",
                    "query": OpikQueries.agent_success_rate(),
                    "size": "large",
                },
                {
                    "title": "Agent Latency Trends",
                    "query": OpikQueries.agent_latency_trend("all_agents"),
                    "size": "large",
                },
                {
                    "title": "Error Distribution",
                    "query": OpikQueries.agent_error_distribution(),
                    "size": "medium",
                },
                {
                    "title": "Agent Comparison",
                    "query": OpikQueries.agent_comparison([
                        "llm_do_selector",
                        "llm_coach",
                        "stuck_pattern_agent",
                        "motivation_agent",
                    ]),
                    "size": "large",
                },
            ],
        }

    @staticmethod
    def dashboard_task_selection() -> Dict[str, Any]:
        """Get task selection performance dashboard."""
        return {
            "name": "Task Selection Dashboard",
            "refresh_interval_seconds": 60,
            "panels": [
                {
                    "title": "Selection Accuracy",
                    "query": OpikQueries.task_selection_accuracy(),
                    "size": "large",
                },
                {
                    "title": "LLM vs Deterministic",
                    "query": OpikQueries.llm_vs_deterministic_selection(),
                    "size": "large",
                },
                {
                    "title": "Constraint Violations",
                    "query": OpikQueries.constraint_violations_by_type(),
                    "size": "medium",
                },
            ],
        }

    @staticmethod
    def dashboard_user_engagement() -> Dict[str, Any]:
        """Get user engagement dashboard."""
        return {
            "name": "User Engagement Dashboard",
            "refresh_interval_seconds": 300,
            "panels": [
                {
                    "title": "Daily Active Users",
                    "query": OpikQueries.daily_active_users(),
                    "size": "large",
                },
                {
                    "title": "Check-in Engagement",
                    "query": OpikQueries.check_in_engagement(),
                    "size": "medium",
                },
                {
                    "title": "Task Completion Funnel",
                    "query": OpikQueries.task_completion_funnel(),
                    "size": "large",
                },
                {
                    "title": "User Retention",
                    "query": OpikQueries.user_retention_cohort(),
                    "size": "large",
                },
            ],
        }

    @staticmethod
    def dashboard_quality_metrics() -> Dict[str, Any]:
        """Get quality metrics dashboard."""
        return {
            "name": "Quality Metrics Dashboard",
            "refresh_interval_seconds": 60,
            "panels": [
                {
                    "title": "Hallucination Rate",
                    "query": OpikQueries.hallucination_rate(),
                    "size": "medium",
                },
                {
                    "title": "Motivation Quality",
                    "query": OpikQueries.motivation_message_quality(),
                    "size": "large",
                },
                {
                    "title": "Stuck Detection",
                    "query": OpikQueries.stuck_detection_accuracy(),
                    "size": "medium",
                },
            ],
        }
