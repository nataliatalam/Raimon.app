"""
DoSelector Agent: Uses Gemini to select the best task from candidates.

Input: list of tasks + constraints
Output: selected task_id + reason codes + alternatives
"""

from typing import List, Optional
from models.contracts import (
    TaskCandidate,
    SelectionConstraints,
    DoSelectorOutput,
)
from services.llm_service.prompts import build_do_selector_prompt
from orchestrator.validators import validate_do_selector_output
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


@track(name="do_selector_agent")
def select_task(
    candidates: List[TaskCandidate],
    constraints: SelectionConstraints,
    recent_actions: dict = None,
    llm_service: Optional[LLMService] = None,
) -> tuple[DoSelectorOutput, bool]:
    """
    Select the best task using LLM service (Gemini).

    Args:
        candidates: List of candidate tasks
        constraints: Selection constraints (time, energy, mode, etc.)
        recent_actions: Optional context from recent actions
        llm_service: Optional LLM service instance (uses singleton if not provided)

    Returns:
        (DoSelectorOutput, is_valid: bool)
        is_valid=False means fallback was used
    """
    if not candidates:
        raise ValueError("At least one candidate task required")

    logger.info(f"🤖 DoSelector: Selecting from {len(candidates)} candidates")

    try:
        # Build prompt
        prompt = build_do_selector_prompt(candidates, constraints, recent_actions)

        # Get LLM service and call it
        service = llm_service or get_llm_service()
        raw_response = service.generate_json(
            prompt=prompt,
            temperature=0.5,  # Lower temp for deterministic selection
            max_tokens=300,
        )

        # Validate and get fallback if needed
        output, is_valid = validate_do_selector_output(raw_response, candidates)

        if is_valid:
            logger.info(f"✅ Selected task: {output.task_id}")
        else:
            logger.warning(f"⚠️  Used fallback selection: {output.task_id}")

        return output, is_valid

    except Exception as e:
        logger.error(f"❌ DoSelector error: {str(e)}")
        # Use fallback on any error
        fallback_output, _ = validate_do_selector_output({}, candidates)
        return fallback_output, False
