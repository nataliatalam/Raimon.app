"""
Priority Engine Agent - Deterministic priority scoring.

Functionality: Score task candidates by multiple priority factors (deadline, dependencies, user preferences).

Inputs: PriorityCandidates { candidates: List[TaskCandidate], user_profile: UserProfileAnalysis }

Outputs: PriorityScoredCandidates { scored_candidates: List[TaskCandidateWithScore] }

Memory:
- reads: ai_learning_data (user_profile), task dependencies
- writes: NONE (pure function)

LLM: NO (deterministic scoring algorithm)

Critical guarantees:
- deterministic scoring based on fixed algorithm
- never modifies task data
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from models.contracts import (
    PriorityCandidates,
    PriorityScoredCandidates,
    TaskCandidateWithScore,
    UserProfileAnalysis,
)
from services.storage_service import get_task_dependencies
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="priority_engine_agent")
def score_task_priorities(
    request: PriorityCandidates,
) -> PriorityScoredCandidates:
    """
    Score task candidates by priority factors.

    Args:
        request: Candidates and user profile

    Returns:
        Scored candidates with priority scores
    """
    logger.info(f"🎯 Scoring {len(request.candidates)} task candidates")

    scored = []

    for candidate in request.candidates:
        score = _calculate_priority_score(candidate, request.user_profile)
        scored.append(TaskCandidateWithScore(
            task=candidate,
            priority_score=score,
            score_breakdown=_get_score_breakdown(candidate, request.user_profile),
        ))

    # Sort by score descending
    scored.sort(key=lambda x: x.priority_score, reverse=True)

    logger.info(f"✅ Priority scoring complete, top score: {scored[0].priority_score if scored else 0}")
    return PriorityScoredCandidates(scored_candidates=scored)


def _calculate_priority_score(
    candidate: Dict[str, Any],
    user_profile: UserProfileAnalysis,
) -> float:
    """Calculate composite priority score (0-100)."""
    score = 0.0

    # Base priority weight (40%)
    base_priority = _get_base_priority_weight(candidate.get("priority", "medium"))
    score += base_priority * 0.4

    # Deadline proximity (30%)
    deadline_score = _calculate_deadline_score(candidate)
    score += deadline_score * 0.3

    # Dependencies (15%)
    dependency_score = _calculate_dependency_score(candidate)
    score += dependency_score * 0.15

    # User preference alignment (15%)
    preference_score = _calculate_preference_score(candidate, user_profile)
    score += preference_score * 0.15

    return min(100.0, max(0.0, score))


def _get_base_priority_weight(priority: str) -> float:
    """Convert priority string to numeric weight."""
    weights = {
        "urgent": 100.0,
        "high": 75.0,
        "medium": 50.0,
        "low": 25.0,
    }
    return weights.get(priority.lower(), 50.0)


def _calculate_deadline_score(candidate: Dict[str, Any]) -> float:
    """Score based on deadline proximity (higher = closer deadline)."""
    deadline = candidate.get("deadline")
    if not deadline:
        return 25.0  # Default for no deadline

    try:
        if isinstance(deadline, str):
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        else:
            deadline_dt = deadline

        now = datetime.now(timezone.utc)
        days_until = (deadline_dt - now).days

        if days_until < 0:
            return 100.0  # Overdue
        elif days_until == 0:
            return 90.0   # Due today
        elif days_until <= 1:
            return 80.0   # Due tomorrow
        elif days_until <= 3:
            return 60.0   # Due this week
        elif days_until <= 7:
            return 40.0   # Due next week
        else:
            return 10.0   # Far future
    except:
        return 25.0


def _calculate_dependency_score(candidate: Dict[str, Any]) -> float:
    """Score based on blocking other tasks."""
    task_id = candidate.get("id")
    if not task_id:
        return 50.0

    try:
        dependencies = get_task_dependencies(task_id)
        blocked_count = len(dependencies.get("blocked_by", []))

        if blocked_count == 0:
            return 100.0  # Not blocking anyone
        elif blocked_count <= 2:
            return 75.0   # Blocking few tasks
        elif blocked_count <= 5:
            return 50.0   # Blocking several tasks
        else:
            return 25.0   # Blocking many tasks
    except:
        return 50.0


def _calculate_preference_score(
    candidate: Dict[str, Any],
    user_profile: UserProfileAnalysis,
) -> float:
    """Score based on user preferences alignment."""
    if not user_profile or not user_profile.task_preferences:
        return 50.0

    score = 50.0  # Base

    # Tag preference alignment
    task_tags = set(candidate.get("tags", []))
    preferred_tags = set(user_profile.task_preferences.get("tag_preferences", {}).keys())

    if task_tags & preferred_tags:
        score += 20.0  # Tag match bonus

    # Duration preference alignment
    task_duration = candidate.get("estimated_duration", 60)
    preferred_duration = user_profile.task_preferences.get("preferred_duration", 60)

    duration_diff = abs(task_duration - preferred_duration)
    if duration_diff <= 15:
        score += 15.0  # Duration match bonus
    elif duration_diff <= 30:
        score += 7.5   # Close duration bonus

    # Priority distribution alignment
    task_priority = candidate.get("priority", "medium")
    priority_dist = user_profile.task_preferences.get("priority_distribution", {})
    total_completed = user_profile.task_preferences.get("total_completed", 1)

    if task_priority in priority_dist:
        priority_ratio = priority_dist[task_priority] / total_completed
        score += priority_ratio * 15.0  # Preference alignment bonus

    return min(100.0, score)


def _get_score_breakdown(
    candidate: Dict[str, Any],
    user_profile: UserProfileAnalysis,
) -> Dict[str, float]:
    """Get detailed score breakdown for transparency."""
    return {
        "base_priority": _get_base_priority_weight(candidate.get("priority", "medium")),
        "deadline_proximity": _calculate_deadline_score(candidate),
        "dependency_impact": _calculate_dependency_score(candidate),
        "preference_alignment": _calculate_preference_score(candidate, user_profile),
    }