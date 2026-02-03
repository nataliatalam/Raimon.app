"""
Context Continuity Agent - App open state resumption.

Functionality: Resume user context when app opens, suggesting continuation of previous work.

Inputs: AppOpenRequest { user_id, current_time }

Outputs: ContextResumption { previous_session: WorkSession?, suggested_continuation: str?, context_hints: List[str] }

Memory:
- reads: work_sessions (recent), active_do, session_state
- writes: NONE (read-only)

LLM: NO (deterministic context retrieval)

Critical guarantees:
- never modifies session data
- only returns recent context (last 24 hours)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from agent_mvp.contracts import (
    AppOpenRequest,
    ContextResumption,
    WorkSession,
)
from agent_mvp.storage import get_recent_sessions, get_active_do, get_session_state
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="context_continuity_agent")
def resume_context(
    request: AppOpenRequest,
) -> ContextResumption:
    """
    Resume user context on app open.

    Args:
        request: App open request

    Returns:
        Context resumption data
    """
    logger.info(f"🔄 Resuming context for user {request.user_id}")

    resumption = ContextResumption()

    # Get recent sessions (last 24 hours)
    recent_sessions = get_recent_sessions(request.user_id, hours=24)

    if recent_sessions:
        # Get the most recent session
        latest_session = max(recent_sessions, key=lambda s: s.get("start_time", ""))
        resumption.previous_session = WorkSession(**latest_session)

        # Generate continuation suggestion
        resumption.suggested_continuation = _generate_continuation_suggestion(latest_session)

    # Get active task if exists
    active_do = get_active_do(request.user_id)
    if active_do:
        resumption.context_hints.append(f"Active task: {active_do.get('task_title', 'Unknown')}")

    # Get session state hints
    session_state = get_session_state(request.user_id)
    if session_state:
        hints = _extract_state_hints(session_state)
        resumption.context_hints.extend(hints)

    # Add time-based hints
    time_hints = _generate_time_hints(request.current_time)
    resumption.context_hints.extend(time_hints)

    logger.info(f"✅ Context resumed with {len(resumption.context_hints)} hints")
    return resumption


def _generate_continuation_suggestion(session: Dict[str, Any]) -> Optional[str]:
    """Generate suggestion for continuing previous work."""
    if not session:
        return None

    task_title = session.get("task_title", "")
    completed = session.get("completed_at") is not None
    duration = session.get("duration_minutes", 0)
    actual_duration = session.get("actual_duration_minutes", duration)

    if completed:
        return f"Great job completing '{task_title}'! Ready for your next task?"
    elif actual_duration > 0:
        if actual_duration < duration * 0.5:
            return f"You were working on '{task_title}' - want to continue where you left off?"
        else:
            return f"You made good progress on '{task_title}' - ready to finish it?"
    else:
        return f"You started '{task_title}' - shall we continue?"

    return None


def _extract_state_hints(state: Dict[str, Any]) -> List[str]:
    """Extract helpful hints from session state."""
    hints = []

    # Energy hints
    last_energy = state.get("last_energy_level")
    if last_energy:
        if last_energy <= 2:
            hints.append("You mentioned feeling low energy last time - how are you feeling now?")
        elif last_energy >= 4:
            hints.append("You were feeling energetic last time - let's channel that!")

    # Focus hints
    focus_areas = state.get("focus_areas", [])
    if focus_areas:
        hints.append(f"Previously focusing on: {', '.join(focus_areas[:3])}")

    # Streak hints
    current_streak = state.get("current_streak", 0)
    if current_streak > 0:
        hints.append(f"You're on a {current_streak} day streak - keep it up!")

    return hints


def _generate_time_hints(current_time: datetime) -> List[str]:
    """Generate time-based context hints."""
    hints = []
    hour = current_time.hour

    # Time of day hints
    if 5 <= hour < 9:
        hints.append("Early morning session - great for focused work!")
    elif 9 <= hour < 12:
        hints.append("Morning productivity time - perfect for important tasks!")
    elif 12 <= hour < 17:
        hints.append("Afternoon session - consider a short break if needed")
    elif 17 <= hour < 21:
        hints.append("Evening work time - wind down with lighter tasks")
    else:
        hints.append("Late night session - maybe wrap up and rest?")

    # Day of week hints
    day = current_time.weekday()
    if day == 0:  # Monday
        hints.append("Monday momentum - start the week strong!")
    elif day == 4:  # Friday
        hints.append("Friday focus - finish strong before the weekend!")
    elif day >= 5:  # Weekend
        hints.append("Weekend work - balance with rest and fun!")

    return hints