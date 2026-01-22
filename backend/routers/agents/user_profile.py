from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel
from collections import defaultdict
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(prefix="/user-profile", tags=["User Profile Agent"])


class AnalyzeRequest(BaseModel):
    include_tasks: bool = True
    include_sessions: bool = True
    include_patterns: bool = True


class UpdatePreferencesRequest(BaseModel):
    work_patterns: Optional[dict] = None
    task_preferences: Optional[dict] = None
    energy_patterns: Optional[dict] = None


@router.post("/analyze")
async def analyze_user_profile(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Analyze user's work patterns and preferences."""
    supabase = get_supabase()
    user_id = current_user["id"]

    analysis = {
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "work_patterns": {},
        "task_preferences": {},
        "energy_patterns": {},
    }

    # Analyze work sessions
    if request.include_sessions:
        sessions = (
            supabase.table("work_sessions")
            .select("start_time, end_time, energy_before, energy_after, interruptions")
            .eq("user_id", user_id)
            .not_.is_("end_time", "null")
            .order("start_time", desc=True)
            .limit(100)
            .execute()
        )

        hourly_activity = defaultdict(int)
        daily_activity = defaultdict(int)
        total_duration = 0
        session_count = 0

        for session in sessions.data or []:
            start = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(session["end_time"].replace("Z", "+00:00"))
            duration = (end - start).total_seconds() / 60

            hourly_activity[start.hour] += duration
            daily_activity[start.strftime("%A")] += duration
            total_duration += duration
            session_count += 1

        # Find peak hours
        peak_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_days = sorted(daily_activity.items(), key=lambda x: x[1], reverse=True)[:3]

        analysis["work_patterns"] = {
            "peak_hours": [f"{h}:00-{h+1}:00" for h, _ in peak_hours],
            "most_productive_days": [d for d, _ in peak_days],
            "average_session_duration": round(total_duration / session_count, 1) if session_count else 0,
            "total_sessions_analyzed": session_count,
        }

    # Analyze task preferences
    if request.include_tasks:
        tasks = (
            supabase.table("tasks")
            .select("priority, estimated_duration, actual_duration, status, tags")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .order("completed_at", desc=True)
            .limit(100)
            .execute()
        )

        priority_completion = defaultdict(int)
        duration_preferences = []
        tag_frequency = defaultdict(int)

        for task in tasks.data or []:
            priority_completion[task.get("priority", "medium")] += 1
            if task.get("actual_duration"):
                duration_preferences.append(task["actual_duration"])
            for tag in (task.get("tags") or []):
                tag_frequency[tag] += 1

        # Preferred task size
        avg_duration = sum(duration_preferences) / len(duration_preferences) if duration_preferences else 30
        if avg_duration < 30:
            preferred_size = "small"
        elif avg_duration < 90:
            preferred_size = "medium"
        else:
            preferred_size = "large"

        analysis["task_preferences"] = {
            "preferred_task_size": preferred_size,
            "average_task_duration": round(avg_duration, 0),
            "priority_distribution": dict(priority_completion),
            "common_tags": [tag for tag, _ in sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)[:5]],
            "tasks_analyzed": len(tasks.data or []),
        }

    # Analyze energy patterns
    if request.include_patterns:
        checkins = (
            supabase.table("daily_check_ins")
            .select("date, energy_level, mood, sleep_quality")
            .eq("user_id", user_id)
            .order("date", desc=True)
            .limit(30)
            .execute()
        )

        energy_levels = [c["energy_level"] for c in (checkins.data or []) if c.get("energy_level")]
        mood_counts = defaultdict(int)
        sleep_quality = []

        for checkin in checkins.data or []:
            if checkin.get("mood"):
                mood_counts[checkin["mood"]] += 1
            if checkin.get("sleep_quality"):
                sleep_quality.append(checkin["sleep_quality"])

        analysis["energy_patterns"] = {
            "average_energy": round(sum(energy_levels) / len(energy_levels), 1) if energy_levels else None,
            "energy_variance": round(
                sum((e - sum(energy_levels) / len(energy_levels)) ** 2 for e in energy_levels) / len(energy_levels), 2
            ) if len(energy_levels) > 1 else 0,
            "common_moods": [m for m, _ in sorted(mood_counts.items(), key=lambda x: x[1], reverse=True)[:3]],
            "average_sleep_quality": round(sum(sleep_quality) / len(sleep_quality), 1) if sleep_quality else None,
            "days_analyzed": len(checkins.data or []),
        }

    # Store analysis for future reference
    supabase.table("ai_learning_data").insert({
        "user_id": user_id,
        "agent_type": "user_profile",
        "data": analysis,
    }).execute()

    return {
        "success": True,
        "data": analysis,
    }


