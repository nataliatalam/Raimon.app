"""
LangGraph orchestrator for agent MVP.

State machine with nodes:
1. load_candidates - Supabase query
2. derive_constraints - from daily_check_in or defaults
3. llm_select_do - call DoSelector
4. validate_or_fallback - strict validation
5. llm_coach - call Coach
6. return_result - prepare response

Uses Opik for tracing each node and LLM call.
"""

from typing import Optional, List
from datetime import datetime, timezone, date
from agent_mvp.contracts import (
    GraphState,
    TaskCandidate,
    SelectionConstraints,
    ActiveDo,
)
from agent_mvp.llm_do_selector import select_task
from agent_mvp.llm_coach import generate_coaching_message
from opik import track
from core.supabase import get_supabase_admin
import logging

logger = logging.getLogger(__name__)


@track(name="graph_load_candidates")
def load_candidates(state: GraphState) -> GraphState:
    """
    Load candidate tasks from Supabase for the user.
    Filters for open (non-completed) tasks only.
    """
    logger.info(f"📥 Loading candidates for user {state.user_id}")

    try:
        supabase = get_supabase_admin()

        # Query open tasks
        response = (
            supabase.table("tasks")
            .select("id, title, priority, status, estimated_duration, due_at, tags, created_at")
            .eq("user_id", state.user_id)
            .in_("status", ["todo", "in_progress", "paused", "blocked"])
            .order("priority", desc=True)
            .order("due_at", desc=False)
            .limit(50)
            .execute()
        )

        if not response.data:
            logger.warning(f"⚠️  No open tasks found for user {state.user_id}")
            state.error = "No open tasks available"
            return state

        # Parse into TaskCandidate objects
        candidates = []
        for row in response.data:
            due_at = None
            if row.get("due_at"):
                try:
                    due_at = datetime.fromisoformat(
                        row["due_at"].replace("Z", "+00:00")
                    )
                except:
                    pass

            candidate = TaskCandidate(
                id=row["id"],
                title=row["title"],
                priority=row.get("priority", "medium"),
                status=row.get("status", "todo"),
                estimated_duration=row.get("estimated_duration"),
                due_at=due_at,
                tags=row.get("tags") or [],
                created_at=row.get("created_at"),
            )
            candidates.append(candidate)

        state.candidates = candidates
        logger.info(f"✅ Loaded {len(candidates)} candidate tasks")
        return state

    except Exception as e:
        logger.error(f"❌ Error loading candidates: {str(e)}")
        state.error = f"Failed to load tasks: {str(e)}"
        return state


@track(name="graph_derive_constraints")
def derive_constraints(state: GraphState) -> GraphState:
    """
    Derive selection constraints from latest daily_check_in or use defaults.
    """
    logger.info(f"⚙️  Deriving constraints for user {state.user_id}")

    try:
        supabase = get_supabase_admin()
        today = date.today().isoformat()

        # Try to load today's check-in
        response = (
            supabase.table("daily_check_ins")
            .select("energy_level, mood, stress_level")
            .eq("user_id", state.user_id)
            .eq("date", today)
            .execute()
        )

        energy_level = 5  # Default
        if response.data:
            energy_level = response.data[0].get("energy_level", 5)

        # Build constraints (use provided or derive from energy)
        if state.constraints is None:
            mode = "quick" if energy_level <= 3 else "balanced" if energy_level <= 7 else "focus"
            state.constraints = SelectionConstraints(
                max_minutes=90,
                mode=mode,
                current_energy=energy_level,
            )

        logger.info(
            f"✅ Constraints: energy={state.constraints.current_energy}, "
            f"mode={state.constraints.mode}, max_time={state.constraints.max_minutes}min"
        )
        return state

    except Exception as e:
        logger.error(f"❌ Error deriving constraints: {str(e)}")
        # Use defaults
        state.constraints = SelectionConstraints()
        return state


@track(name="graph_llm_select_do")
def llm_select_do(state: GraphState) -> GraphState:
    """
    Call DoSelector agent to pick best task.
    """
    logger.info("🤖 Calling DoSelector agent")

    if state.error:
        return state

    if not state.candidates:
        state.error = "No candidates available"
        return state

    try:
        selector_output, is_valid = select_task(
            candidates=state.candidates,
            constraints=state.constraints,
        )

        # Find the actual task object
        selected_task = next(
            (c for c in state.candidates if c.id == selector_output.task_id),
            None,
        )

        if not selected_task:
            state.error = f"Selected task {selector_output.task_id} not found in candidates"
            return state

        state.active_do = ActiveDo(
            task=selected_task,
            reason_codes=selector_output.reason_codes,
            alt_task_ids=selector_output.alt_task_ids,
        )

        logger.info(f"✅ Selected task: {selected_task.title}")
        return state

    except Exception as e:
        logger.error(f"❌ DoSelector error: {str(e)}")
        state.error = f"Selection failed: {str(e)}"
        return state


@track(name="graph_llm_coach")
def llm_coach(state: GraphState) -> GraphState:
    """
    Call Coach agent to generate motivational message.
    """
    logger.info("🧠 Calling Coach agent")

    if state.error or not state.active_do:
        return state

    try:
        coach_output, is_valid = generate_coaching_message(
            task=state.active_do.task,
            reason_codes=state.active_do.reason_codes,
            mode=state.constraints.mode if state.constraints else "balanced",
        )

        state.coach_message = coach_output
        logger.info(f"✅ Coach message ready: '{coach_output.title}'")
        return state

    except Exception as e:
        logger.error(f"❌ Coach error: {str(e)}")
        state.error = f"Coaching failed: {str(e)}"
        return state


@track(name="graph_return_result")
def return_result(state: GraphState) -> dict:
    """
    Prepare final response from state.
    """
    logger.info("📤 Preparing result")

    if state.error:
        return {
            "success": False,
            "error": state.error,
            "data": {},
        }

    if not state.active_do or not state.coach_message:
        return {
            "success": False,
            "error": "Missing active_do or coach_message",
            "data": {},
        }

    return {
        "success": True,
        "error": None,
        "data": {
            "active_do": {
                "task_id": state.active_do.task.id,
                "task_title": state.active_do.task.title,
                "reason_codes": state.active_do.reason_codes,
                "alt_task_ids": state.active_do.alt_task_ids,
                "selected_at": state.active_do.selected_at.isoformat(),
            },
            "coach_message": {
                "title": state.coach_message.title,
                "message": state.coach_message.message,
                "next_step": state.coach_message.next_step,
            },
        },
    }


@track(name="agent_mvp_orchestrator")
async def run_agent_mvp(
    user_id: str,
    constraints: Optional[SelectionConstraints] = None,
) -> dict:
    """
    Main orchestration function: run the full LangGraph workflow.

    Args:
        user_id: User UUID
        constraints: Optional override constraints

    Returns:
        Response dict with {success, data, error}
    """
    logger.info(f"🚀 Starting agent MVP for user {user_id}")

    # Initialize state
    state = GraphState(
        user_id=user_id,
        constraints=constraints,
    )

    # Execute nodes sequentially
    state = load_candidates(state)
    if state.error:
        return return_result(state)

    state = derive_constraints(state)
    if state.error:
        return return_result(state)

    state = llm_select_do(state)
    if state.error:
        return return_result(state)

    state = llm_coach(state)
    if state.error:
        return return_result(state)

    result = return_result(state)
    logger.info(f"✅ Agent MVP complete: {result['success']}")

    return result
