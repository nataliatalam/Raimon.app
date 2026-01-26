from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, timedelta, date
from typing import Optional
from core.supabase import get_supabase
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def get_greeting(hour: int, user_name: str, streak: int = 0) -> str:
    """Generate a personalized greeting based on time of day."""
    name = user_name or "there"

    if 5 <= hour < 12:
        base = f"Good morning, {name}!"
    elif 12 <= hour < 17:
        base = f"Good afternoon, {name}!"
    elif 17 <= hour < 21:
        base = f"Good evening, {name}!"
    else:
        base = f"Hey {name}, burning the midnight oil?"

    if streak >= 7:
        base += f" You're on a {streak}-day streak! Keep it up!"
    elif streak >= 3:
        base += f" {streak} days strong!"

    return base


@router.get("/summary")
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
):
    """Get the complete dashboard summary."""
    try:
        supabase = get_supabase()
        user_id = current_user["id"]
        today = date.today()
        now = datetime.now(timezone.utc)

        # Get current active task/session
        active_session = (
            supabase.table("work_sessions")
            .select("*, tasks(id, title, project_id, estimated_duration)")
            .eq("user_id", user_id)
            .is_("end_time", "null")
            .order("start_time", desc=True)
            .limit(1)
            .execute()
        )

        current_task = None
        if active_session.data:
            session = active_session.data[0]
            task = session.get("tasks", {})
            start_time = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
            elapsed = int((now - start_time).total_seconds() / 60)

            current_task = {
                "id": task.get("id"),
                "title": task.get("title"),
                "elapsed_time": elapsed,
                "estimated_remaining": max(0, (task.get("estimated_duration") or 30) - elapsed),
                "session_id": session["id"],
            }

        # Get today's check-in
        checkin = (
            supabase.table("daily_check_ins")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", today.isoformat())
            .execute()
        )

        checkin_data = checkin.data[0] if checkin.data else None
        energy_level = checkin_data.get("energy_level") if checkin_data else None

        # Get today's task stats
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)

        # Tasks completed today
        completed_today = (
            supabase.table("tasks")
            .select("id")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .gte("completed_at", today_start.isoformat())
            .lt("completed_at", today_end.isoformat())
            .execute()
        )

        # Tasks remaining (due today or in progress)
        tasks_remaining = (
            supabase.table("tasks")
            .select("id")
            .eq("user_id", user_id)
            .in_("status", ["todo", "in_progress", "paused"])
            .execute()
        )

        # Focus time today (from work sessions)
        sessions_today = (
            supabase.table("work_sessions")
            .select("start_time, end_time")
            .eq("user_id", user_id)
            .gte("start_time", today_start.isoformat())
            .execute()
        )

        focus_time = 0
        for session in sessions_today.data or []:
            start = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(session["end_time"].replace("Z", "+00:00")) if session.get("end_time") else now
            focus_time += int((end - start).total_seconds() / 60)

        # Get active projects with progress
        projects = (
            supabase.table("projects")
            .select("id, name, status, priority")
            .eq("user_id", user_id)
            .eq("status", "active")
            .order("priority", desc=True)
            .limit(5)
            .execute()
        )

        projects_with_progress = []
        for project in projects.data or []:
            # Get task counts for this project
            project_tasks = (
                supabase.table("tasks")
                .select("status")
                .eq("project_id", project["id"])
                .execute()
            )
            total = len(project_tasks.data or [])
            completed = len([t for t in (project_tasks.data or []) if t["status"] == "completed"])
            progress = int((completed / total * 100) if total > 0 else 0)

            projects_with_progress.append({
                "id": project["id"],
                "name": project["name"],
                "progress": progress,
                "status": "on_track" if progress >= 50 else "needs_attention",
            })

        # Get streaks
        streaks = (
            supabase.table("streaks")
            .select("streak_type, current_count")
            .eq("user_id", user_id)
            .execute()
        )

        streak_data = {}
        for streak in streaks.data or []:
            streak_data[streak["streak_type"]] = streak["current_count"]

        daily_streak = streak_data.get("daily_check_in", 0)

        # Generate greeting
        current_hour = now.hour
        greeting = get_greeting(current_hour, current_user.get("name"), daily_streak)

        # Get recent insights (placeholder for AI-generated insights)
        insights = []
        if focus_time > 120:
            insights.append({
                "type": "productivity_tip",
                "message": f"Great focus today! You've been productive for {focus_time} minutes.",
            })
        if energy_level and energy_level >= 7:
            insights.append({
                "type": "energy_tip",
                "message": "Your energy is high - perfect time for challenging tasks!",
            })

        return {
            "success": True,
            "data": {
                "greeting": greeting,
                "current_state": {
                    "status": "working" if current_task else "idle",
                    "current_task": current_task,
                },
                "today": {
                    "tasks_completed": len(completed_today.data or []),
                    "tasks_remaining": len(tasks_remaining.data or []),
                    "focus_time": focus_time,
                    "energy_level": energy_level,
                },
                "projects": projects_with_progress,
                "insights": insights,
                "streaks": streak_data,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_dashboard_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard summary",
        )


@router.get("/current-task")
async def get_current_task(
    current_user: dict = Depends(get_current_user),
):
    """Get the currently active task."""
    supabase = get_supabase()
    now = datetime.now(timezone.utc)

    active_session = (
        supabase.table("work_sessions")
        .select("*, tasks(*)")
        .eq("user_id", current_user["id"])
        .is_("end_time", "null")
        .order("start_time", desc=True)
        .limit(1)
        .execute()
    )

    if not active_session.data:
        return {
            "success": True,
            "data": {
                "current_task": None,
                "message": "No task in progress",
            },
        }

    session = active_session.data[0]
    task = session.get("tasks", {})
    start_time = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
    elapsed = int((now - start_time).total_seconds() / 60)

    return {
        "success": True,
        "data": {
            "current_task": {
                "id": task.get("id"),
                "title": task.get("title"),
                "description": task.get("description"),
                "project_id": task.get("project_id"),
                "priority": task.get("priority"),
                "status": task.get("status"),
                "elapsed_time": elapsed,
                "estimated_duration": task.get("estimated_duration"),
                "estimated_remaining": max(0, (task.get("estimated_duration") or 30) - elapsed),
            },
            "session": {
                "id": session["id"],
                "start_time": session["start_time"],
                "energy_before": session.get("energy_before"),
                "interruptions": session.get("interruptions", 0),
            },
        },
    }


@router.get("/today-tasks")
async def get_today_tasks(
    current_user: dict = Depends(get_current_user),
):
    """Get all tasks for today (due today or in progress)."""
    supabase = get_supabase()
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)

    # Get tasks due today
    due_today = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .gte("deadline", today_start.isoformat())
        .lt("deadline", today_end.isoformat())
        .execute()
    )

    # Get in-progress tasks
    in_progress = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .in_("status", ["in_progress", "paused"])
        .execute()
    )

    # Get tasks completed today
    completed_today = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .eq("status", "completed")
        .gte("completed_at", today_start.isoformat())
        .lt("completed_at", today_end.isoformat())
        .execute()
    )

    # Combine and deduplicate
    all_tasks = {}
    for task in (due_today.data or []) + (in_progress.data or []):
        if task["id"] not in all_tasks:
            all_tasks[task["id"]] = {
                **task,
                "project_name": task.get("projects", {}).get("name") if task.get("projects") else None,
            }
            del all_tasks[task["id"]]["projects"]

    pending_tasks = list(all_tasks.values())
    completed = [
        {**t, "project_name": t.get("projects", {}).get("name") if t.get("projects") else None}
        for t in (completed_today.data or [])
    ]
    for t in completed:
        if "projects" in t:
            del t["projects"]

    # Sort by priority
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    pending_tasks.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))

    return {
        "success": True,
        "data": {
            "pending": pending_tasks,
            "completed": completed,
            "summary": {
                "total_pending": len(pending_tasks),
                "total_completed": len(completed),
            },
        },
    }


