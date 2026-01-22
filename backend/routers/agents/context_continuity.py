from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, timedelta, date
from typing import Optional
from pydantic import BaseModel
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(prefix="/context", tags=["Context Continuity"])


class SaveStateRequest(BaseModel):
    current_task_id: Optional[str] = None
    notes: Optional[str] = None
    context_data: Optional[dict] = None


@router.get("/session-summary")
async def get_session_summary(
    current_user: dict = Depends(get_current_user),
):
    """Get a summary of the current/last work session."""
    supabase = get_supabase()
    now = datetime.now(timezone.utc)
    today = date.today()

    # Get recent work sessions
    sessions = (
        supabase.table("work_sessions")
        .select("*, tasks(id, title, status, project_id, projects(name))")
        .eq("user_id", current_user["id"])
        .order("start_time", desc=True)
        .limit(5)
        .execute()
    )

    # Get today's completed tasks
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    completed_today = (
        supabase.table("tasks")
        .select("id, title, completed_at")
        .eq("user_id", current_user["id"])
        .eq("status", "completed")
        .gte("completed_at", today_start.isoformat())
        .order("completed_at", desc=True)
        .execute()
    )

    # Build session summary
    recent_sessions = []
    total_focus_time = 0

    for session in sessions.data or []:
        start = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(session["end_time"].replace("Z", "+00:00")) if session.get("end_time") else now

        duration = int((end - start).total_seconds() / 60)
        total_focus_time += duration

        task = session.get("tasks", {})
        recent_sessions.append({
            "task_id": task.get("id"),
            "task_title": task.get("title"),
            "project_name": task.get("projects", {}).get("name") if task.get("projects") else None,
            "duration_minutes": duration,
            "start_time": session["start_time"],
            "end_time": session.get("end_time"),
            "is_active": session.get("end_time") is None,
        })

    # Current active session
    active_session = next((s for s in recent_sessions if s["is_active"]), None)

    # Generate summary message
    if active_session:
        summary = f"You're currently working on '{active_session['task_title']}' for {active_session['duration_minutes']} minutes."
    elif recent_sessions:
        last = recent_sessions[0]
        summary = f"Your last session was on '{last['task_title']}' ({last['duration_minutes']} minutes)."
    else:
        summary = "No recent work sessions found."

    return {
        "success": True,
        "data": {
            "summary": summary,
            "active_session": active_session,
            "recent_sessions": recent_sessions[:5],
            "today_stats": {
                "total_focus_time": total_focus_time,
                "tasks_completed": len(completed_today.data or []),
                "completed_tasks": [
                    {"id": t["id"], "title": t["title"]}
                    for t in (completed_today.data or [])[:5]
                ],
            },
        },
    }


