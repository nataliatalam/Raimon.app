from fastapi import APIRouter, HTTPException, status, Depends
from models.user import (
    UserProfile,
    UserProfileUpdate,
    UserPreferencesUpdate,
    OnboardingUpdate,
    CheckInRequest,
)
from core.supabase import get_supabase
from core.security import get_current_user
from datetime import datetime, timezone, date

router = APIRouter(prefix="/api/users", tags=["Users"])


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
    supabase = get_supabase()

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


@router.patch("/preferences")
async def update_preferences(
    request: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update user preferences."""
    supabase = get_supabase()

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
    supabase = get_supabase()

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


@router.get("/current-state")
async def get_current_state(current_user: dict = Depends(get_current_user)):
    """Get the user's current state."""
    supabase = get_supabase()

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


@router.post("/state/check-in")
async def daily_check_in(
    request: CheckInRequest,
    current_user: dict = Depends(get_current_user),
):
    """Record daily check-in."""
    supabase = get_supabase()

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
        },
    }


@router.get("/state/history")
async def get_state_history(current_user: dict = Depends(get_current_user)):
    """Get the user's state history."""
    supabase = get_supabase()

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

    supabase = get_supabase()

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
