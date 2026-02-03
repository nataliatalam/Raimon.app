"""
Time Learning Agent - Deterministic time pattern learning.

Functionality: Learn user's time patterns from work sessions to predict optimal work times.

Inputs: TimeLearningRequest { user_id, analysis_window_days: int }

Outputs: TimePatterns { peak_hours, optimal_durations, day_patterns, time_efficiency }

Memory:
- reads: work_sessions, daily_check_ins
- writes: ai_learning_data (agent_type=time_learning)

LLM: NO (deterministic pattern analysis)

Critical guarantees:
- never modifies session/check-in data
- patterns based on historical data only
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from agent_mvp.contracts import (
    TimeLearningRequest,
    TimePatterns,
)
from agent_mvp.storage import get_user_sessions, get_user_checkins, save_ai_learning
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="time_learning_agent")
def learn_time_patterns(
    request: TimeLearningRequest,
) -> TimePatterns:
    """
    Learn user's time patterns from historical data.

    Args:
        request: Time learning request

    Returns:
        Learned time patterns
    """
    logger.info(f"⏰ Learning time patterns for user {request.user_id}")

    # Get historical data
    sessions = get_user_sessions(request.user_id, days=request.analysis_window_days)
    checkins = get_user_checkins(request.user_id, days=request.analysis_window_days)

    patterns = TimePatterns()

    # Analyze peak hours
    patterns.peak_hours = _analyze_peak_hours(sessions)

    # Analyze optimal durations
    patterns.optimal_durations = _analyze_optimal_durations(sessions)

    # Analyze day patterns
    patterns.day_patterns = _analyze_day_patterns(sessions, checkins)

    # Calculate time efficiency
    patterns.time_efficiency = _calculate_time_efficiency(sessions)

    # Save patterns for reuse
    _save_time_patterns(request.user_id, patterns)

    logger.info(f"✅ Time patterns learned for user {request.user_id}")
    return patterns


def _analyze_peak_hours(sessions: List[Dict[str, Any]]) -> List[int]:
    """Analyze peak productive hours."""
    if not sessions:
        return [9, 10, 11]  # Default morning hours

    hour_counts = defaultdict(int)
    hour_productivity = defaultdict(float)

    for session in sessions:
        start_time = session.get("start_time")
        if not start_time:
            continue

        try:
            if isinstance(start_time, str):
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                dt = start_time

            hour = dt.hour
            duration = session.get("duration_minutes", 0)
            completed = 1 if session.get("completed_at") else 0

            hour_counts[hour] += 1
            hour_productivity[hour] += completed * duration
        except:
            continue

    # Calculate productivity score per hour
    hour_scores = {}
    for hour in hour_counts:
        if hour_counts[hour] >= 3:  # Need at least 3 sessions for reliability
            avg_productivity = hour_productivity[hour] / hour_counts[hour]
            hour_scores[hour] = avg_productivity

    # Return top 3 hours
    top_hours = sorted(hour_scores.items(), key=lambda x: x[1], reverse=True)
    return [hour for hour, _ in top_hours[:3]]


def _analyze_optimal_durations(sessions: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze optimal task durations by completion rate."""
    if not sessions:
        return {"short": 30, "medium": 60, "long": 90}

    duration_buckets = {
        "short": [],    # 0-45 min
        "medium": [],   # 45-90 min
        "long": [],     # 90+ min
    }

    for session in sessions:
        duration = session.get("duration_minutes", 0)
        completed = session.get("completed_at") is not None

        if duration <= 45:
            duration_buckets["short"].append(completed)
        elif duration <= 90:
            duration_buckets["medium"].append(completed)
        else:
            duration_buckets["long"].append(completed)

    # Calculate optimal durations based on completion rates
    optimal = {}
    for bucket, completions in duration_buckets.items():
        if completions:
            completion_rate = sum(completions) / len(completions)
            if bucket == "short":
                optimal[bucket] = int(30 * (0.8 + completion_rate * 0.4))  # 24-48 min
            elif bucket == "medium":
                optimal[bucket] = int(60 * (0.8 + completion_rate * 0.4))  # 48-96 min
            else:  # long
                optimal[bucket] = int(90 * (0.8 + completion_rate * 0.4))  # 72-144 min

    # Fill defaults if missing data
    optimal.setdefault("short", 30)
    optimal.setdefault("medium", 60)
    optimal.setdefault("long", 90)

    return optimal


def _analyze_day_patterns(
    sessions: List[Dict[str, Any]],
    checkins: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Analyze patterns by day of week."""
    day_stats = {}

    # Session patterns by day
    session_days = defaultdict(list)
    for session in sessions:
        start_time = session.get("start_time")
        if not start_time:
            continue
        try:
            if isinstance(start_time, str):
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                dt = start_time
            day = dt.weekday()  # 0=Monday, 6=Sunday
            session_days[day].append(session)
        except:
            continue

    # Check-in patterns by day
    checkin_days = defaultdict(list)
    for checkin in checkins:
        day = checkin.get("day_of_week", 0)
        checkin_days[day].append(checkin)

    # Calculate stats for each day
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for day_num, day_name in enumerate(day_names):
        day_sessions = session_days[day_num]
        day_checkins = checkin_days[day_num]

        if day_sessions:
            avg_duration = sum(s.get("duration_minutes", 0) for s in day_sessions) / len(day_sessions)
            completion_rate = sum(1 for s in day_sessions if s.get("completed_at")) / len(day_sessions)
        else:
            avg_duration = 0
            completion_rate = 0

        if day_checkins:
            avg_energy = sum(c.get("energy_level", 5) for c in day_checkins) / len(day_checkins)
        else:
            avg_energy = 5

        day_stats[day_name] = {
            "avg_session_duration": round(avg_duration, 1),
            "completion_rate": round(completion_rate, 2),
            "avg_energy": round(avg_energy, 1),
            "session_count": len(day_sessions),
        }

    return day_stats


def _calculate_time_efficiency(sessions: List[Dict[str, Any]]) -> float:
    """Calculate overall time efficiency score."""
    if not sessions:
        return 0.5  # Neutral efficiency

    total_planned = sum(s.get("duration_minutes", 0) for s in sessions)
    total_actual = sum(s.get("actual_duration_minutes", s.get("duration_minutes", 0)) for s in sessions)
    completed_count = sum(1 for s in sessions if s.get("completed_at"))

    if total_planned == 0:
        return 0.5

    # Efficiency = (completed/planned) * (planned/actual) - accounts for time overruns
    completion_ratio = completed_count / len(sessions)
    time_ratio = min(1.0, total_planned / total_actual) if total_actual > 0 else 1.0

    efficiency = completion_ratio * time_ratio
    return round(max(0.0, min(1.0, efficiency)), 2)


def _save_time_patterns(user_id: str, patterns: TimePatterns) -> None:
    """Save learned patterns to ai_learning_data."""
    try:
        save_ai_learning(
            user_id=user_id,
            agent_type="time_learning",
            data=patterns.model_dump(),
            expires_at=datetime.utcnow() + timedelta(days=14),  # Refresh bi-weekly
        )
        logger.info(f"💾 Saved time patterns for user {user_id}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to save time patterns: {str(e)}")