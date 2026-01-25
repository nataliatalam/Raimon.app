"""
Error tracking and alerting for Opik observability
Monitors critical metrics and triggers alerts
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from opik_utils.client import get_opik_client
import logging

logger = logging.getLogger(__name__)


class AlertConfig:
    """Alert threshold configuration"""

    # Error rate thresholds
    ERROR_RATE_WARNING = 0.05  # 5%
    ERROR_RATE_CRITICAL = 0.10  # 10%

    # Latency thresholds (milliseconds)
    LATENCY_P95_WARNING = 2000  # 2 seconds
    LATENCY_P95_CRITICAL = 5000  # 5 seconds

    # Cost thresholds (USD per user per day)
    COST_PER_USER_WARNING = 0.05  # $0.05
    COST_PER_USER_CRITICAL = 0.10  # $0.10

    # Hallucination thresholds
    HALLUCINATION_RATE_WARNING = 0.05  # 5%
    HALLUCINATION_RATE_CRITICAL = 0.10  # 10%

    # Stuck detection recall threshold
    STUCK_RECALL_WARNING = 0.6  # 60%
    STUCK_RECALL_CRITICAL = 0.4  # 40%


class AlertManager:
    """
    Monitors metrics and triggers alerts

    Usage:
        alert_manager = AlertManager()
        alert_manager.check_error_rate(agent_name="priority_engine")
        alert_manager.check_latency(agent_name="priority_engine")
        alert_manager.check_cost_per_user(user_id="user_123")
    """

    def __init__(self):
        self.opik_client = get_opik_client()
        self.config = AlertConfig()
        self.alert_history: List[Dict[str, Any]] = []

    def check_error_rate(
        self,
        agent_name: str,
        time_window_minutes: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        Check error rate for an agent

        Args:
            agent_name: Name of the agent to monitor
            time_window_minutes: Time window for analysis

        Returns:
            Alert dict if threshold exceeded, None otherwise
        """
        try:
            # Query Opik for traces in time window
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes)

            # This is a placeholder - adjust based on actual Opik API
            # traces = self.opik_client.opik.get_traces(
            #     agent=agent_name,
            #     start_time=start_time,
            #     end_time=end_time
            # )

            # For now, simulate calculation
            total_calls = 100  # Replace with actual query
            failed_calls = 8   # Replace with actual query

            error_rate = failed_calls / total_calls if total_calls > 0 else 0

            # Check thresholds
            if error_rate >= self.config.ERROR_RATE_CRITICAL:
                return self._create_alert(
                    severity="critical",
                    metric="error_rate",
                    agent=agent_name,
                    value=error_rate,
                    threshold=self.config.ERROR_RATE_CRITICAL,
                    message=f"CRITICAL: Error rate {error_rate:.1%} exceeds {self.config.ERROR_RATE_CRITICAL:.1%}"
                )
            elif error_rate >= self.config.ERROR_RATE_WARNING:
                return self._create_alert(
                    severity="warning",
                    metric="error_rate",
                    agent=agent_name,
                    value=error_rate,
                    threshold=self.config.ERROR_RATE_WARNING,
                    message=f"WARNING: Error rate {error_rate:.1%} exceeds {self.config.ERROR_RATE_WARNING:.1%}"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking error rate: {e}")
            return None

    def check_latency(
        self,
        agent_name: str,
        time_window_minutes: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        Check P95 latency for an agent

        Args:
            agent_name: Name of the agent to monitor
            time_window_minutes: Time window for analysis

        Returns:
            Alert dict if threshold exceeded, None otherwise
        """
        try:
            # Query Opik for latency metrics
            # This is a placeholder - adjust based on actual Opik API

            # Simulate P95 calculation
            p95_latency_ms = 2500  # Replace with actual query

            # Check thresholds
            if p95_latency_ms >= self.config.LATENCY_P95_CRITICAL:
                return self._create_alert(
                    severity="critical",
                    metric="p95_latency",
                    agent=agent_name,
                    value=p95_latency_ms,
                    threshold=self.config.LATENCY_P95_CRITICAL,
                    message=f"CRITICAL: P95 latency {p95_latency_ms}ms exceeds {self.config.LATENCY_P95_CRITICAL}ms"
                )
            elif p95_latency_ms >= self.config.LATENCY_P95_WARNING:
                return self._create_alert(
                    severity="warning",
                    metric="p95_latency",
                    agent=agent_name,
                    value=p95_latency_ms,
                    threshold=self.config.LATENCY_P95_WARNING,
                    message=f"WARNING: P95 latency {p95_latency_ms}ms exceeds {self.config.LATENCY_P95_WARNING}ms"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking latency: {e}")
            return None

    def check_cost_per_user(
        self,
        user_id: str,
        date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check cost per user for a specific date

        Args:
            user_id: User ID to monitor
            date: Date in ISO format (defaults to today)

        Returns:
            Alert dict if threshold exceeded, None otherwise
        """
        try:
            if date is None:
                date = datetime.utcnow().date().isoformat()

            # Query Opik for cost metrics
            # This is a placeholder - adjust based on actual Opik API

            # Simulate cost calculation
            daily_cost = 0.08  # Replace with actual query

            # Check thresholds
            if daily_cost >= self.config.COST_PER_USER_CRITICAL:
                return self._create_alert(
                    severity="critical",
                    metric="cost_per_user",
                    user_id=user_id,
                    value=daily_cost,
                    threshold=self.config.COST_PER_USER_CRITICAL,
                    message=f"CRITICAL: Daily cost ${daily_cost:.3f} exceeds ${self.config.COST_PER_USER_CRITICAL:.3f}"
                )
            elif daily_cost >= self.config.COST_PER_USER_WARNING:
                return self._create_alert(
                    severity="warning",
                    metric="cost_per_user",
                    user_id=user_id,
                    value=daily_cost,
                    threshold=self.config.COST_PER_USER_WARNING,
                    message=f"WARNING: Daily cost ${daily_cost:.3f} exceeds ${self.config.COST_PER_USER_WARNING:.3f}"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking cost: {e}")
            return None

    def check_hallucination_rate(
        self,
        agent_name: str,
        time_window_minutes: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        Check hallucination rate for an agent

        Args:
            agent_name: Name of the agent to monitor
            time_window_minutes: Time window for analysis

        Returns:
            Alert dict if threshold exceeded, None otherwise
        """
        try:
            # Query Opik for hallucination evaluation results
            # This is a placeholder - adjust based on actual Opik API

            # Simulate hallucination rate
            hallucination_rate = 0.07  # Replace with actual query

            # Check thresholds
            if hallucination_rate >= self.config.HALLUCINATION_RATE_CRITICAL:
                return self._create_alert(
                    severity="critical",
                    metric="hallucination_rate",
                    agent=agent_name,
                    value=hallucination_rate,
                    threshold=self.config.HALLUCINATION_RATE_CRITICAL,
                    message=f"CRITICAL: Hallucination rate {hallucination_rate:.1%} exceeds {self.config.HALLUCINATION_RATE_CRITICAL:.1%}"
                )
            elif hallucination_rate >= self.config.HALLUCINATION_RATE_WARNING:
                return self._create_alert(
                    severity="warning",
                    metric="hallucination_rate",
                    agent=agent_name,
                    value=hallucination_rate,
                    threshold=self.config.HALLUCINATION_RATE_WARNING,
                    message=f"WARNING: Hallucination rate {hallucination_rate:.1%} exceeds {self.config.HALLUCINATION_RATE_WARNING:.1%}"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking hallucination rate: {e}")
            return None

    def _create_alert(
        self,
        severity: str,
        metric: str,
        value: float,
        threshold: float,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create and log an alert

        Args:
            severity: "warning" or "critical"
            metric: Metric name
            value: Current value
            threshold: Threshold that was exceeded
            message: Alert message
            **kwargs: Additional metadata

        Returns:
            Alert dictionary
        """
        alert = {
            "severity": severity,
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }

        # Log alert
        if severity == "critical":
            logger.error(f"🚨 {message}")
        else:
            logger.warning(f"⚠️ {message}")

        # Store in history
        self.alert_history.append(alert)

        # Log to Opik
        try:
            self.opik_client.opik.log_metric(
                metric_name=f"alert_{metric}",
                value=1,
                metadata=alert
            )
        except Exception as e:
            logger.error(f"Failed to log alert to Opik: {e}")

        return alert

    def get_alert_history(
        self,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts

        Args:
            severity: Filter by severity ("warning" or "critical")
            limit: Maximum number of alerts to return

        Returns:
            List of alert dictionaries
        """
        alerts = self.alert_history

        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]

        return alerts[-limit:]

    def run_all_checks(
        self,
        agents: List[str],
        user_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run all alert checks

        Args:
            agents: List of agent names to check
            user_ids: Optional list of user IDs to check costs for

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []

        # Check each agent
        for agent in agents:
            # Error rate check
            alert = self.check_error_rate(agent)
            if alert:
                triggered_alerts.append(alert)

            # Latency check
            alert = self.check_latency(agent)
            if alert:
                triggered_alerts.append(alert)

            # Hallucination rate check
            alert = self.check_hallucination_rate(agent)
            if alert:
                triggered_alerts.append(alert)

        # Check user costs if provided
        if user_ids:
            for user_id in user_ids:
                alert = self.check_cost_per_user(user_id)
                if alert:
                    triggered_alerts.append(alert)

        return triggered_alerts


# Global instance
alert_manager = AlertManager()
