"""
Motivation Agent - Bounded motivation messages.

Functionality: Generate encouraging, personalized motivation messages.

Inputs: MotivationRequest { user_id, context: str, tone: str }

Outputs: MotivationResponse { message: str, category: str }

Memory:
- reads: gamification_state, work_sessions (recent), user_profile
- writes: NONE (pure function)

LLM: YES (bounded message generation)

Critical guarantees:
- messages are positive and encouraging
- bounded length (max 200 chars)
- never discouraging or guilt-inducing
"""

from typing import Dict, Any, Optional, List
from agent_mvp.contracts import (
    MotivationRequest,
    MotivationResponse,
)
from agent_mvp.storage import get_gamification_state, get_recent_sessions, get_user_profile
from agent_mvp.gemini_client import GeminiClient
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="motivation_agent")
def generate_motivation(
    request: MotivationRequest,
) -> MotivationResponse:
    """
    Generate bounded motivation message.

    Args:
        request: Motivation request

    Returns:
        Motivation response with bounded message
    """
    logger.info(f"💪 Generating motivation for user {request.user_id}")

    # Gather context data
    gamification = get_gamification_state(request.user_id)
    recent_sessions = get_recent_sessions(request.user_id, hours=24)
    user_profile = get_user_profile(request.user_id)

    # Generate base motivation data
    motivation_data = _gather_motivation_data(gamification, recent_sessions, user_profile, request.context)

    # Generate message with LLM
    message = _generate_motivation_message(motivation_data, request.tone)

    # Determine category
    category = _determine_motivation_category(motivation_data, request.context)

    response = MotivationResponse(
        message=message,
        category=category,
    )

    logger.info(f"✅ Generated {category} motivation message")
    return response


def _gather_motivation_data(
    gamification: Dict[str, Any],
    recent_sessions: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    context: str,
) -> Dict[str, Any]:
    """Gather data for motivation generation."""
    data = {
        "context": context,
        "current_streak": gamification.get("current_streak", 0) if gamification else 0,
        "total_xp": gamification.get("total_xp", 0) if gamification else 0,
        "level": gamification.get("level", 1) if gamification else 1,
        "recent_sessions": len(recent_sessions),
        "completed_today": sum(1 for s in recent_sessions if s.get("completed_at")),
    }

    # Add profile-based motivation
    if user_profile:
        data["work_patterns"] = user_profile.get("work_patterns", {})
        data["energy_patterns"] = user_profile.get("energy_patterns", {})

    # Calculate recent productivity
    if recent_sessions:
        completed = data["completed_today"]
        data["completion_rate"] = completed / len(recent_sessions)
    else:
        data["completion_rate"] = 0

    return data


def _generate_motivation_message(data: Dict[str, Any], tone: str) -> str:
    """Generate bounded motivation message using LLM."""
    try:
        client = GeminiClient()

        prompt = f"""
        Generate a short, encouraging motivation message based on this user data:

        Context: {data.get('context', 'general')}
        Current streak: {data.get('current_streak', 0)} days
        Level: {data.get('level', 1)}
        Recent completion rate: {data.get('completion_rate', 0):.1%}
        Sessions today: {data.get('recent_sessions', 0)}

        Tone: {tone} (encouraging, positive, supportive)

        Requirements:
        - Under 150 characters
        - Positive and encouraging
        - Personalized to their progress
        - End with actionable encouragement

        Return only the message text, no quotes or extra formatting.
        """

        response = client.generate_json_response(prompt, max_tokens=100)

        if isinstance(response, str) and len(response) <= 150:
            return response
        elif isinstance(response, dict) and "message" in response:
            message = response["message"]
            if isinstance(message, str) and len(message) <= 150:
                return message

        # Fallback to template
        return _generate_fallback_message(data, tone)

    except Exception as e:
        logger.warning(f"⚠️ LLM motivation generation failed: {str(e)}")
        return _generate_fallback_message(data, tone)


def _generate_fallback_message(data: Dict[str, Any], tone: str) -> str:
    """Generate fallback motivation message."""
    streak = data.get('current_streak', 0)
    level = data.get('level', 1)

    if streak > 0:
        return f"You're on a {streak}-day streak! Keep the momentum going - you've got this! 💪"
    elif level > 1:
        return f"Level {level} achiever! Every step forward counts. Ready for your next win? 🌟"
    else:
        return "Every journey begins with a single step. You've started - that's something to celebrate! 🚀"


def _determine_motivation_category(data: Dict[str, Any], context: str) -> str:
    """Determine the category of motivation."""
    streak = data.get('current_streak', 0)
    completion_rate = data.get('completion_rate', 0)

    if streak >= 7:
        return "streak_celebration"
    elif streak >= 3:
        return "momentum_building"
    elif completion_rate >= 0.8:
        return "high_achiever"
    elif "stuck" in context.lower() or "struggling" in context.lower():
        return "overcoming_challenge"
    elif "start" in context.lower() or "begin" in context.lower():
        return "getting_started"
    else:
        return "general_encouragement"