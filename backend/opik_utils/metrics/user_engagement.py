"""
User engagement metrics for Opik observability.

Tracks app opens, check-in rate, task completion, and user retention.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class UserEngagementMetrics:
    """
    Tracks user engagement patterns and health.

    Metrics:
    - app_opens: Total application opens per user
    - check_in_rate: % of sessions with check-ins
    - task_completion_rate: % of started tasks completed
    - daily_active_users: Users active today
    - retention: New user retention after N days
    - session_duration: Average time in app per session
    """

    def __init__(self):
        """Initialize user engagement metrics."""
        self.metrics = {
            "total_app_opens": 0,
            "total_check_ins": 0,
            "total_tasks_started": 0,
            "total_tasks_completed": 0,
            "user_sessions": {},  # user_id -> session list
            "daily_active_users": set(),  # users active today
        }
        self.created_at = datetime.now(timezone.utc).isoformat()

    def record_app_open(
        self,
        user_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an app open event.

        Args:
            user_id: User ID
            session_id: Session ID
            metadata: Additional metadata
        """
        self.metrics["total_app_opens"] += 1
        self.metrics["daily_active_users"].add(user_id)

        if user_id not in self.metrics["user_sessions"]:
            self.metrics["user_sessions"][user_id] = []

        session = {
            "session_id": session_id,
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "check_in": False,
            "tasks_started": 0,
            "tasks_completed": 0,
            "metadata": metadata or {},
        }
        self.metrics["user_sessions"][user_id].append(session)

        # Keep only recent sessions (last 1000)
        if len(self.metrics["user_sessions"][user_id]) > 1000:
            self.metrics["user_sessions"][user_id] = self.metrics["user_sessions"][user_id][-1000:]

    def record_check_in(self, user_id: str, session_id: str) -> None:
        """
        Record a check-in event.

        Args:
            user_id: User ID
            session_id: Session ID
        """
        self.metrics["total_check_ins"] += 1

        if user_id in self.metrics["user_sessions"]:
            for session in self.metrics["user_sessions"][user_id]:
                if session["session_id"] == session_id:
                    session["check_in"] = True
                    break

    def record_task_action(
        self,
        user_id: str,
        session_id: str,
        action: str,  # "start" or "complete"
    ) -> None:
        """
        Record a task action (start or complete).

        Args:
            user_id: User ID
            session_id: Session ID
            action: "start" or "complete"
        """
        if action == "start":
            self.metrics["total_tasks_started"] += 1
            if user_id in self.metrics["user_sessions"]:
                for session in self.metrics["user_sessions"][user_id]:
                    if session["session_id"] == session_id:
                        session["tasks_started"] += 1
                        break

        elif action == "complete":
            self.metrics["total_tasks_completed"] += 1
            if user_id in self.metrics["user_sessions"]:
                for session in self.metrics["user_sessions"][user_id]:
                    if session["session_id"] == session_id:
                        session["tasks_completed"] += 1
                        break

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics summary.

        Returns:
            Dictionary with aggregated metrics
        """
        total_opens = self.metrics["total_app_opens"]
        total_checkins = self.metrics["total_check_ins"]
        total_started = self.metrics["total_tasks_started"]
        total_completed = self.metrics["total_tasks_completed"]

        return {
            "total_app_opens": total_opens,
            "total_check_ins": total_checkins,
            "check_in_rate": total_checkins / total_opens if total_opens > 0 else 0.0,
            "total_tasks_started": total_started,
            "total_tasks_completed": total_completed,
            "task_completion_rate": total_completed / total_started if total_started > 0 else 0.0,
            "unique_users": len(self.metrics["user_sessions"]),
            "daily_active_users": len(self.metrics["daily_active_users"]),
            "avg_tasks_per_session": total_started / total_opens if total_opens > 0 else 0.0,
            "created_at": self.created_at,
        }

    def get_recent_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get engagement metrics for recent period.

        Args:
            hours: Look back this many hours

        Returns:
            Recent engagement metrics
        """
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        recent_opens = 0
        recent_checkins = 0
        recent_started = 0
        recent_completed = 0
        recent_users = set()

        for user_id, sessions in self.metrics["user_sessions"].items():
            for session in sessions:
                if session["opened_at"] >= cutoff_time:
                    recent_opens += 1
                    recent_users.add(user_id)
                    if session["check_in"]:
                        recent_checkins += 1
                    recent_started += session["tasks_started"]
                    recent_completed += session["tasks_completed"]

        return {
            "period_hours": hours,
            "recent_app_opens": recent_opens,
            "recent_check_in_rate": recent_checkins / recent_opens if recent_opens > 0 else 0.0,
            "recent_active_users": len(recent_users),
            "recent_task_completion_rate": recent_completed / recent_started if recent_started > 0 else 0.0,
        }

    def get_user_engagement(self, user_id: str) -> Dict[str, Any]:
        """
        Get engagement metrics for a specific user.

        Args:
            user_id: User ID

        Returns:
            User-specific engagement metrics
        """
        if user_id not in self.metrics["user_sessions"]:
            return {
                "user_id": user_id,
                "message": "No sessions for this user",
            }

        sessions = self.metrics["user_sessions"][user_id]
        if not sessions:
            return {
                "user_id": user_id,
                "message": "No sessions for this user",
            }

        total_opens = len(sessions)
        check_ins = sum(1 for s in sessions if s["check_in"])
        total_started = sum(s["tasks_started"] for s in sessions)
        total_completed = sum(s["tasks_completed"] for s in sessions)

        # Calculate session duration if available
        session_durations = []
        for session in sessions:
            if "closed_at" in session["metadata"]:
                opened = datetime.fromisoformat(session["opened_at"])
                closed = datetime.fromisoformat(session["metadata"]["closed_at"])
                duration = (closed - opened).total_seconds() / 60  # minutes
                session_durations.append(duration)

        avg_duration = sum(session_durations) / len(session_durations) if session_durations else 0

        return {
            "user_id": user_id,
            "session_count": total_opens,
            "check_in_rate": check_ins / total_opens if total_opens > 0 else 0.0,
            "task_completion_rate": total_completed / total_started if total_started > 0 else 0.0,
            "total_tasks_completed": total_completed,
            "avg_session_duration_minutes": avg_duration,
            "last_session": sessions[-1]["opened_at"] if sessions else None,
            "engagement_level": self._calculate_engagement_level(
                total_opens, check_ins, total_completed
            ),
        }

    def get_cohort_metrics(self, days_since_signup: int) -> Dict[str, Any]:
        """
        Get retention metrics for users who signed up N days ago.

        Args:
            days_since_signup: Days since user signup

        Returns:
            Cohort retention metrics
        """
        # This would require signup date tracking in the session metadata
        # For now, return placeholder
        return {
            "days_since_signup": days_since_signup,
            "message": "Cohort analysis requires signup date tracking",
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "total_app_opens": 0,
            "total_check_ins": 0,
            "total_tasks_started": 0,
            "total_tasks_completed": 0,
            "user_sessions": {},
            "daily_active_users": set(),
        }
        self.created_at = datetime.now(timezone.utc).isoformat()

    def _calculate_engagement_level(
        self,
        opens: int,
        check_ins: int,
        completions: int
    ) -> str:
        """
        Calculate user engagement level.

        Returns:
            "high", "medium", "low", or "inactive"
        """
        check_in_rate = check_ins / opens if opens > 0 else 0

        if opens < 1:
            return "inactive"
        elif opens < 3 and check_in_rate < 0.5:
            return "low"
        elif opens < 5 or check_in_rate < 0.5 or completions == 0:
            return "medium"
        else:
            return "high"


# Global instance
_engagement_metrics = UserEngagementMetrics()


def get_engagement_metrics() -> UserEngagementMetrics:
    """Get the global engagement metrics instance."""
    return _engagement_metrics


def record_app_open(
    user_id: str,
    session_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Record app open event globally."""
    _engagement_metrics.record_app_open(user_id, session_id, metadata)


def record_check_in(user_id: str, session_id: str) -> None:
    """Record check-in event globally."""
    _engagement_metrics.record_check_in(user_id, session_id)


def record_task_action(user_id: str, session_id: str, action: str) -> None:
    """Record task action globally."""
    _engagement_metrics.record_task_action(user_id, session_id, action)
