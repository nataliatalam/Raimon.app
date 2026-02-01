"""
FastAPI router for agent MVP endpoints.

Provides:
- POST /agent-mvp/next-do - Main endpoint
- POST /agent-mvp/simulate - Local testing (no DB)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from agent_mvp.contracts import SelectionConstraints, AgentMVPResponse
from agent_mvp.graph import run_agent_mvp
from core.security import get_current_user
from opik import track
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-mvp", tags=["Agent MVP"])


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
        from agent_mvp.contracts import TaskCandidate
        from agent_mvp.graph import (
            load_candidates,
            derive_constraints,
            llm_select_do,
            llm_coach,
            return_result,
            GraphState,
        )
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
