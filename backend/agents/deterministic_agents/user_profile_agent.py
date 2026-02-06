"""
User Profile Agent - Deterministic user preference learning.

Functionality: Learn stable user preferences from history (sessions/tasks/check-ins), store analysis for reuse.

Inputs: UserProfileAnalyzeRequest { include_tasks: bool, include_sessions: bool, include_patterns: bool }

Outputs: UserProfileAnalysis { analyzed_at, work_patterns, task_preferences, energy_patterns }

Memory:
- reads: work_sessions, tasks (completed), daily_check_ins
- writes: ai_learning_data (agent_type=user_profile), optional user_preferences

LLM: NO (deterministic only)

Critical guarantees:
- never writes task/project data
- never overwrites user_preferences without merge strategy
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from models.contracts import (
    UserProfileAnalyzeRequest,
    UserProfileAnalysis,
)
from services.storage_service import get_user_sessions, get_user_tasks, get_user_checkins, save_ai_learning
from opik import track
import logging

logger = logging.getLogger(__name__)


def _extract_start_hour(session: Dict[str, Any]) -> int:
    """Extract start hour from work session shape variants."""
    start_time = session.get("start_time")

    if isinstance(start_time, dict):
        hour = start_time.get("hour")
        if isinstance(hour, int) and 0 <= hour <= 23:
            return hour

    if isinstance(start_time, str):
        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            return dt.hour
        except Exception:
            pass

    return 9


@track(name="user_profile_agent")
def analyze_user_profile(
    user_id: str,
    request: UserProfileAnalyzeRequest,
) -> UserProfileAnalysis:
    """
    Analyze user profile from historical data.

    Args:
        user_id: User UUID
        request: Analysis request parameters

    Returns:
        UserProfileAnalysis with patterns and preferences
    """
    logger.info(f"📊 Analyzing profile for user {user_id}")

    analysis = UserProfileAnalysis()

    # Analyze work patterns
    if request.include_sessions:
        analysis.work_patterns = _analyze_work_patterns(user_id)

    # Analyze task preferences
    if request.include_tasks:
        analysis.task_preferences = _analyze_task_preferences(user_id)

    # Analyze energy patterns
    if request.include_patterns:
        analysis.energy_patterns = _analyze_energy_patterns(user_id)

    # Save analysis for reuse
    _save_profile_analysis(user_id, analysis)

    logger.info(f"✅ Profile analysis complete for user {user_id}")
    return analysis


def _analyze_work_patterns(user_id: str) -> Dict[str, Any]:
    """Analyze work session patterns."""
    sessions = get_user_sessions(user_id, days=90)

    if not sessions:
        return {"pattern": "insufficient_data"}

    # Calculate average session duration
    durations = [s.get("duration_minutes", 0) for s in sessions if s.get("duration_minutes")]
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Calculate completion rate
    completed = sum(1 for s in sessions if s.get("completed_at"))
    completion_rate = completed / len(sessions) if sessions else 0

    # Find peak hours (simplified)
    hours = [_extract_start_hour(s) for s in sessions]
    peak_hour = max(set(hours), key=hours.count) if hours else 9

    return {
        "avg_session_duration": round(avg_duration, 1),
        "completion_rate": round(completion_rate, 2),
        "peak_hour": peak_hour,
        "total_sessions": len(sessions),
    }


def _analyze_task_preferences(user_id: str) -> Dict[str, Any]:
    """Analyze task completion preferences."""
    tasks = get_user_tasks(user_id, completed_only=True, days=90)

    if not tasks:
        return {"preference": "insufficient_data"}

    # Count by priority
    priorities = {}
    for task in tasks:
        pri = task.get("priority", "medium")
        priorities[pri] = priorities.get(pri, 0) + 1

    # Count by tags
    tags = {}
    for task in tasks:
        task_tags = task.get("tags", [])
        for tag in task_tags:
            tags[tag] = tags.get(tag, 0) + 1

    # Preferred task duration
    durations = [t.get("estimated_duration", 60) for t in tasks if t.get("estimated_duration")]
    avg_duration = sum(durations) / len(durations) if durations else 60

    return {
        "priority_distribution": priorities,
        "tag_preferences": tags,
        "preferred_duration": round(avg_duration, 0),
        "total_completed": len(tasks),
    }


def _analyze_energy_patterns(user_id: str) -> Dict[str, Any]:
    """Analyze energy and check-in patterns."""
    checkins = get_user_checkins(user_id, days=90)

    if not checkins:
        return {"pattern": "insufficient_data"}

    # Average energy by day of week
    energy_by_day = {}
    for checkin in checkins:
        day = checkin.get("day_of_week", 0)
        energy = checkin.get("energy_level", 5)
        if day not in energy_by_day:
            energy_by_day[day] = []
        energy_by_day[day].append(energy)

    avg_energy_by_day = {
        day: round(sum(levels) / len(levels), 1)
        for day, levels in energy_by_day.items()
    }

    # Energy trend
    energies = [c.get("energy_level", 5) for c in checkins[-30:]]  # last 30
    energy_trend = "stable"
    if len(energies) >= 7:
        recent_avg = sum(energies[-7:]) / 7
        older_avg = sum(energies[:-7]) / len(energies[:-7]) if energies[:-7] else recent_avg
        if recent_avg > older_avg + 0.5:
            energy_trend = "improving"
        elif recent_avg < older_avg - 0.5:
            energy_trend = "declining"

    return {
        "avg_energy_by_day": avg_energy_by_day,
        "energy_trend": energy_trend,
        "total_checkins": len(checkins),
    }


def _save_profile_analysis(user_id: str, analysis: UserProfileAnalysis) -> None:
    """Save analysis to ai_learning_data."""
    try:
        save_ai_learning(
            user_id=user_id,
            agent_type="user_profile",
            data=analysis.model_dump(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),  # Refresh monthly
        )
        logger.info(f"💾 Saved profile analysis for user {user_id}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to save profile analysis: {str(e)}")