@router.get("/greetings")
async def get_greeting_message(
    current_user: dict = Depends(get_current_user),
):
    """Get a personalized greeting message."""
    supabase = get_supabase()
    now = datetime.now(timezone.utc)
    today = date.today()

    # Get streak
    streak = (
        supabase.table("streaks")
        .select("current_count")
        .eq("user_id", current_user["id"])
        .eq("streak_type", "daily_check_in")
        .execute()
    )

    streak_count = streak.data[0].get("current_count", 0) if streak.data else 0

    # Get today's check-in
    checkin = (
        supabase.table("daily_check_ins")
        .select("energy_level, mood")
        .eq("user_id", current_user["id"])
        .eq("date", today.isoformat())
        .execute()
    )

    # Get completed tasks count
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    completed = (
        supabase.table("tasks")
        .select("id")
        .eq("user_id", current_user["id"])
        .eq("status", "completed")
        .gte("completed_at", today_start.isoformat())
        .execute()
    )

    greeting = get_greeting(now.hour, current_user.get("name"), streak_count)

    # Add contextual message
    checkin_data = checkin.data[0] if checkin.data else None
    messages = []
    if checkin_data:
        energy = checkin_data.get("energy_level", 5)
        if energy >= 8:
            messages.append("You're full of energy today!")
        elif energy <= 3:
            messages.append("Take it easy today, focus on quick wins.")

    completed_count = len(completed.data or [])
    if completed_count >= 5:
        messages.append(f"Amazing! You've completed {completed_count} tasks today!")
    elif completed_count >= 1:
        messages.append(f"You've completed {completed_count} task{'s' if completed_count > 1 else ''} so far.")

    return {
        "success": True,
        "data": {
            "greeting": greeting,
            "messages": messages,
            "streak": streak_count,
            "checked_in": checkin_data is not None,
        },
    }
