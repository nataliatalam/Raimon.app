"""
State Adapter Agent - Convert check-in to selection constraints.

Functionality: Transform daily check-in data into task selection constraints.

Inputs: CheckInToConstraintsRequest { check_in_data: DailyCheckIn, user_profile: UserProfileAnalysis }

Outputs: SelectionConstraints { energy_level, time_available, focus_areas, blocked_categories }

Memory:
- reads: ai_learning_data (user_profile)
- writes: NONE (pure function)

LLM: NO (deterministic mapping)

Critical guarantees:
- deterministic constraint generation
- never modifies check-in data
"""

from typing import List, Dict, Any
from agent_mvp.contracts import (
    CheckInToConstraintsRequest,
    SelectionConstraints,
    DailyCheckIn,
    UserProfileAnalysis,
)
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="state_adapter_agent")
def adapt_checkin_to_constraints(
    request: CheckInToConstraintsRequest,
) -> SelectionConstraints:
    """
    Convert daily check-in to task selection constraints.

    Args:
        request: Check-in data and user profile

    Returns:
        Selection constraints for task selection
    """
    logger.info("🔄 Adapting check-in to constraints")

    check_in = request.check_in_data
    user_profile = request.user_profile

    constraints = SelectionConstraints()

    # Map energy level directly (SelectionConstraints uses "current_energy")
    constraints.current_energy = check_in.energy_level

    # Calculate time available from check-in (SelectionConstraints uses "max_minutes")
    constraints.max_minutes = _calculate_time_available(check_in)

    # Determine mode based on energy and time available
    if check_in.energy_level <= 2 and constraints.max_minutes <= 30:
        constraints.mode = "quick"
    elif check_in.energy_level >= 8:
        constraints.mode = "focus"
    elif "learning" in getattr(check_in, "priorities", []):
        constraints.mode = "learning"
    else:
        constraints.mode = "balanced"

    # Extract focus areas and derive avoid_tags conservatively.
    # If user didn't specify focus areas, do not block broad categories.
    focus_areas = _extract_focus_areas(check_in)
    all_categories = ["work", "personal", "health", "learning", "creative", "social", "maintenance"]
    recognized_focus = [cat for cat in focus_areas if cat in all_categories]
    if recognized_focus:
        avoid_tags = [cat for cat in all_categories if cat not in recognized_focus]
        if avoid_tags:
            constraints.avoid_tags = avoid_tags

    # Set prefer_priority based on urgent tasks
    if hasattr(check_in, "priorities") and "urgent" in check_in.priorities:
        constraints.prefer_priority = "urgent"
    elif check_in.energy_level >= 8:
        constraints.prefer_priority = "high"

    logger.info(f"✅ Constraints adapted: energy={constraints.current_energy}, time={constraints.max_minutes}, mode={constraints.mode}")
    return constraints


def _calculate_time_available(check_in: DailyCheckIn) -> int:
    """Calculate available time in minutes from check-in."""
    # Base time from check-in (use focus_minutes if available)
    base_time = check_in.focus_minutes or 120  # Default 2 hours

    # Adjust based on energy level
    energy_multiplier = {
        1: 0.3,   # Very low energy = 30% of stated time
        2: 0.5,   # Low energy = 50%
        3: 0.7,   # Medium-low = 70%
        4: 0.9,   # Medium-high = 90%
        5: 1.0,   # Full energy = 100%
    }.get(check_in.energy_level, 1.0)

    available = int(base_time * energy_multiplier)

    # Cap at reasonable limits
    return max(30, min(480, available))  # 30min to 8hours


def _extract_focus_areas(check_in: DailyCheckIn) -> List[str]:
    """Extract focus areas from check-in priorities."""
    focus_areas = []

    # Map priorities to focus areas
    priority_mapping = {
        "work": ["work", "professional"],
        "personal": ["personal", "home"],
        "health": ["health", "fitness", "wellness"],
        "learning": ["learning", "education", "skill"],
        "creative": ["creative", "art", "design"],
        "social": ["social", "community", "relationships"],
    }

    for priority in check_in.priorities:
        areas = priority_mapping.get(priority.lower(), [priority.lower()])
        focus_areas.extend(areas)

    # Remove duplicates while preserving order
    seen = set()
    unique_areas = []
    for area in focus_areas:
        if area not in seen:
            seen.add(area)
            unique_areas.append(area)

    return unique_areas[:5]  # Limit to 5 focus areas


def _determine_blocked_categories(
    check_in: DailyCheckIn,
    user_profile: UserProfileAnalysis,
) -> List[str]:
    """Determine categories to block based on energy and preferences."""
    blocked = []

    # Block high-energy tasks if energy is low
    if check_in.energy_level <= 2:
        blocked.extend(["urgent", "complex", "creative"])

    # Block based on user patterns
    if user_profile and user_profile.energy_patterns:
        avg_energy = user_profile.energy_patterns.get("avg_energy_by_day", {}).get(check_in.day_of_week, 5)
        if check_in.energy_level < avg_energy - 1:
            blocked.append("challenging")  # Block challenging tasks on low-energy days

    # Block based on stated priorities (focus on what's important)
    all_categories = ["work", "personal", "health", "learning", "creative", "social", "maintenance"]
    stated_priorities = [p.lower() for p in check_in.priorities]

    # Block categories not in priorities (if priorities specified)
    if stated_priorities:
        for category in all_categories:
            if category not in stated_priorities and category not in ["maintenance"]:  # Always allow maintenance
                blocked.append(category)

    return list(set(blocked))  # Remove duplicates


def _calculate_max_task_duration(constraints: SelectionConstraints) -> int:
    """Calculate maximum task duration based on constraints."""
    time_available = constraints.time_available
    energy_level = constraints.energy_level

    # Base max duration as fraction of available time
    if time_available <= 60:  # 1 hour or less
        base_max = min(45, time_available - 5)  # Leave buffer
    elif time_available <= 120:  # 2 hours
        base_max = 60
    elif time_available <= 240:  # 4 hours
        base_max = 90
    else:  # More than 4 hours
        base_max = 120

    # Adjust for energy
    energy_multiplier = {
        1: 0.5,   # Half duration for very low energy
        2: 0.7,   # 70% for low energy
        3: 0.9,   # 90% for medium-low
        4: 1.0,   # Full for medium-high
        5: 1.2,   # 120% for full energy (can handle longer tasks)
    }.get(energy_level, 1.0)

    max_duration = int(base_max * energy_multiplier)

    # Cap at available time minus buffer
    return max(15, min(max_duration, time_available - 10))
