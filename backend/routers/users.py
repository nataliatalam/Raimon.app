from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from models.user import (
    UserProfile,
    UserProfileUpdate,
    UserPreferencesUpdate,
    OnboardingUpdate,
    CheckInRequest,
    FlowerPointsUpdate,
    GraveyardMetaUpdate,
)
from core.supabase import get_supabase, get_supabase_admin
from core.security import get_current_user
from agent_mvp.contracts import CheckInSubmittedEvent
from agent_mvp.orchestrator import process_agent_event
from datetime import datetime, timezone, date
from opik import track
import logging
from agent_mvp.orchestrator import process_agent_event
from agent_mvp.contracts import CheckInSubmittedEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])


# ============================================================================
# Agent Integration - Triggers orchestrator on user events
# ============================================================================

def trigger_agent_on_checkin(user_id: str, energy_level: int, focus_areas: List[str]):
    """
    Emit CHECKIN_SUBMITTED event to orchestrator (sync, doesn't block API response much).
    Logs success/failure but doesn't block the API response.
    """
    try:
        event = CheckInSubmittedEvent(
            user_id=user_id,
            energy_level=energy_level,
            focus_areas=focus_areas,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        logger.info(f"🤖 AGENTS_INVOKED event_type=CHECKIN_SUBMITTED user_id={user_id}")
        result = process_agent_event(event)
        logger.info(f"🤖 AGENTS_DONE active_do_task_id={result.get('data', {}).get('selected_task_id', 'N/A')} user_id={user_id}")
    except Exception as e:
        logger.error(f"❌ Agent invocation failed: {str(e)}", exc_info=False)


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get the current user's profile."""
    return {
        "success": True,
        "data": {"user": current_user},
    }


@router.put("/profile")
async def update_profile(
    request: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update the current user's profile."""
    try:
        supabase = get_supabase_admin()

        update_data = request.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        response = (
            supabase.table("users")
            .update(update_data)
            .eq("id", current_user["id"])
            .execute()
        )

        return {
            "success": True,
            "data": {"user": response.data[0] if response.data else current_user},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )


@router.patch("/preferences")
async def update_preferences(
    request: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update user preferences."""
    try:
        supabase = get_supabase_admin()

        update_data = request.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        response = (
            supabase.table("user_preferences")
            .update(update_data)
            .eq("user_id", current_user["id"])
            .execute()
        )

        return {
            "success": True,
            "data": {"preferences": response.data[0] if response.data else {}},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences",
        )


@router.get("/onboarding-status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """Get the user's onboarding status."""
    return {
        "success": True,
        "data": {
            "onboarding_completed": current_user.get("onboarding_completed", False),
            "onboarding_step": current_user.get("onboarding_step", 0),
        },
    }


@router.put("/onboarding")
async def update_onboarding(
    request: OnboardingUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update onboarding progress."""
    try:
        logger.debug(
            "update_onboarding payload",
            extra={
                "user_id": current_user.get("id"),
                "step": request.step,
                "payload_keys": list(request.data.keys()) if request.data else [],
            },
        )
        # Use service-role client so RLS doesn’t block server-side onboarding updates
        supabase = get_supabase_admin()

        # Update onboarding step
        is_completed = request.step >= 3  # Assuming 3 steps total

        supabase.table("users").update(
            {
                "onboarding_step": request.step,
                "onboarding_completed": is_completed,
            }
        ).eq("id", current_user["id"]).execute()

        # Update preferences if provided
        if request.data:
            prefs_update = {}
            if "energy_patterns" in request.data:
                prefs_update["energy_patterns"] = request.data["energy_patterns"]
            if "work_style" in request.data:
                prefs_update["work_style"] = request.data["work_style"]

            if prefs_update:
                supabase.table("user_preferences").update(prefs_update).eq(
                    "user_id", current_user["id"]
                ).execute()

        return {
            "success": True,
            "data": {
                "onboarding_step": request.step,
                "completed": is_completed,
                "next_step": "complete" if is_completed else f"step_{request.step + 1}",
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error in update_onboarding",
            extra={
                "user_id": current_user.get("id"),
                "step": request.step,
                "payload_sample": request.data,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update onboarding",
        )


@router.get("/current-state")
async def get_current_state(current_user: dict = Depends(get_current_user)):
    """Get the user's current state."""
    try:
        supabase = get_supabase_admin()

        response = (
            supabase.table("user_states")
            .select("*")
            .eq("user_id", current_user["id"])
            .is_("ended_at", "null")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )

        if not response.data:
            return {
                "success": True,
                "data": {
                    "status": "idle",
                    "current_task": None,
                },
            }

        return {
            "success": True,
            "data": response.data[0],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get current state",
        )


@router.post("/state/check-in")
@track(name="daily_check_in_endpoint")
async def daily_check_in(
    request: CheckInRequest,
    current_user: dict = Depends(get_current_user),
):
    """Record daily check-in."""
    try:
        supabase = get_supabase_admin()

        today = date.today().isoformat()

        # Check if already checked in today
        existing = (
            supabase.table("daily_check_ins")
            .select("*")
            .eq("user_id", current_user["id"])
            .eq("date", today)
            .execute()
        )

        check_in_data = {
            "user_id": current_user["id"],
            "date": today,
            "energy_level": request.energy_level,
            "mood": request.mood,
            "sleep_quality": request.sleep_quality,
            "blockers": request.blockers,
            "focus_areas": request.focus_areas,
        }

        if existing.data:
            # Update existing check-in
            response = (
                supabase.table("daily_check_ins")
                .update(check_in_data)
                .eq("id", existing.data[0]["id"])
                .execute()
            )
        else:
            # Create new check-in
            response = supabase.table("daily_check_ins").insert(check_in_data).execute()

        # Trigger CHECKIN_SUBMITTED agent event
        agent_constraints = None
        try:
            checkin_event = CheckInSubmittedEvent(
                user_id=current_user["id"],
                energy_level=request.energy_level,
                mood=request.mood,
                focus_areas=request.focus_areas or [],
                time_available=getattr(request, "time_available", None),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            agent_result = process_agent_event(checkin_event)
            logger.info(f"📝 CHECKIN_SUBMITTED event processed for user {current_user['id']}: {agent_result.get('success')}")
            # Get constraints from agent result
            if agent_result.get('success') and agent_result.get('data'):
                agent_constraints = agent_result['data'].get('selection_constraints')
        except Exception as agent_err:
            logger.warning(f"CHECKIN_SUBMITTED agent event failed (non-blocking): {agent_err}")

        # Generate greeting based on energy
        greeting = "Good morning!"
        if request.energy_level >= 7:
            greeting = f"Good morning! With your energy at {request.energy_level}/10, you're ready for focused work."
        elif request.energy_level >= 4:
            greeting = f"Good morning! Your energy is at {request.energy_level}/10. Consider starting with lighter tasks."
        else:
            greeting = f"Good morning! Energy at {request.energy_level}/10. Take it easy and build momentum gradually."

        return {
            "success": True,
            "data": {
                "check_in": response.data[0] if response.data else check_in_data,
                "greeting": greeting,
                "recommendations": {
                    "working_style_today": (
                        "deep_work_blocks" if request.energy_level >= 7 else "light_tasks"
                    ),
                },
                "agent_constraints": agent_constraints,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in daily_check_in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record check-in",
        )


@router.post("/agents/trigger-debug")
async def trigger_agent_debug(
    event_type: str = "APP_OPEN",
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    DEBUG ONLY: Manually trigger agent orchestrator with a test event.
    
    Used to verify that agent system is wired correctly.
    
    Example:
      POST /api/users/agents/trigger-debug?event_type=APP_OPEN
    """
    user_id = user_id or current_user["id"]
    
    try:
        from agent_mvp.contracts import AppOpenEvent
        
        if event_type == "APP_OPEN":
            event = AppOpenEvent(
                user_id=user_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        elif event_type == "CHECKIN_SUBMITTED":
            event = CheckInSubmittedEvent(
                user_id=user_id,
                energy_level=6,
                focus_areas=["debug"],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        else:
            return {
                "ok": False,
                "error": f"Unknown event_type: {event_type}",
                "supported": ["APP_OPEN", "CHECKIN_SUBMITTED"],
            }
        
        logger.info(f"🤖 DEBUG: AGENTS_INVOKED event_type={event_type} user_id={user_id}")
        result = process_agent_event(event)
        logger.info(f"🤖 DEBUG: AGENTS_DONE event_type={event_type} user_id={user_id}")
        
        return {
            "ok": True,
            "event_type": event_type,
            "user_id": user_id,
            "agent_ran": True,
            "response_keys": list(result.keys()) if isinstance(result, dict) else "N/A",
        }
    except Exception as e:
        logger.error(f"❌ DEBUG agent trigger failed: {str(e)}", exc_info=True)
        return {
            "ok": False,
            "event_type": event_type,
            "user_id": user_id,
            "error": str(e),
        }


@router.get("/state/history")
async def get_state_history(current_user: dict = Depends(get_current_user)):
    """Get the user's state history."""
    try:
        supabase = get_supabase_admin()

        response = (
            supabase.table("daily_check_ins")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("date", desc=True)
            .limit(30)
            .execute()
        )

        return {
            "success": True,
            "data": {"history": response.data or []},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_state_history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get state history",
        )


@router.post("/state/energy-level")
async def update_energy_level(
    energy_level: int,
    current_user: dict = Depends(get_current_user),
):
    """Update current energy level."""
    if not 1 <= energy_level <= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Energy level must be between 1 and 10",
        )

    try:
        supabase = get_supabase_admin()

        # Update or create current state
        response = (
            supabase.table("user_states")
            .upsert(
                {
                    "user_id": current_user["id"],
                    "energy_level": energy_level,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .execute()
        )

        return {
            "success": True,
            "data": {"energy_level": energy_level},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_energy_level: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update energy level",
        )


# ============================================
# FLOWER POINTS ENDPOINTS
# ============================================


@router.get("/flower-points")
async def get_flower_points(current_user: dict = Depends(get_current_user)):
    """Get the current user's flower points balance."""
    try:
        supabase = get_supabase_admin()

        response = (
            supabase.table("user_flower_points")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not response.data:
            # Create default balance if not exists
            new_balance = supabase.table("user_flower_points").insert(
                {"user_id": current_user["id"], "balance": 30}
            ).execute()
            return {
                "success": True,
                "data": {"balance": 30},
            }

        return {
            "success": True,
            "data": {"balance": response.data[0]["balance"]},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_flower_points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get flower points",
        )


@router.post("/flower-points")
async def update_flower_points(
    request: FlowerPointsUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update flower points (earn or spend)."""
    try:
        supabase = get_supabase_admin()

        # Get current balance
        current = (
            supabase.table("user_flower_points")
            .select("balance")
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not current.data:
            # Create with default if not exists
            current_balance = 30
            supabase.table("user_flower_points").insert(
                {"user_id": current_user["id"], "balance": current_balance}
            ).execute()
        else:
            current_balance = current.data[0]["balance"]

        # Calculate new balance
        if request.type == "earned":
            new_balance = current_balance + request.amount
        else:
            if current_balance < request.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient flower points",
                )
            new_balance = current_balance - request.amount

        # Update balance
        supabase.table("user_flower_points").update(
            {"balance": new_balance}
        ).eq("user_id", current_user["id"]).execute()

        # Record transaction
        transaction_data = {
            "user_id": current_user["id"],
            "amount": request.amount,
            "type": request.type,
            "reason": request.reason,
            "project_id": request.project_id,
        }
        supabase.table("flower_transactions").insert(transaction_data).execute()

        return {
            "success": True,
            "data": {"balance": new_balance},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_flower_points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update flower points",
        )


# ============================================
# GRAVEYARD ENDPOINTS
# ============================================


@router.get("/graveyard")
async def get_all_graveyard_meta(current_user: dict = Depends(get_current_user)):
    """Get all graveyard metadata for the user."""
    try:
        supabase = get_supabase_admin()

        # Get all graveyard meta entries
        meta_response = (
            supabase.table("graveyard_meta")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )

        graveyard_items = []
        for meta in meta_response.data or []:
            # Get flowers for this graveyard entry
            flowers_response = (
                supabase.table("graveyard_flowers")
                .select("*")
                .eq("graveyard_meta_id", meta["id"])
                .execute()
            )

            graveyard_items.append({
                "project_id": meta["project_id"],
                "epitaph": meta.get("epitaph"),
                "expiry_date": meta["expiry_date"],
                "flowers": [
                    {
                        "id": f["flower_id"],
                        "name": f["flower_name"],
                        "emoji": f["flower_emoji"],
                        "cost": f["cost"],
                        "days_added": f["days_added"],
                        "placed_at": f.get("placed_at"),
                    }
                    for f in (flowers_response.data or [])
                ],
            })

        return {
            "success": True,
            "data": {"graveyard": graveyard_items},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_all_graveyard_meta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get graveyard data",
        )


@router.put("/graveyard/{project_id}")
async def update_graveyard_meta(
    project_id: str,
    request: GraveyardMetaUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update or create graveyard metadata for a project."""
    try:
        supabase = get_supabase_admin()

        # Verify project belongs to user
        project = (
            supabase.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not project.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check if meta already exists
        existing = (
            supabase.table("graveyard_meta")
            .select("id")
            .eq("user_id", current_user["id"])
            .eq("project_id", project_id)
            .execute()
        )

        meta_data = {
            "user_id": current_user["id"],
            "project_id": project_id,
            "epitaph": request.epitaph,
            "expiry_date": request.expiry_date.isoformat(),
        }

        if existing.data:
            # Update existing
            meta_response = (
                supabase.table("graveyard_meta")
                .update(meta_data)
                .eq("id", existing.data[0]["id"])
                .execute()
            )
            meta_id = existing.data[0]["id"]

            # Delete existing flowers
            supabase.table("graveyard_flowers").delete().eq(
                "graveyard_meta_id", meta_id
            ).execute()
        else:
            # Create new
            meta_response = (
                supabase.table("graveyard_meta")
                .insert(meta_data)
                .execute()
            )
            meta_id = meta_response.data[0]["id"]

        # Insert new flowers
        if request.flowers:
            flower_data = [
                {
                    "graveyard_meta_id": meta_id,
                    "flower_id": f.id,
                    "flower_name": f.name,
                    "flower_emoji": f.emoji,
                    "cost": f.cost,
                    "days_added": f.days_added,
                    "placed_at": f.placed_at.isoformat() if f.placed_at else datetime.now(timezone.utc).isoformat(),
                }
                for f in request.flowers
            ]
            supabase.table("graveyard_flowers").insert(flower_data).execute()

        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "epitaph": request.epitaph,
                "expiry_date": request.expiry_date.isoformat(),
                "flowers": [f.model_dump() for f in request.flowers],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_graveyard_meta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update graveyard data",
        )


@router.delete("/graveyard/{project_id}")
async def delete_graveyard_meta(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete graveyard metadata for a project (e.g., on resurrection)."""
    try:
        supabase = get_supabase_admin()

        # Delete meta (flowers will cascade delete)
        supabase.table("graveyard_meta").delete().eq(
            "user_id", current_user["id"]
        ).eq("project_id", project_id).execute()

        return {
            "success": True,
            "data": {"deleted": True},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_graveyard_meta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete graveyard data",
        )
