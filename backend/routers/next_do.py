from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from models.next_do import NextDoFeedback, NextDoSkip
from core.supabase import get_supabase_admin
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/next-do", tags=["Next Do"])


def calculate_task_score(task: dict, user_state: dict, current_hour: int) -> tuple[float, List[str]]:
    """
    Calculate priority score for a task based on multiple factors.
    Returns (score, list of reasons).
    """
    score = 0.0
    reasons = []

    energy_level = user_state.get("energy_level") or 5

    # 1. Deadline urgency (0-40 points)
    if task.get("deadline"):
        try:
            deadline = datetime.fromisoformat(task["deadline"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            hours_until = (deadline - now).total_seconds() / 3600

            if hours_until < 0:
                score += 45  # Overdue - highest priority
                reasons.append("Task is overdue!")
            elif hours_until < 4:
                score += 40
                reasons.append("Due within 4 hours")
            elif hours_until < 24:
                score += 30
                reasons.append("Due today")
            elif hours_until < 72:
                score += 20
                reasons.append("Due within 3 days")
            elif hours_until < 168:
                score += 10
                reasons.append("Due this week")
        except (ValueError, TypeError):
            pass

    # 2. Priority weight (0-30 points)
    priority_scores = {"urgent": 30, "high": 22, "medium": 12, "low": 5}
    priority = task.get("priority", "medium")
    priority_score = priority_scores.get(priority, 12)
    score += priority_score
    if priority in ["urgent", "high"]:
        reasons.append(f"{priority.capitalize()} priority task")

    # 3. Energy match (0-20 points)
    estimated_duration = task.get("estimated_duration") or 30
    # Longer/harder tasks need more energy
    task_energy_required = min(10, max(1, estimated_duration // 15 + 3))

    if energy_level >= 7:
        # High energy - prefer challenging tasks
        if task_energy_required >= 6:
            score += 20
            reasons.append("Good match for your high energy")
        else:
            score += 10
    elif energy_level >= 4:
        # Medium energy - prefer medium tasks
        if 4 <= task_energy_required <= 7:
            score += 18
            reasons.append("Matches your current energy level")
        else:
            score += 8
    else:
        # Low energy - prefer easy tasks
        if task_energy_required <= 4:
            score += 20
            reasons.append("Light task suitable for lower energy")
        else:
            score += 5

    # 4. Time of day fit (0-10 points)
    # Morning (6-12): Good for creative/complex work
    # Afternoon (12-17): Good for collaborative/routine work
    # Evening (17-22): Good for wrapping up/planning
    if 6 <= current_hour < 12:
        if estimated_duration >= 60:
            score += 10
            reasons.append("Complex task - morning is your peak focus time")
        else:
            score += 5
    elif 12 <= current_hour < 17:
        if 30 <= estimated_duration <= 60:
            score += 10
        else:
            score += 5
    else:
        if estimated_duration <= 30:
            score += 10
            reasons.append("Quick task - good for end of day")
        else:
            score += 3

    # 5. Task age bonus (0-10 points) - older incomplete tasks get slight boost
    if task.get("created_at"):
        try:
            created = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
            days_old = (datetime.now(timezone.utc) - created).days
            if days_old > 7:
                score += 10
                reasons.append("This task has been waiting a while")
            elif days_old > 3:
                score += 5
        except (ValueError, TypeError):
            pass

    # 6. Started but not finished bonus (0-10 points)
    if task.get("status") == "paused":
        score += 10
        reasons.append("Continue where you left off")
    elif task.get("status") == "in_progress":
        score += 15
        reasons.append("You already started this task")

    return score, reasons


async def get_user_current_state(user_id: str) -> dict:
    """Get the user's current state including energy level."""
    supabase = get_supabase_admin()

    # Try to get today's check-in
    today = datetime.now(timezone.utc).date().isoformat()
    checkin = (
        supabase.table("daily_check_ins")
        .select("*")
        .eq("user_id", user_id)
        .eq("date", today)
        .execute()
    )

    if checkin.data:
        return checkin.data[0]

    # Fallback to user_states
    state = (
        supabase.table("user_states")
        .select("*")
        .eq("user_id", user_id)
        .is_("ended_at", "null")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )

    if state.data:
        return state.data[0]

    return {"energy_level": 5}  # Default


@router.get("")
async def get_next_do(
    current_user: dict = Depends(get_current_user),
):
    """Get the single most important task to do right now."""
    try:
        supabase = get_supabase_admin()

        # Get user's current state
        user_state = await get_user_current_state(current_user["id"])
        current_hour = datetime.now(timezone.utc).hour

        # Get all incomplete tasks
        tasks_response = (
            supabase.table("tasks")
            .select("*, projects(name)")
            .eq("user_id", current_user["id"])
            .in_("status", ["todo", "in_progress", "paused"])
            .execute()
        )

        tasks = tasks_response.data or []

        if not tasks:
            return {
                "success": True,
                "data": {
                    "task": None,
                    "message": "No tasks to do! Time to relax or plan ahead.",
                },
            }

        # Score each task
        scored_tasks = []
        for task in tasks:
            score, reasons = calculate_task_score(task, user_state, current_hour)
            scored_tasks.append({
                "task": task,
                "score": score,
                "reasons": reasons,
            })

        # Sort by score descending
        scored_tasks.sort(key=lambda x: x["score"], reverse=True)

        top_task = scored_tasks[0]

        return {
            "success": True,
            "data": {
                "task": {
                    "id": top_task["task"]["id"],
                    "title": top_task["task"]["title"],
                    "description": top_task["task"].get("description"),
                    "project_id": top_task["task"]["project_id"],
                    "project_name": top_task["task"].get("projects", {}).get("name") if top_task["task"].get("projects") else None,
                    "priority": top_task["task"]["priority"],
                    "status": top_task["task"]["status"],
                    "estimated_duration": top_task["task"].get("estimated_duration"),
                    "deadline": top_task["task"].get("deadline"),
                },
                "score": round(top_task["score"], 1),
                "reasons": top_task["reasons"],
                "energy_level": user_state.get("energy_level", 5),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_next_do: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get next task recommendation",
        )


@router.post("/feedback")
async def submit_feedback(
    request: NextDoFeedback,
    current_user: dict = Depends(get_current_user),
):
    """Submit feedback on a task recommendation."""
    supabase = get_supabase_admin()

    # Record feedback for AI learning
    feedback_data = {
        "user_id": current_user["id"],
        "task_id": request.task_id,
        "agent_type": "next_do",
        "data": {
            "feedback": request.feedback,
            "reason": request.reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

    supabase.table("ai_learning_data").insert(feedback_data).execute()

    return {
        "success": True,
        "message": "Feedback recorded. This helps improve recommendations!",
    }


@router.post("/skip")
async def skip_task(
    request: NextDoSkip,
    current_user: dict = Depends(get_current_user),
):
    """Skip the current recommended task and get the next one."""
    supabase = get_supabase_admin()

    # Record the skip
    skip_data = {
        "user_id": current_user["id"],
        "task_id": request.task_id,
        "agent_type": "next_do",
        "data": {
            "action": "skip",
            "reason": request.reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

    supabase.table("ai_learning_data").insert(skip_data).execute()

    # Get user's current state
    user_state = await get_user_current_state(current_user["id"])
    current_hour = datetime.now(timezone.utc).hour

    # Get all incomplete tasks except the skipped one
    tasks_response = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .in_("status", ["todo", "in_progress", "paused"])
        .neq("id", request.task_id)
        .execute()
    )

    tasks = tasks_response.data or []

    if not tasks:
        return {
            "success": True,
            "data": {
                "task": None,
                "message": "No other tasks available.",
            },
        }

    # Score and sort
    scored_tasks = []
    for task in tasks:
        score, reasons = calculate_task_score(task, user_state, current_hour)
        scored_tasks.append({"task": task, "score": score, "reasons": reasons})

    scored_tasks.sort(key=lambda x: x["score"], reverse=True)
    top_task = scored_tasks[0]

    return {
        "success": True,
        "data": {
            "task": {
                "id": top_task["task"]["id"],
                "title": top_task["task"]["title"],
                "description": top_task["task"].get("description"),
                "project_id": top_task["task"]["project_id"],
                "project_name": top_task["task"].get("projects", {}).get("name") if top_task["task"].get("projects") else None,
                "priority": top_task["task"]["priority"],
                "status": top_task["task"]["status"],
                "estimated_duration": top_task["task"].get("estimated_duration"),
                "deadline": top_task["task"].get("deadline"),
            },
            "score": round(top_task["score"], 1),
            "reasons": top_task["reasons"],
            "skipped_task_id": request.task_id,
        },
    }


@router.get("/queue")
async def get_task_queue(
    current_user: dict = Depends(get_current_user),
    limit: int = 5,
):
    """Get a preview of upcoming recommended tasks."""
    supabase = get_supabase_admin()

    user_state = await get_user_current_state(current_user["id"])
    current_hour = datetime.now(timezone.utc).hour

    tasks_response = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .in_("status", ["todo", "in_progress", "paused"])
        .execute()
    )

    tasks = tasks_response.data or []

    # Score all tasks
    scored_tasks = []
    for task in tasks:
        score, reasons = calculate_task_score(task, user_state, current_hour)
        scored_tasks.append({
            "id": task["id"],
            "title": task["title"],
            "project_name": task.get("projects", {}).get("name") if task.get("projects") else None,
            "priority": task["priority"],
            "status": task["status"],
            "score": round(score, 1),
            "reasons": reasons[:2],  # Top 2 reasons only
            "estimated_duration": task.get("estimated_duration"),
            "deadline": task.get("deadline"),
        })

    scored_tasks.sort(key=lambda x: x["score"], reverse=True)

    return {
        "success": True,
        "data": {
            "queue": scored_tasks[:limit],
            "total_pending": len(scored_tasks),
        },
    }


@router.post("/refresh")
async def refresh_recommendations(
    current_user: dict = Depends(get_current_user),
):
    """Force recalculation of task recommendations."""
    # This is essentially the same as GET /next-do but explicitly signals a refresh
    supabase = get_supabase_admin()

    user_state = await get_user_current_state(current_user["id"])
    current_hour = datetime.now(timezone.utc).hour

    tasks_response = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .in_("status", ["todo", "in_progress", "paused"])
        .execute()
    )

    tasks = tasks_response.data or []

    if not tasks:
        return {
            "success": True,
            "data": {
                "task": None,
                "queue": [],
                "message": "No tasks to do!",
            },
        }

    scored_tasks = []
    for task in tasks:
        score, reasons = calculate_task_score(task, user_state, current_hour)
        scored_tasks.append({"task": task, "score": score, "reasons": reasons})

    scored_tasks.sort(key=lambda x: x["score"], reverse=True)

    top_task = scored_tasks[0]
    queue = [
        {
            "id": st["task"]["id"],
            "title": st["task"]["title"],
            "score": round(st["score"], 1),
        }
        for st in scored_tasks[1:6]
    ]

    return {
        "success": True,
        "data": {
            "task": {
                "id": top_task["task"]["id"],
                "title": top_task["task"]["title"],
                "project_name": top_task["task"].get("projects", {}).get("name") if top_task["task"].get("projects") else None,
                "priority": top_task["task"]["priority"],
                "estimated_duration": top_task["task"].get("estimated_duration"),
            },
            "score": round(top_task["score"], 1),
            "reasons": top_task["reasons"],
            "queue": queue,
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
        },
    }
