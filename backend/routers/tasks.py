from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone
from typing import Optional, List
from models.task import (
    TaskCreate,
    TaskUpdate,
    TaskStatusUpdate,
    TaskPriorityUpdate,
    TaskStartRequest,
    TaskPauseRequest,
    TaskCompleteRequest,
    TaskBreakRequest,
    TaskInterventionRequest,
    TaskStatus,
    TaskPriority,
)
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(tags=["Tasks"])


# Helper functions
async def verify_project_access(project_id: str, user_id: str):
    """Verify user has access to the project."""
    supabase = get_supabase()
    response = (
        supabase.table("projects")
        .select("id")
        .eq("id", project_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return response.data


async def get_user_task(task_id: str, user_id: str):
    """Fetch a task and verify ownership."""
    supabase = get_supabase()
    response = (
        supabase.table("tasks")
        .select("*")
        .eq("id", task_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return response.data


async def get_active_session(task_id: str, user_id: str):
    """Get the active work session for a task."""
    supabase = get_supabase()
    response = (
        supabase.table("work_sessions")
        .select("*")
        .eq("task_id", task_id)
        .eq("user_id", user_id)
        .is_("end_time", "null")
        .order("start_time", desc=True)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


async def end_active_session(task_id: str, user_id: str, energy_after: Optional[int] = None):
    """End the active work session for a task."""
    supabase = get_supabase()
    session = await get_active_session(task_id, user_id)

    if session:
        update_data = {"end_time": datetime.now(timezone.utc).isoformat()}
        if energy_after is not None:
            update_data["energy_after"] = energy_after

        supabase.table("work_sessions").update(update_data).eq("id", session["id"]).execute()

    return session


# Project Tasks Endpoints
@router.get("/api/projects/{project_id}/tasks")
async def list_project_tasks(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    status_filter: Optional[TaskStatus] = Query(default=None, alias="status"),
    priority_filter: Optional[TaskPriority] = Query(default=None, alias="priority"),
    include_completed: bool = Query(default=False),
):
    """List all tasks for a project."""
    await verify_project_access(project_id, current_user["id"])

    supabase = get_supabase()

    query = (
        supabase.table("tasks")
        .select("*")
        .eq("project_id", project_id)
        .eq("user_id", current_user["id"])
    )

    if status_filter:
        query = query.eq("status", status_filter.value)
    elif not include_completed:
        query = query.neq("status", "completed")

    if priority_filter:
        query = query.eq("priority", priority_filter.value)

    # Order by priority (urgent first), then by deadline, then by created_at
    query = query.order("created_at", desc=True)

    response = query.execute()

    # Sort by priority weight
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    tasks = sorted(
        response.data or [],
        key=lambda t: (priority_order.get(t.get("priority", "medium"), 2), t.get("deadline") or "9999"),
    )

    return {
        "success": True,
        "data": {
            "tasks": tasks,
            "total": len(tasks),
        },
    }


@router.post("/api/projects/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: str,
    request: TaskCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new task in a project."""
    await verify_project_access(project_id, current_user["id"])

    supabase = get_supabase()

    # Validate parent task if provided
    if request.parent_task_id:
        parent = await get_user_task(request.parent_task_id, current_user["id"])
        if parent["project_id"] != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent task must be in the same project",
            )

    task_data = {
        "project_id": project_id,
        "user_id": current_user["id"],
        "title": request.title,
        "description": request.description,
        "priority": request.priority.value,
        "status": "todo",
        "estimated_duration": request.estimated_duration,
        "tags": request.tags,
        "parent_task_id": request.parent_task_id,
    }

    if request.deadline:
        task_data["deadline"] = request.deadline.isoformat()

    response = supabase.table("tasks").insert(task_data).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )

    return {
        "success": True,
        "data": {"task": response.data[0]},
    }


# Individual Task Endpoints
@router.get("/api/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific task by ID."""
    task = await get_user_task(task_id, current_user["id"])

    # Get subtasks
    supabase = get_supabase()
    subtasks_response = (
        supabase.table("tasks")
        .select("*")
        .eq("parent_task_id", task_id)
        .execute()
    )

    # Get active session if any
    active_session = await get_active_session(task_id, current_user["id"])

    return {
        "success": True,
        "data": {
            "task": task,
            "subtasks": subtasks_response.data or [],
            "active_session": active_session,
        },
    }


@router.put("/api/tasks/{task_id}")
async def update_task(
    task_id: str,
    request: TaskUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a task."""
    await get_user_task(task_id, current_user["id"])

    supabase = get_supabase()

    update_data = {}
    if request.title is not None:
        update_data["title"] = request.title
    if request.description is not None:
        update_data["description"] = request.description
    if request.priority is not None:
        update_data["priority"] = request.priority.value
    if request.status is not None:
        update_data["status"] = request.status.value
    if request.estimated_duration is not None:
        update_data["estimated_duration"] = request.estimated_duration
    if request.deadline is not None:
        update_data["deadline"] = request.deadline.isoformat()
    if request.tags is not None:
        update_data["tags"] = request.tags
    if request.parent_task_id is not None:
        update_data["parent_task_id"] = request.parent_task_id

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    response = (
        supabase.table("tasks")
        .update(update_data)
        .eq("id", task_id)
        .execute()
    )

    return {
        "success": True,
        "data": {"task": response.data[0] if response.data else None},
    }


@router.delete("/api/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a task."""
    task = await get_user_task(task_id, current_user["id"])

    supabase = get_supabase()

    # Check for subtasks
    subtasks = (
        supabase.table("tasks")
        .select("id")
        .eq("parent_task_id", task_id)
        .execute()
    )

    if subtasks.data:
        # Option 1: Delete subtasks too (cascade)
        # Option 2: Prevent deletion if has subtasks
        # Going with cascade delete
        for subtask in subtasks.data:
            supabase.table("tasks").delete().eq("id", subtask["id"]).execute()

    # End any active sessions
    await end_active_session(task_id, current_user["id"])

    # Delete the task
    supabase.table("tasks").delete().eq("id", task_id).execute()

    return {
        "success": True,
        "message": "Task deleted",
    }


@router.patch("/api/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    request: TaskStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update task status."""
    task = await get_user_task(task_id, current_user["id"])

    supabase = get_supabase()

    update_data = {"status": request.status.value}

    # Handle status-specific logic
    if request.status == TaskStatus.COMPLETED:
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        # End active session
        await end_active_session(task_id, current_user["id"])
    elif request.status == TaskStatus.IN_PROGRESS and task["status"] == "todo":
        update_data["started_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("tasks")
        .update(update_data)
        .eq("id", task_id)
        .execute()
    )

    return {
        "success": True,
        "data": {"task": response.data[0] if response.data else None},
    }


@router.patch("/api/tasks/{task_id}/priority")
async def update_task_priority(
    task_id: str,
    request: TaskPriorityUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update task priority."""
    await get_user_task(task_id, current_user["id"])

    supabase = get_supabase()

    response = (
        supabase.table("tasks")
        .update({"priority": request.priority.value})
        .eq("id", task_id)
        .execute()
    )

    return {
        "success": True,
        "data": {"task": response.data[0] if response.data else None},
    }


# Task Action Endpoints
@router.post("/api/tasks/{task_id}/start")
async def start_task(
    task_id: str,
    request: TaskStartRequest,
    current_user: dict = Depends(get_current_user),
):
    """Start working on a task."""
    task = await get_user_task(task_id, current_user["id"])

    if task["status"] == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start a completed task",
        )

    supabase = get_supabase()

    # Check if there's already an active session on any task
    existing_session = (
        supabase.table("work_sessions")
        .select("*, tasks(title)")
        .eq("user_id", current_user["id"])
        .is_("end_time", "null")
        .execute()
    )

    if existing_session.data:
        # End the existing session
        for session in existing_session.data:
            supabase.table("work_sessions").update(
                {"end_time": datetime.now(timezone.utc).isoformat()}
            ).eq("id", session["id"]).execute()

            # Pause the other task
            if session["task_id"] != task_id:
                supabase.table("tasks").update(
                    {"status": "paused"}
                ).eq("id", session["task_id"]).execute()

    # Create new work session
    session_data = {
        "task_id": task_id,
        "user_id": current_user["id"],
        "start_time": datetime.now(timezone.utc).isoformat(),
        "energy_before": request.energy_level,
        "notes": request.notes,
        "interruptions": 0,
    }

    session_response = supabase.table("work_sessions").insert(session_data).execute()

    # Update task status
    task_update = {"status": "in_progress"}
    if task["status"] == "todo":
        task_update["started_at"] = datetime.now(timezone.utc).isoformat()

    task_response = (
        supabase.table("tasks")
        .update(task_update)
        .eq("id", task_id)
        .execute()
    )

    return {
        "success": True,
        "data": {
            "task": task_response.data[0] if task_response.data else None,
            "session": session_response.data[0] if session_response.data else None,
        },
    }


@router.post("/api/tasks/{task_id}/pause")
async def pause_task(
    task_id: str,
    request: TaskPauseRequest,
    current_user: dict = Depends(get_current_user),
):
    """Pause working on a task."""
    task = await get_user_task(task_id, current_user["id"])

    if task["status"] not in ["in_progress", "on_break"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not in progress",
        )

    supabase = get_supabase()

    # End active session
    session = await end_active_session(task_id, current_user["id"])

    # Update session with pause reason if provided
    if session and request.reason:
        supabase.table("work_sessions").update(
            {"notes": f"{session.get('notes', '') or ''}\nPaused: {request.reason}".strip()}
        ).eq("id", session["id"]).execute()

    # Update task status
    task_response = (
        supabase.table("tasks")
        .update({"status": "paused"})
        .eq("id", task_id)
        .execute()
    )

    return {
        "success": True,
        "data": {
            "task": task_response.data[0] if task_response.data else None,
            "session": session,
        },
    }


@router.post("/api/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    request: TaskCompleteRequest,
    current_user: dict = Depends(get_current_user),
):
    """Mark a task as complete."""
    task = await get_user_task(task_id, current_user["id"])

    if task["status"] == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is already completed",
        )

    supabase = get_supabase()

    # End active session
    session = await end_active_session(task_id, current_user["id"], request.energy_after)

    # Calculate actual duration from all sessions
    all_sessions = (
        supabase.table("work_sessions")
        .select("start_time, end_time")
        .eq("task_id", task_id)
        .not_.is_("end_time", "null")
        .execute()
    )

    total_duration = 0
    for s in all_sessions.data or []:
        if s["start_time"] and s["end_time"]:
            start = datetime.fromisoformat(s["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(s["end_time"].replace("Z", "+00:00"))
            total_duration += int((end - start).total_seconds() / 60)

    # Use provided duration or calculated
    actual_duration = request.actual_duration or total_duration

    # Update task
    task_response = (
        supabase.table("tasks")
        .update({
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "actual_duration": actual_duration,
        })
        .eq("id", task_id)
        .execute()
    )

    return {
        "success": True,
        "data": {
            "task": task_response.data[0] if task_response.data else None,
            "session": session,
            "total_duration": actual_duration,
        },
    }


@router.post("/api/tasks/{task_id}/break")
async def take_break(
    task_id: str,
    request: TaskBreakRequest,
    current_user: dict = Depends(get_current_user),
):
    """Take a break from the task."""
    task = await get_user_task(task_id, current_user["id"])

    if task["status"] not in ["in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not in progress",
        )

    supabase = get_supabase()

    # End active session
    session = await end_active_session(task_id, current_user["id"])

    # Update session notes
    if session:
        break_note = f"Break ({request.break_type}): {request.reason or 'No reason'}"
        supabase.table("work_sessions").update(
            {"notes": f"{session.get('notes', '') or ''}\n{break_note}".strip()}
        ).eq("id", session["id"]).execute()

    # Update task status
    task_response = (
        supabase.table("tasks")
        .update({"status": "on_break"})
        .eq("id", task_id)
        .execute()
    )

    # Determine break duration
    break_durations = {"short": 5, "long": 15, "custom": request.duration or 10}
    break_duration = break_durations.get(request.break_type, 10)

    return {
        "success": True,
        "data": {
            "task": task_response.data[0] if task_response.data else None,
            "break_duration": break_duration,
            "break_type": request.break_type,
            "message": f"Take a {break_duration} minute break!",
        },
    }


@router.post("/api/tasks/{task_id}/intervention")
async def report_intervention(
    task_id: str,
    request: TaskInterventionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Report an intervention (stuck, interrupted, blocked, overwhelmed)."""
    task = await get_user_task(task_id, current_user["id"])

    supabase = get_supabase()

    # Increment interruption count on active session
    session = await get_active_session(task_id, current_user["id"])
    if session:
        supabase.table("work_sessions").update(
            {"interruptions": (session.get("interruptions", 0) or 0) + 1}
        ).eq("id", session["id"]).execute()

    # Record the intervention in stuck_pattern_detections
    intervention_data = {
        "task_id": task_id,
        "user_id": current_user["id"],
        "pattern_type": request.intervention_type,
        "description": request.description,
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "suggested_actions": get_intervention_suggestions(request.intervention_type),
    }

    supabase.table("stuck_pattern_detections").insert(intervention_data).execute()

    # Update task status if blocked
    if request.intervention_type == "blocked":
        supabase.table("tasks").update({"status": "blocked"}).eq("id", task_id).execute()

    # Generate suggestions based on intervention type
    suggestions = get_intervention_suggestions(request.intervention_type)

    return {
        "success": True,
        "data": {
            "intervention_type": request.intervention_type,
            "recorded": True,
            "suggestions": suggestions,
        },
    }


def get_intervention_suggestions(intervention_type: str) -> list:
    """Get suggestions based on intervention type."""
    suggestions_map = {
        "stuck": [
            {"action": "take_break", "reason": "Clear your mind with a short break", "duration": 5},
            {"action": "break_task", "reason": "Split the task into smaller pieces"},
            {"action": "ask_help", "reason": "Reach out to a colleague or resource"},
        ],
        "interrupted": [
            {"action": "note_context", "reason": "Write down where you left off"},
            {"action": "block_notifications", "reason": "Enable focus mode"},
            {"action": "reschedule", "reason": "Find a quieter time to work"},
        ],
        "blocked": [
            {"action": "switch_task", "reason": "Work on something else while waiting"},
            {"action": "document_blocker", "reason": "Clearly document what's blocking you"},
            {"action": "escalate", "reason": "Reach out to resolve the blocker"},
        ],
        "overwhelmed": [
            {"action": "take_break", "reason": "Step away and breathe", "duration": 10},
            {"action": "prioritize", "reason": "Focus on just one small thing"},
            {"action": "simplify", "reason": "Remove non-essential requirements"},
        ],
    }

    return suggestions_map.get(intervention_type, [])
