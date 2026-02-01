from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, date
from typing import Optional, List
from pydantic import BaseModel, Field
from core.supabase import get_supabase
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/state-adapter", tags=["Daily State Adapter"])


class StateCheckInRequest(BaseModel):
    energy_level: int = Field(..., ge=1, le=10)
    mood: str
    sleep_quality: Optional[int] = Field(default=None, ge=1, le=10)
    stress_level: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = None


@router.post("/check-in")
async def state_check_in(
    request: StateCheckInRequest,
    current_user: dict = Depends(get_current_user),
):
    """Process a daily state check-in and provide adaptive recommendations."""
    try:
        supabase = get_supabase()
        today = date.today().isoformat()

        # Save or update check-in
        existing = (
            supabase.table("daily_check_ins")
            .select("id")
            .eq("user_id", current_user["id"])
            .eq("date", today)
            .execute()
        )

        checkin_data = {
            "user_id": current_user["id"],
            "date": today,
            "energy_level": request.energy_level,
            "mood": request.mood,
            "sleep_quality": request.sleep_quality,
        }

        if existing.data:
            supabase.table("daily_check_ins").update(checkin_data).eq("id", existing.data[0]["id"]).execute()
        else:
            supabase.table("daily_check_ins").insert(checkin_data).execute()

        # Generate adaptive recommendations
        recommendations = generate_state_recommendations(
            request.energy_level,
            request.mood,
            request.sleep_quality,
            request.stress_level,
        )

        # Update streak
        update_checkin_streak(supabase, current_user["id"])

        return {
            "success": True,
            "data": {
                "check_in_recorded": True,
                "state_summary": {
                    "energy_level": request.energy_level,
                    "mood": request.mood,
                    "overall_readiness": calculate_readiness(request.energy_level, request.mood),
                },
                "recommendations": recommendations,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in state_check_in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process state check-in",
        )


def calculate_readiness(energy: int, mood: str) -> str:
    """Calculate overall work readiness."""
    mood_scores = {
        "energized": 3, "focused": 3, "calm": 2, "neutral": 1,
        "tired": -1, "stressed": -1, "anxious": -2, "frustrated": -2,
    }
    mood_score = mood_scores.get(mood.lower(), 0)
    total = energy + mood_score

    if total >= 10:
        return "high"
    elif total >= 6:
        return "moderate"
    else:
        return "low"


def generate_state_recommendations(energy: int, mood: str, sleep: Optional[int], stress: Optional[int]) -> dict:
    """Generate recommendations based on current state."""
    recommendations = {
        "work_style": "normal",
        "suggested_task_types": [],
        "breaks": {"frequency": "normal", "duration": 15},
        "tips": [],
    }

    # Energy-based recommendations
    if energy >= 8:
        recommendations["work_style"] = "deep_focus"
        recommendations["suggested_task_types"] = ["complex", "creative", "challenging"]
        recommendations["tips"].append("High energy - tackle your most challenging tasks now")
    elif energy >= 5:
        recommendations["work_style"] = "balanced"
        recommendations["suggested_task_types"] = ["moderate", "routine", "collaborative"]
        recommendations["tips"].append("Steady energy - good for balanced workload")
    else:
        recommendations["work_style"] = "light"
        recommendations["suggested_task_types"] = ["simple", "administrative", "quick-wins"]
        recommendations["breaks"]["frequency"] = "frequent"
        recommendations["breaks"]["duration"] = 10
        recommendations["tips"].append("Lower energy - focus on quick wins and take frequent breaks")

    # Mood-based adjustments
    if mood.lower() in ["stressed", "anxious"]:
        recommendations["tips"].append("Consider starting with a calming routine or simple task")
        recommendations["breaks"]["frequency"] = "frequent"
    elif mood.lower() in ["focused", "energized"]:
        recommendations["tips"].append("Great mindset for productivity - minimize distractions")

    # Sleep-based adjustments
    if sleep and sleep < 5:
        recommendations["tips"].append("Low sleep quality - prioritize essential tasks only")
        recommendations["work_style"] = "light"

    return recommendations


def update_checkin_streak(supabase, user_id: str):
    """Update the daily check-in streak."""
    streak = (
        supabase.table("streaks")
        .select("*")
        .eq("user_id", user_id)
        .eq("streak_type", "daily_check_in")
        .execute()
    )

    today = date.today()

    if streak.data:
        streak_data = streak.data[0]
        last_date = datetime.fromisoformat(streak_data["last_activity_date"]).date() if streak_data.get("last_activity_date") else None

        if last_date == today:
            return  # Already counted today

        if last_date == today - timedelta(days=1):
            # Continue streak
            new_count = streak_data["current_count"] + 1
            longest = max(streak_data.get("longest_count", 0), new_count)
            supabase.table("streaks").update({
                "current_count": new_count,
                "longest_count": longest,
                "last_activity_date": today.isoformat(),
            }).eq("id", streak_data["id"]).execute()
        else:
            # Reset streak
            supabase.table("streaks").update({
                "current_count": 1,
                "last_activity_date": today.isoformat(),
            }).eq("id", streak_data["id"]).execute()
    else:
        # Create new streak
        supabase.table("streaks").insert({
            "user_id": user_id,
            "streak_type": "daily_check_in",
            "current_count": 1,
            "longest_count": 1,
            "last_activity_date": today.isoformat(),
        }).execute()


@router.get("/energy-assessment")
async def get_energy_assessment(
    current_user: dict = Depends(get_current_user),
):
    """Get energy assessment and patterns."""
    try:
        supabase = get_supabase()

        # Get recent check-ins
        checkins = (
            supabase.table("daily_check_ins")
            .select("date, energy_level, mood, sleep_quality")
            .eq("user_id", current_user["id"])
            .order("date", desc=True)
            .limit(14)
            .execute()
        )

        data = checkins.data or []

        if not data:
            return {
                "success": True,
                "data": {
                    "message": "No check-in data available yet",
                    "recommendation": "Start with a daily check-in to track your energy patterns",
                },
            }

        # Calculate averages
        energy_levels = [c["energy_level"] for c in data if c.get("energy_level")]
        avg_energy = sum(energy_levels) / len(energy_levels) if energy_levels else 5

        # Find patterns
        high_energy_days = [c for c in data if c.get("energy_level", 0) >= 7]
        low_energy_days = [c for c in data if c.get("energy_level", 0) <= 4]

        assessment = {
            "current_energy": data[0].get("energy_level") if data else None,
            "average_energy": round(avg_energy, 1),
            "trend": "stable",
            "patterns": {
                "high_energy_frequency": f"{len(high_energy_days)}/{len(data)} days",
                "low_energy_frequency": f"{len(low_energy_days)}/{len(data)} days",
            },
            "recommendations": [],
        }

        # Determine trend
        if len(energy_levels) >= 3:
            recent = sum(energy_levels[:3]) / 3
            older = sum(energy_levels[-3:]) / 3
            if recent > older + 1:
                assessment["trend"] = "improving"
            elif recent < older - 1:
                assessment["trend"] = "declining"

        # Add recommendations
        if avg_energy < 5:
            assessment["recommendations"].append("Consider reviewing your sleep and stress management")
        if len(low_energy_days) > len(data) / 2:
            assessment["recommendations"].append("Many low-energy days - consider lighter workloads")

        return {
            "success": True,
            "data": assessment,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_energy_assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get energy assessment",
        )


@router.get("/task-recommendations")
async def get_state_based_recommendations(
    current_user: dict = Depends(get_current_user),
):
    """Get task recommendations based on current state."""
    try:
        supabase = get_supabase()
        today = date.today().isoformat()

        # Get today's check-in
        checkin = (
            supabase.table("daily_check_ins")
            .select("*")
            .eq("user_id", current_user["id"])
            .eq("date", today)
            .execute()
        )

        if not checkin.data:
            return {
                "success": True,
                "data": {
                    "message": "Please complete your daily check-in first",
                    "check_in_required": True,
                },
            }

        checkin_record = checkin.data[0]
        energy = checkin_record.get("energy_level", 5)
        mood = checkin_record.get("mood", "neutral")

        # Get tasks
        tasks = (
            supabase.table("tasks")
            .select("*, projects(name)")
            .eq("user_id", current_user["id"])
            .in_("status", ["todo", "in_progress", "paused"])
            .execute()
        )

        # Categorize tasks by complexity
        recommended = []
        for task in tasks.data or []:
            duration = task.get("estimated_duration") or 30
            priority = task.get("priority", "medium")

            # Calculate fit score based on energy
            fit_score = 0
            if energy >= 7:
                # High energy - prefer complex tasks
                if duration >= 60 or priority in ["urgent", "high"]:
                    fit_score = 10
                else:
                    fit_score = 5
            elif energy >= 4:
                # Medium energy - prefer moderate tasks
                if 30 <= duration <= 60:
                    fit_score = 10
                else:
                    fit_score = 6
            else:
                # Low energy - prefer simple tasks
                if duration <= 30:
                    fit_score = 10
                else:
                    fit_score = 3

            recommended.append({
                "task_id": task["id"],
                "title": task["title"],
                "project_name": task.get("projects", {}).get("name") if task.get("projects") else None,
                "priority": priority,
                "estimated_duration": duration,
                "fit_score": fit_score,
                "fit_reason": get_fit_reason(energy, duration, priority),
            })

        recommended.sort(key=lambda x: x["fit_score"], reverse=True)

        return {
            "success": True,
            "data": {
                "current_state": {
                    "energy_level": energy,
                    "mood": mood,
                },
                "recommended_tasks": recommended[:5],
                "work_style": "deep_focus" if energy >= 7 else "light" if energy <= 4 else "balanced",
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_state_based_recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get state-based recommendations",
        )


def get_fit_reason(energy: int, duration: int, priority: str) -> str:
    """Get explanation for task fit."""
    if energy >= 7:
        if duration >= 60 or priority in ["urgent", "high"]:
            return "High energy - great for challenging work"
        return "Could handle more complex tasks"
    elif energy >= 4:
        if 30 <= duration <= 60:
            return "Moderate task matches your energy"
        return "Might want to adjust scope"
    else:
        if duration <= 30:
            return "Quick win for lower energy"
        return "Consider breaking into smaller tasks"
