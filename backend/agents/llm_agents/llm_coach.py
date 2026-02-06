"""
Coach Agent: Generates motivational coaching copy for the selected task.

Input: task + reason codes + mode
Output: title + message + next_step
"""

from typing import List, Optional
from models.contracts import (
    TaskCandidate,
    CoachOutput,
)
from services.llm_service.prompts import build_coach_prompt
from orchestrator.validators import validate_coach_output
from services.llm_service import LLMService
from opik import track
import logging

logger = logging.getLogger(__name__)

# Default LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create singleton LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


@track(name="coach_agent")
def generate_coaching_message(
    task: TaskCandidate,
    reason_codes: List[str],
    mode: str = "balanced",
    user_name: Optional[str] = None,
    llm_service: Optional[LLMService] = None,
) -> tuple[CoachOutput, bool]:
    """
    Generate coaching message using LLM service (Gemini).

    Args:
        task: Selected task
        reason_codes: Why this task was selected
        mode: Selection mode (focus, quick, learning, balanced)
        user_name: Optional user name for personalization
        llm_service: Optional LLM service instance (uses singleton if not provided)

    Returns:
        (CoachOutput, is_valid: bool)
        is_valid=False means a minimal fallback was used
    """

    logger.info(f"🧠 Coach: Generating message for task '{task.title}'")

    try:
        # Build prompt
        prompt = build_coach_prompt(task, reason_codes, mode, user_name)

        # Get LLM service and call it
        service = llm_service or get_llm_service()
        raw_response = service.generate_json(
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