@router.get("/insights")
async def get_profile_insights(
    current_user: dict = Depends(get_current_user),
):
    """Get insights based on user profile analysis."""
    supabase = get_supabase()

    # Get latest analysis
    analysis = (
        supabase.table("ai_learning_data")
        .select("data, created_at")
        .eq("user_id", current_user["id"])
        .eq("agent_type", "user_profile")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not analysis.data:
        return {
            "success": True,
            "data": {
                "message": "No profile analysis available. Run /analyze first.",
                "insights": [],
            },
        }

    data = analysis.data[0]["data"]
    insights = []

    # Generate insights from work patterns
    work_patterns = data.get("work_patterns", {})
    if work_patterns.get("peak_hours"):
        insights.append({
            "type": "productivity",
            "title": "Peak Productivity Hours",
            "description": f"You're most productive during {', '.join(work_patterns['peak_hours'])}",
            "recommendation": "Schedule your most important tasks during these hours",
        })

    if work_patterns.get("average_session_duration"):
        duration = work_patterns["average_session_duration"]
        if duration < 25:
            insights.append({
                "type": "focus",
                "title": "Short Sessions",
                "description": f"Your average session is {int(duration)} minutes",
                "recommendation": "Try extending focus sessions to 25-50 minutes for deeper work",
            })
        elif duration > 90:
            insights.append({
                "type": "wellness",
                "title": "Long Sessions",
                "description": f"Your average session is {int(duration)} minutes",
                "recommendation": "Consider taking breaks every 60-90 minutes",
            })

    # Generate insights from task preferences
    task_prefs = data.get("task_preferences", {})
    if task_prefs.get("preferred_task_size"):
        size = task_prefs["preferred_task_size"]
        insights.append({
            "type": "task_management",
            "title": f"Task Size Preference: {size.capitalize()}",
            "description": f"You tend to complete {size} tasks (avg {int(task_prefs.get('average_task_duration', 30))} min)",
            "recommendation": f"Break larger tasks into {size}-sized chunks for better progress",
        })

    # Generate insights from energy patterns
    energy_patterns = data.get("energy_patterns", {})
    if energy_patterns.get("average_energy"):
        avg_energy = energy_patterns["average_energy"]
        if avg_energy < 5:
            insights.append({
                "type": "wellness",
                "title": "Energy Levels",
                "description": f"Your average energy is {avg_energy}/10",
                "recommendation": "Consider reviewing sleep, exercise, and breaks",
            })
        elif avg_energy >= 7:
            insights.append({
                "type": "wellness",
                "title": "Great Energy",
                "description": f"Your average energy is {avg_energy}/10",
                "recommendation": "Keep up your healthy habits!",
            })

    return {
        "success": True,
        "data": {
            "insights": insights,
            "last_analyzed": analysis.data[0]["created_at"],
            "profile_summary": {
                "peak_hours": work_patterns.get("peak_hours", []),
                "preferred_task_size": task_prefs.get("preferred_task_size"),
                "average_energy": energy_patterns.get("average_energy"),
            },
        },
    }


@router.post("/update-preferences")
async def update_preferences(
    request: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update user preferences based on learned patterns."""
    supabase = get_supabase()

    # Get current preferences
    prefs = (
        supabase.table("user_preferences")
        .select("*")
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    update_data = {}

    if request.work_patterns:
        current_work = prefs.data.get("work_style", {}) if prefs.data else {}
        update_data["work_style"] = {**current_work, **request.work_patterns}

    if request.energy_patterns:
        current_energy = prefs.data.get("energy_patterns", {}) if prefs.data else {}
        update_data["energy_patterns"] = {**current_energy, **request.energy_patterns}

    if not update_data:
        return {
            "success": True,
            "data": {"message": "No updates provided"},
        }

    if prefs.data:
        response = (
            supabase.table("user_preferences")
            .update(update_data)
            .eq("user_id", current_user["id"])
            .execute()
        )
    else:
        response = (
            supabase.table("user_preferences")
            .insert({
                "user_id": current_user["id"],
                **update_data,
            })
            .execute()
        )

    return {
        "success": True,
        "data": {
            "updated": True,
            "preferences": response.data[0] if response.data else update_data,
        },
    }
