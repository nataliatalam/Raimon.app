"""
Validation and fallback logic for agent MVP.

Validates LLM outputs and provides deterministic fallbacks.
"""

from typing import List, Optional, Tuple
from agent_mvp.contracts import (
    TaskCandidate,
    DoSelectorOutput,
    CoachOutput,
)
import logging

logger = logging.getLogger(__name__)


def validate_do_selector_output(
    raw_output: dict,
    candidates: List[TaskCandidate],
) -> Tuple[DoSelectorOutput, bool]:
    """
    Validate DoSelector output against candidates.

    Returns:
        (DoSelectorOutput, is_valid: bool)
        If invalid, returns fallback selection + False
    """
    try:
        # Try to parse as DoSelectorOutput
        output = DoSelectorOutput(**raw_output)

        # Validate task_id is in candidates
        candidate_ids = {c.id for c in candidates}
        if output.task_id not in candidate_ids:
            logger.warning(
                f"❌ task_id '{output.task_id}' not in candidates. "
                f"Fallback to deterministic pick."
            )
            return fallback_do_selector(candidates), False

        # Validate alt_task_ids are in candidates
        valid_alts = [aid for aid in output.alt_task_ids if aid in candidate_ids]
        output.alt_task_ids = valid_alts

        logger.info(f"✅ Valid DoSelector output: {output.task_id}")
        return output, True

    except ValueError as e:
        logger.warning(f"❌ Invalid DoSelector output format: {str(e)}")
        return fallback_do_selector(candidates), False
    except Exception as e:
        logger.error(f"❌ Unexpected error validating DoSelector: {str(e)}")
        return fallback_do_selector(candidates), False


def validate_coach_output(raw_output: dict) -> Tuple[CoachOutput, bool]:
    """
    Validate Coach output.

    Returns:
        (CoachOutput, is_valid: bool)
        If invalid, returns empty CoachOutput + False
    """
    try:
        output = CoachOutput(**raw_output)
        logger.info(f"✅ Valid Coach output: {output.title}")
        return output, True

    except ValueError as e:
        logger.warning(f"❌ Invalid Coach output: {str(e)}")
        return CoachOutput(
            title="Let's go",
            message="You've got this.",
            next_step="Begin.",
        ), False
    except Exception as e:
        logger.error(f"❌ Unexpected error validating Coach: {str(e)}")
        return CoachOutput(
            title="Let's go",
            message="You've got this.",
            next_step="Begin.",
        ), False


def fallback_do_selector(candidates: List[TaskCandidate]) -> DoSelectorOutput:
    """
    Deterministic fallback: pick highest priority, shortest task.

    Ordering:
    1. Urgent/High priority first
    2. Shortest estimated duration
    3. Oldest creation date (FIFO)
    """
    if not candidates:
        raise ValueError("No candidates available for fallback selection")

    priority_order = {"urgent": 4, "high": 3, "medium": 2, "low": 1}

    # Sort by: priority (desc), duration (asc), created_at (asc)
    sorted_tasks = sorted(
        candidates,
        key=lambda t: (
            -priority_order.get(t.priority, 0),  # Negative for descending
            t.estimated_duration or 999,  # Ascending
            t.created_at or "9999",  # Ascending
        ),
    )

    selected = sorted_tasks[0]
    logger.warning(
        f"🔄 Fallback selection: {selected.id} "
        f"({selected.priority}, {selected.estimated_duration}min)"
    )

    # Provide 1-2 alternatives
    alt_ids = [t.id for t in sorted_tasks[1:3]]

    return DoSelectorOutput(
        task_id=selected.id,
        reason_codes=["fallback", "fallback_deterministic"],
        alt_task_ids=alt_ids,
    )
