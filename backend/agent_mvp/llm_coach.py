"""
Coach Agent: Generates motivational coaching copy for the selected task.

Input: task + reason codes + mode
Output: title + message + next_step
"""

from typing import List, Optional
from agent_mvp.contracts import (
    TaskCandidate,
    CoachOutput,
)
from agent_mvp.gemini_client import get_gemini_client
from agent_mvp.prompts import build_coach_prompt
from agent_mvp.validators import validate_coach_output
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="coach_agent")
def generate_coaching_message(
    task: TaskCandidate,
    reason_codes: List[str],
    mode: str = "balanced",
    user_name: Optional[str] = None,
) -> tuple[CoachOutput, bool]:
    """
    Generate coaching message using Gemini.

    Args:
        task: Selected task
        reason_codes: Why this task was selected
        mode: Selection mode (focus, quick, learning, balanced)
        user_name: Optional user name for personalization

    Returns:
        (CoachOutput, is_valid: bool)
        is_valid=False means a minimal fallback was used
    """

    logger.info(f"🧠 Coach: Generating message for task '{task.title}'")

    try:
        # Build prompt
        prompt = build_coach_prompt(task, reason_codes, mode, user_name)

        # Call Gemini
        gemini = get_gemini_client()
        raw_response = gemini.generate_json_response(
            prompt=prompt,
            temperature=0.8,  # Slightly higher for more creative copy
            max_tokens=200,
        )

        # Validate
        output, is_valid = validate_coach_output(raw_response)

        if is_valid:
            logger.info(f"✅ Coach message generated: '{output.title}'")
        else:
            logger.warning(f"⚠️  Used fallback coach message")

        return output, is_valid

    except Exception as e:
        logger.error(f"❌ Coach error: {str(e)}")
        # Use minimal fallback
        fallback = CoachOutput(
            title="Let's go",
            message="You've got this.",
            next_step="Begin.",
        )
        return fallback, False