@router.post("/save-state")
async def save_context_state(
    request: SaveStateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Save the current context state for later resumption."""
    supabase = get_supabase()
    today = date.today().isoformat()

    # Get current task info if provided
    task_info = None
    if request.current_task_id:
        task = (
            supabase.table("tasks")
            .select("id, title, status, project_id")
            .eq("id", request.current_task_id)
            .eq("user_id", current_user["id"])
            .single()
            .execute()
        )
        if task.data:
            task_info = task.data

    # Build context
    context = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "current_task": task_info,
        "notes": request.notes,
        "custom_data": request.context_data,
    }

    # Upsert session context
    existing = (
        supabase.table("session_contexts")
        .select("id")
        .eq("user_id", current_user["id"])
        .eq("session_date", today)
        .single()
        .execute()
    )

    if existing.data:
        response = (
            supabase.table("session_contexts")
            .update({
                "context_data": context,
                "last_task_id": request.current_task_id,
            })
            .eq("id", existing.data["id"])
            .execute()
        )
    else:
        response = (
            supabase.table("session_contexts")
            .insert({
                "user_id": current_user["id"],
                "session_date": today,
                "context_data": context,
                "last_task_id": request.current_task_id,
            })
            .execute()
        )

    return {
        "success": True,
        "data": {
            "saved": True,
            "context_summary": {
                "task": task_info["title"] if task_info else None,
                "notes": request.notes,
                "saved_at": context["saved_at"],
            },
        },
    }


@router.get("/next-steps")
async def get_next_steps(
    current_user: dict = Depends(get_current_user),
):
    """Get suggested next steps based on context."""
    supabase = get_supabase()
    today = date.today().isoformat()

    # Get saved context
    context = (
        supabase.table("session_contexts")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("session_date", desc=True)
        .limit(1)
        .execute()
    )

    # Get incomplete tasks
    tasks = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .in_("status", ["in_progress", "paused", "todo"])
        .order("updated_at", desc=True)
        .limit(10)
        .execute()
    )

    next_steps = []

    # Priority 1: Resume last task
    saved_context = context.data[0] if context.data else None
    if saved_context and saved_context.get("last_task_id"):
        last_task = next(
            (t for t in (tasks.data or []) if t["id"] == saved_context["last_task_id"]),
            None
        )
        if last_task and last_task["status"] != "completed":
            next_steps.append({
                "type": "resume",
                "priority": 1,
                "title": f"Resume: {last_task['title']}",
                "description": "Continue where you left off",
                "task_id": last_task["id"],
                "task": {
                    "title": last_task["title"],
                    "project_name": last_task.get("projects", {}).get("name") if last_task.get("projects") else None,
                    "status": last_task["status"],
                },
            })

    # Priority 2: In-progress tasks
    in_progress = [t for t in (tasks.data or []) if t["status"] == "in_progress"]
    for task in in_progress[:2]:
        if not any(s.get("task_id") == task["id"] for s in next_steps):
            next_steps.append({
                "type": "continue",
                "priority": 2,
                "title": f"Continue: {task['title']}",
                "description": "Task in progress",
                "task_id": task["id"],
                "task": {
                    "title": task["title"],
                    "project_name": task.get("projects", {}).get("name") if task.get("projects") else None,
                },
            })

    # Priority 3: High priority tasks
    high_priority = [
        t for t in (tasks.data or [])
        if t.get("priority") in ["urgent", "high"] and t["status"] == "todo"
    ]
    for task in high_priority[:2]:
        if not any(s.get("task_id") == task["id"] for s in next_steps):
            next_steps.append({
                "type": "start",
                "priority": 3,
                "title": f"Start: {task['title']}",
                "description": f"{task['priority'].capitalize()} priority",
                "task_id": task["id"],
                "task": {
                    "title": task["title"],
                    "priority": task["priority"],
                    "project_name": task.get("projects", {}).get("name") if task.get("projects") else None,
                },
            })

    # Context notes
    context_notes = None
    if saved_context and saved_context.get("context_data", {}).get("notes"):
        context_notes = saved_context["context_data"]["notes"]

    return {
        "success": True,
        "data": {
            "next_steps": next_steps[:5],
            "context_notes": context_notes,
            "last_session_date": saved_context["session_date"] if saved_context else None,
        },
    }


@router.get("/unfinished-work")
async def get_unfinished_work(
    current_user: dict = Depends(get_current_user),
):
    """Get all unfinished work items."""
    supabase = get_supabase()

    # Get in-progress and paused tasks
    unfinished = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .in_("status", ["in_progress", "paused", "blocked"])
        .order("updated_at", desc=True)
        .execute()
    )

    # Get tasks started but not completed with sessions
    recent_sessions = (
        supabase.table("work_sessions")
        .select("task_id, start_time, end_time")
        .eq("user_id", current_user["id"])
        .order("start_time", desc=True)
        .limit(20)
        .execute()
    )

    # Organize unfinished work
    in_progress = []
    paused = []
    blocked = []

    for task in unfinished.data or []:
        task_info = {
            "id": task["id"],
            "title": task["title"],
            "project_name": task.get("projects", {}).get("name") if task.get("projects") else None,
            "priority": task["priority"],
            "started_at": task.get("started_at"),
            "estimated_duration": task.get("estimated_duration"),
        }

        if task["status"] == "in_progress":
            in_progress.append(task_info)
        elif task["status"] == "paused":
            paused.append(task_info)
        elif task["status"] == "blocked":
            blocked.append(task_info)

    # Calculate time invested in unfinished work
    task_ids = [t["id"] for t in (unfinished.data or [])]
    sessions_for_tasks = [s for s in (recent_sessions.data or []) if s["task_id"] in task_ids]

    total_invested = 0
    for session in sessions_for_tasks:
        if session.get("end_time"):
            start = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(session["end_time"].replace("Z", "+00:00"))
            total_invested += int((end - start).total_seconds() / 60)

    return {
        "success": True,
        "data": {
            "summary": {
                "total_unfinished": len(unfinished.data or []),
                "time_invested_minutes": total_invested,
            },
            "in_progress": in_progress,
            "paused": paused,
            "blocked": blocked,
            "recommendation": get_unfinished_recommendation(in_progress, paused, blocked),
        },
    }


def get_unfinished_recommendation(in_progress: list, paused: list, blocked: list) -> str:
    """Generate recommendation based on unfinished work."""
    total = len(in_progress) + len(paused) + len(blocked)

    if total == 0:
        return "All caught up! Ready to start something new."

    if blocked:
        return f"You have {len(blocked)} blocked task(s). Consider resolving blockers first."

    if len(in_progress) > 2:
        return "Multiple tasks in progress. Consider focusing on one at a time."

    if in_progress:
        return f"Continue with '{in_progress[0]['title']}' to maintain momentum."

    if paused:
        return f"Resume '{paused[0]['title']}' - you've already made progress on it."

    return "Review your unfinished work and prioritize."
