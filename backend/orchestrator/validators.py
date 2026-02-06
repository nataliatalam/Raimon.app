"""
Validation and fallback logic for agent MVP.

Validates LLM outputs and provides deterministic fallbacks.
"""

from typing import List, Optional, Tuple, Dict, Any
from models.contracts import (
    TaskCandidate,
    DoSelectorOutput,
    CoachOutput,
    ProjectSuggestion,
    Microtask,
    Insight,
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


def fallback_coach(selected_task: Dict[str, Any], context: str = "task_selection") -> Tuple[str, str]:
    """Deterministic fallback coaching message.

    Returns:
        (message, category)
    """
    title = selected_task.get("title", "this task") if isinstance(selected_task, dict) else "this task"
    if context == "task_selection":
        message = f"Start with one small step on {title}. You can do this."
        category = "focus"
    elif context == "task_completion":
        message = f"Nice work finishing {title}. Take a quick breath and plan your next step."
        category = "motivation"
    else:
        message = f"Keep going on {title}. Small progress adds up."
        category = "general"

    return message, category


def validate_project_suggestions(raw_output: List[Dict[str, Any]]) -> Tuple[List[ProjectSuggestion], bool]:
    """
    Validate project suggestions output.

    Returns:
        (List[ProjectSuggestion], is_valid: bool)
    """
    if not isinstance(raw_output, list):
        logger.warning("❌ Project suggestions not a list")
        return [], False

    suggestions = []
    for item in raw_output[:3]:  # Limit to 3
        try:
            if isinstance(item, dict) and "suggestion" in item:
                suggestion = ProjectSuggestion(
                    category=item.get("category", "general"),
                    suggestion=item["suggestion"][:100],  # Bound length
                    impact=item.get("impact", "medium"),
                )
                suggestions.append(suggestion)
        except Exception as e:
            logger.warning(f"❌ Invalid suggestion item: {str(e)}")
            continue

    is_valid = len(suggestions) > 0
    logger.info(f"✅ Valid project suggestions: {len(suggestions)} items")
    return suggestions, is_valid


def validate_stuck_microtasks(raw_output: List[str]) -> Tuple[List[Microtask], bool]:
    """
    Validate stuck microtasks output.

    Returns:
        (List[Microtask], is_valid: bool)
    """
    if not isinstance(raw_output, list):
        logger.warning("❌ Stuck microtasks not a list")
        return [], False

    microtasks = []
    for task in raw_output[:5]:  # Limit to 5
        try:
            if isinstance(task, str) and len(task) <= 100:
                microtask = Microtask(
                    description=task,
                    estimated_minutes=2,  # All microtasks are 2 minutes
                    category="unstuck_help",
                )
                microtasks.append(microtask)
        except Exception as e:
            logger.warning(f"❌ Invalid microtask item: {str(e)}")
            continue

    is_valid = len(microtasks) > 0
    logger.info(f"✅ Valid stuck microtasks: {len(microtasks)} items")
    return microtasks, is_valid


def validate_project_insights(raw_output: List[str]) -> Tuple[List[Insight], bool]:
    """
    Validate project insights output.

    Returns:
        (List[Insight], is_valid: bool)
    """
    if not isinstance(raw_output, list):
        logger.warning("❌ Project insights not a list")
        return [], False

    insights = []
    for item in raw_output[:5]:  # Limit to 5
        try:
            if isinstance(item, str) and len(item) <= 150:
                insight = Insight(
                    content=item,
                    category="project",
                    confidence=0.85,  # LLM-generated
                )
                insights.append(insight)
        except Exception as e:
            logger.warning(f"❌ Invalid insight item: {str(e)}")
            continue

    is_valid = len(insights) > 0
    logger.info(f"✅ Valid project insights: {len(insights)} items")
    return insights, is_valid


def validate_motivation_message(raw_output: str) -> Tuple[str, bool]:
    """
    Validate motivation message output.

    Returns:
        (message, is_valid: bool)
    """
    if not isinstance(raw_output, str):
        logger.warning("❌ Motivation message not a string")
        return "You've got this!", False

    # Bound length
    message = raw_output[:150] if len(raw_output) > 150 else raw_output

    # Basic validation - not empty and not too short
    is_valid = len(message.strip()) > 10
    if not is_valid:
        logger.warning("❌ Motivation message too short")
        return "You've got this!", False

    logger.info(f"✅ Valid motivation message: {len(message)} chars")
    return message, True


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
