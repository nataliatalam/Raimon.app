"""
FastAPI router for agent MVP endpoints.

Provides:
- POST /agent-mvp/next-do - Main endpoint
- POST /agent-mvp/simulate - Local testing (no DB)
- POST /agent-mvp/app-open - Resume user context
- POST /agent-mvp/checkin - Process daily check-in
- POST /agent-mvp/do-action - Handle task actions
- POST /agent-mvp/day-end - Process day completion
- POST /agent-mvp/insights - Get project insights
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from datetime import datetime, timezone
from models.contracts import (
    SelectionConstraints,
    AgentMVPResponse,
    AppOpenRequest,
    AppOpenEvent,
    CheckInSubmittedEvent,
    DoNextEvent,
    DoActionEvent,
    DayEndEvent,
    ProjectInsightRequest,
)
from orchestrator.graph import run_agent_mvp
from orchestrator.orchestrator import process_agent_event
from services.storage_service import log_agent_event
from agents.llm_agents import generate_project_insights
from core.security import get_current_user
from opik import track
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-mvp", tags=["Agent MVP"])


@router.post("/smoke")
@track(name="agent_mvp_smoke_test")
async def smoke_test():
    """
    Smoke test endpoint for verifying Opik tracing is working.
    
    No auth required. Returns immediate response and emits Opik trace.
    
    Use this to verify:
    1. Endpoint is reachable
    2. @track decorator is working
    3. Trace appears in Opik dashboard
    """
    logger.info("🔥 /smoke endpoint hit - tracing should appear in Opik")
    
    return {
        "success": True,
        "message": "Opik smoke test passed",
        "trace_expected": True,
        "action": "Check Opik dashboard for 'agent_mvp_smoke_test' trace"
    }



@router.post("/next-do", response_model=AgentMVPResponse)
@track(name="agent_mvp_next_do_endpoint")
async def next_do(
    constraints: Optional[SelectionConstraints] = None,
    current_user: dict = Depends(get_current_user),
) -> AgentMVPResponse:
    """
    Main endpoint: Get the next recommended task with coaching.

    Auth required. Returns:
    {
      success: true,
      data: {
        active_do: {
          task_id, task_title, reason_codes, alt_task_ids, selected_at
        },
        coach_message: {
          title, message, next_step
        }
      }
    }
    """
    user_id = current_user["id"]
    logger.info(f"📨 /next-do request from user {user_id}")

    try:
        # Log DO_NEXT event through orchestrator for tracking
        try:
            do_next_event = DoNextEvent(
                user_id=user_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                context="task_selection",
            )
            log_agent_event(user_id, "DO_NEXT", {"context": "task_selection"})
            logger.info(f"🎯 DO_NEXT event logged for user {user_id}")
        except Exception as event_err:
            logger.warning(f"DO_NEXT event logging failed (non-blocking): {event_err}")

        # Run orchestrator
        result = await run_agent_mvp(
            user_id=user_id,
            constraints=constraints,
        )

        if not result["success"]:
            logger.error(f"❌ Agent MVP failed: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Agent MVP failed"),
            )

        logger.info(f"✅ /next-do successful for user {user_id}")
        return AgentMVPResponse(
            success=True,
            data=result["data"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in /next-do: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/app-open", response_model=AgentMVPResponse)
@track(name="agent_mvp_app_open_endpoint")
async def app_open(
    request: AppOpenRequest,
    current_user: dict = Depends(get_current_user),
) -> AgentMVPResponse:
    """
    Resume user context when app opens.

    Returns context resumption data.
    """
    user_id = current_user["id"]
    logger.info(f"📱 /app-open request from user {user_id}")

    try:
        event = AppOpenEvent(
            user_id=user_id,
            current_time=request.current_time or datetime.now(timezone.utc),
        )

        result = process_agent_event(event)

        logger.info(f"✅ /app-open successful for user {user_id}")
        return result

    except Exception as e:
        logger.error(f"❌ App open error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume context",
        )


@router.post("/checkin", response_model=AgentMVPResponse)
@track(name="agent_mvp_checkin_endpoint")
async def checkin(
    event: CheckInSubmittedEvent,
    current_user: dict = Depends(get_current_user),
) -> AgentMVPResponse:
    """
    Process daily check-in submission.

    Adapts check-in to selection constraints.
    """
    user_id = current_user["id"]
    logger.info(f"📝 /checkin request from user {user_id}")

    try:
        event.user_id = user_id
        result = process_agent_event(event)

        logger.info(f"✅ /checkin successful for user {user_id}")
        return result

    except Exception as e:
        logger.error(f"❌ Check-in error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process check-in",
        )


@router.post("/do-action", response_model=AgentMVPResponse)
@track(name="agent_mvp_do_action_endpoint")
async def do_action(
    event: DoActionEvent,
    current_user: dict = Depends(get_current_user),
) -> AgentMVPResponse:
    """
    Handle task actions (start, complete, stuck).

    Updates gamification and provides interventions.
    """
    user_id = current_user["id"]
    logger.info(f"⚡ /do-action request from user {user_id}: {event.action}")

    try:
        event.user_id = user_id
        result = process_agent_event(event)

        logger.info(f"✅ /do-action successful for user {user_id}")
        return result

    except Exception as e:
        logger.error(f"❌ Do action error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process action",
        )


@router.post("/day-end", response_model=AgentMVPResponse)
@track(name="agent_mvp_day_end_endpoint")
async def day_end(
    event: DayEndEvent,
    current_user: dict = Depends(get_current_user),
) -> AgentMVPResponse:
    """
    Process day completion and generate insights.
    """
    user_id = current_user["id"]
    logger.info(f"🌅 /day-end request from user {user_id}")

    try:
        event.user_id = user_id
        result = process_agent_event(event)

        logger.info(f"✅ /day-end successful for user {user_id}")
        return result

    except Exception as e:
        logger.error(f"❌ Day end error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process day end",
        )


@router.post("/insights", response_model=AgentMVPResponse)
@track(name="agent_mvp_insights_endpoint")
async def get_insights(
    request: ProjectInsightRequest,
    current_user: dict = Depends(get_current_user),
) -> AgentMVPResponse:
    """
    Generate project insights.

    Returns insights about project progress and patterns.
    """
    user_id = current_user["id"]
    logger.info(f"💡 /insights request from user {user_id} for project {request.project_id}")

    try:
        insights = generate_project_insights(user_id, request)

        logger.info(f"✅ /insights successful for user {user_id}")
        return AgentMVPResponse(
            success=True,
            data={"insights": [i.model_dump() for i in insights.insights]},
        )

    except Exception as e:
        logger.error(f"❌ Insights error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insights",
        )


@router.post("/simulate", response_model=AgentMVPResponse)
@track(name="agent_mvp_simulate_endpoint")
async def simulate(
    constraints: Optional[SelectionConstraints] = None,
) -> AgentMVPResponse:
    """
    Local testing endpoint: simulate with mock tasks (no auth, no DB).

    Useful for testing LLM behavior and prompt tuning.
    """
    logger.info("🧪 /simulate request (no auth)")

    try:
        from models.contracts import TaskCandidate
        from orchestrator.graph import (
            load_candidates,
            derive_constraints,
            llm_select_do,
            llm_coach,
            return_result,
        )
        from orchestrator.contracts import GraphState
        from datetime import datetime, timezone, timedelta

        # Mock state with sample tasks
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)

        state = GraphState(
            user_id="demo-user-123",
            candidates=[
                TaskCandidate(
                    id="task-001",
                    title="Fix login page CSS styling",
                    priority="high",
                    status="in_progress",
                    estimated_duration=45,
                    due_at=tomorrow,
                    tags=["frontend", "bug"],
                    created_at=now,
                ),
                TaskCandidate(
                    id="task-002",
                    title="Review pull request from Alice",
                    priority="medium",
                    status="todo",
                    estimated_duration=30,
                    due_at=None,
                    tags=["review"],
                    created_at=now,
                ),
                TaskCandidate(
                    id="task-003",
                    title="Learn about React 19 hooks",
                    priority="low",
                    status="todo",
                    estimated_duration=90,
                    due_at=None,
                    tags=["learning"],
                    created_at=now,
                ),
            ],
            constraints=constraints or SelectionConstraints(
                max_minutes=60,
                mode="balanced",
                current_energy=6,
            ),
        )

        logger.info(f"📋 Mock state created with {len(state.candidates)} tasks")

        # Run node sequence (skip load_candidates & derive_constraints since we mocked)
        state = llm_select_do(state)
        if state.error:
            return AgentMVPResponse(
                success=False,
                error=state.error,
            )

        state = llm_coach(state)
        if state.error:
            return AgentMVPResponse(
                success=False,
                error=state.error,
            )

        result = return_result(state)
        logger.info(f"✅ /simulate complete: {result['success']}")

        return AgentMVPResponse(
            success=result["success"],
            data=result.get("data", {}),
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"❌ Simulate error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulate failed: {str(e)}",
        )
