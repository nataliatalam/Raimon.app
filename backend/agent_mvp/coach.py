"""
Coach - LLM coach with strict validation.

Functionality: Generate personalized coaching messages for task selection and progress.

Inputs: user_id, selected_task, context

Outputs: CoachingMessage { message: str, category: str }

Memory:
- reads: user_profile, gamification_state, recent_sessions
- writes: NONE (pure function)

LLM: YES (bounded copy generation with strict JSON validation)

Critical guarantees:
- messages are encouraging and actionable
- bounded length (max 300 chars)
- validated JSON output with fallbacks
"""

from typing import Dict, Any, Optional, List
from agent_mvp.contracts import (
    CoachingMessage,
)
from agent_mvp.storage import get_user_profile, get_gamification_state, get_recent_sessions
from agent_mvp.gemini_client import GeminiClient
from agent_mvp.validators import validate_coach_output, fallback_coach
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="coach")
def generate_coaching_message(
    user_id: str,
    selected_task: Dict[str, Any],
    context: str = "task_selection",
) -> CoachingMessage:
    """
    Generate personalized coaching message.

    Args:
        user_id: User UUID
        selected_task: Selected task details
        context: Context for coaching

    Returns:
        Coaching message
    """
    logger.info(f"🏆 Generating coaching for user {user_id}")

    # Gather context data
    user_profile = get_user_profile(user_id)
    gamification = get_gamification_state(user_id)
    recent_sessions = get_recent_sessions(user_id, hours=24)

    # Build coaching prompt
    prompt = _build_coach_prompt(selected_task, user_profile, gamification, recent_sessions, context)

    # Generate message with LLM
    try:
        client = GeminiClient()
        response = client.generate_json_response(prompt, max_tokens=200)

        # Validate response
        if response and validate_coach_output(response):
            message = response.get("message", "")
            category = response.get("category", "general")
        else:
            # Fallback
            message, category = fallback_coach(selected_task, context)

    except Exception as e:
        logger.warning(f"⚠️ LLM coaching failed: {str(e)}")
        message, category = fallback_coach(selected_task, context)

    # Ensure bounds
    if len(message) > 300:
        message = message[:297] + "..."

    coaching = CoachingMessage(
        message=message,
        category=category,
    )

    logger.info(f"✅ Coaching generated: {category}")
    return coaching


def _build_coach_prompt(
    task: Dict[str, Any],
    user_profile: Dict[str, Any],
    gamification: Dict[str, Any],
    recent_sessions: List[Dict[str, Any]],
    context: str,
) -> str:
    """Build coaching prompt for LLM."""
    task_title = task.get("title", "this task")
    task_priority = task.get("priority", "medium")
    estimated_duration = task.get("estimated_duration", 60)

    # User context
    streak = gamification.get("current_streak", 0) if gamification else 0
    level = gamification.get("level", 1) if gamification else 1
    recent_completed = sum(1 for s in recent_sessions if s.get("completed_at"))

    # Profile insights
    work_patterns = user_profile.get("work_patterns", {}) if user_profile else {}
    avg_session_duration = work_patterns.get("avg_session_duration", 60)

    prompt = f"""
    Generate a personalized, encouraging coaching message for a user about to start a task.

    Task: {task_title}
    Priority: {task_priority}
    Estimated duration: {estimated_duration} minutes
    Context: {context}

    User profile:
    - Current streak: {streak} days
    - Level: {level}
    - Recent completed sessions: {recent_completed}
    - Average session duration: {avg_session_duration} minutes

    Requirements:
    - Message must be encouraging and actionable
    - Under 250 characters
    - Personalized to their progress and task
    - Focus on starting strong and maintaining momentum
    - End with a specific, small first step

    Return JSON with "message" and "category" (motivation/strategy/focus/reminder).
    """

    return prompt