"""
Stuck Pattern Agent - Stuck detection with optional LLM microtasks.

Functionality: Detect when user is stuck, suggest microtasks to get unstuck.

Inputs: StuckDetectionRequest { user_id, current_session: WorkSession, time_stuck: int }

Outputs: StuckAnalysis { is_stuck: bool, stuck_reason: str?, microtasks: List[Microtask] }

Memory:
- reads: work_sessions (patterns), active_do, stuck_episodes
- writes: stuck_episodes (if stuck detected)

LLM: Optional (for microtask generation, bounded copy)

Critical guarantees:
- microtasks are small, actionable steps
- never suggests abandoning work
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from agent_mvp.contracts import (
    StuckDetectionRequest,
    StuckAnalysis,
    Microtask,
    WorkSession,
)
from agent_mvp.storage import get_session_patterns, get_active_do, save_stuck_episode, get_recent_stuck_episodes
from agent_mvp.gemini_client import GeminiClient
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="stuck_pattern_agent")
def detect_stuck_patterns(
    request: StuckDetectionRequest,
) -> StuckAnalysis:
    """
    Detect if user is stuck and suggest microtasks.

    Args:
        request: Stuck detection request

    Returns:
        Stuck analysis with microtasks if stuck
    """
    logger.info(f"🕳️ Detecting stuck patterns for user {request.user_id}")

    analysis = StuckAnalysis()

    # Check if user is stuck
    analysis.is_stuck = _is_user_stuck(request)

    if analysis.is_stuck:
        # Determine stuck reason
        analysis.stuck_reason = _determine_stuck_reason(request)

        # Generate microtasks
        analysis.microtasks = _generate_microtasks(request)

        # Save stuck episode
        _save_stuck_episode(request, analysis.stuck_reason)

        logger.info(f"⚠️ User stuck: {analysis.stuck_reason}")
    else:
        logger.info("✅ User not stuck")

    return analysis


def _is_user_stuck(request: StuckDetectionRequest) -> bool:
    """Determine if user is stuck based on time and patterns."""
    time_stuck = request.time_stuck
    session = request.current_session

    # Time-based threshold (15+ minutes without progress)
    if time_stuck >= 15:
        return True

    # Pattern-based detection
    patterns = get_session_patterns(request.user_id, days=7)

    # Check for repeated short sessions on same task
    recent_sessions = patterns.get("recent_sessions", [])
    same_task_sessions = [s for s in recent_sessions if s.get("task_id") == session.task_id]

    if len(same_task_sessions) >= 3:
        avg_duration = sum(s.get("duration_minutes", 0) for s in same_task_sessions) / len(same_task_sessions)
        if avg_duration < 10:  # Multiple short attempts
            return True

    # Check for frequent stuck episodes
    recent_stuck = get_recent_stuck_episodes(request.user_id, hours=24)
    if len(recent_stuck) >= 2:  # Multiple stuck episodes in 24h
        return True

    return False


def _determine_stuck_reason(request: StuckDetectionRequest) -> str:
    """Determine the reason user is stuck."""
    time_stuck = request.time_stuck
    session = request.current_session

    if time_stuck >= 30:
        return "extended_time_no_progress"
    elif time_stuck >= 15:
        return "moderate_time_no_progress"
    else:
        # Check task complexity vs time
        estimated = session.estimated_duration or 60
        if time_stuck > estimated * 0.8:  # Stuck near end of estimated time
            return "nearing_time_limit"
        else:
            return "early_stuck_pattern"


def _generate_microtasks(request: StuckDetectionRequest) -> List[Microtask]:
    """Generate small, actionable microtasks to get unstuck."""
    session = request.current_session
    task_title = session.task_title or "current task"

    # Base microtasks by stuck reason
    reason = _determine_stuck_reason(request)

    base_microtasks = {
        "extended_time_no_progress": [
            f"Take a 2-minute break and note one small next step for '{task_title}'",
            f"Write down exactly what feels stuck about '{task_title}'",
            f"Set a 5-minute timer and work on just the easiest part of '{task_title}'",
        ],
        "moderate_time_no_progress": [
            f"Break '{task_title}' into 3 smaller steps and pick the easiest one",
            f"Talk through '{task_title}' out loud for 1 minute",
            f"Change your environment for 2 minutes (stand up, walk around)",
        ],
        "nearing_time_limit": [
            f"Focus on completing just 20% more of '{task_title}'",
            f"Ask: what's the minimum viable progress I can make on '{task_title}'?",
            f"Set a 3-minute timer and push through one small hurdle in '{task_title}'",
        ],
        "early_stuck_pattern": [
            f"Clarify the very first step needed for '{task_title}'",
            f"Gather any information you need before starting '{task_title}'",
            f"Write a quick plan for the next 10 minutes of work on '{task_title}'",
        ],
    }

    microtasks = base_microtasks.get(reason, base_microtasks["moderate_time_no_progress"])

    # Try LLM enhancement if available
    enhanced = _enhance_microtasks_with_llm(session, microtasks)
    if enhanced:
        microtasks = enhanced[:5]  # Limit to 5

    # Convert to Microtask objects
    return [
        Microtask(
            description=task,
            estimated_minutes=2,  # All microtasks are 2 minutes
            category="unstuck_help",
        )
        for task in microtasks
    ]


def _enhance_microtasks_with_llm(session: WorkSession, base_tasks: List[str]) -> Optional[List[str]]:
    """Use LLM to generate more specific microtasks."""
    try:
        client = GeminiClient()

        prompt = f"""
        A user is stuck on this task: "{session.task_title or 'Unknown task'}"
        They have been working for {session.actual_duration_minutes or 0} minutes.

        Generate 3 specific, actionable microtasks (1-2 minutes each) to help them get unstuck.
        Make them concrete and immediately actionable.

        Base these on common getting-unstuck strategies but tailor to the task if possible.

        Return as JSON array of strings, each under 100 characters.
        """

        response = client.generate_json_response(prompt, max_tokens=200)

        if isinstance(response, list) and len(response) >= 3:
            # Validate and bound the suggestions
            valid_tasks = []
            for task in response[:3]:
                if isinstance(task, str) and len(task) <= 100:
                    valid_tasks.append(task)
            return valid_tasks

    except Exception as e:
        logger.warning(f"⚠️ LLM microtask enhancement failed: {str(e)}")

    return None


def _save_stuck_episode(request: StuckDetectionRequest, reason: str) -> None:
    """Save stuck episode for pattern analysis."""
    try:
        episode = {
            "user_id": request.user_id,
            "task_id": request.current_session.task_id,
            "session_id": request.current_session.id,
            "stuck_reason": reason,
            "time_stuck": request.time_stuck,
            "detected_at": datetime.utcnow(),
        }
        save_stuck_episode(episode)
        logger.info(f"💾 Saved stuck episode for user {request.user_id}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to save stuck episode: {str(e)}")