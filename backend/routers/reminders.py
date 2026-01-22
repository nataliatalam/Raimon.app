from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone
from typing import Optional
from models.notification import ReminderCreate, ReminderUpdate, ReminderFrequency
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(prefix="/api/reminders", tags=["Reminders"])


@router.get("")
async def list_reminders(
    current_user: dict = Depends(get_current_user),
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, le=100),
):
    """List reminders for the current user."""
    supabase = get_supabase()

    query = (
        supabase.table("reminders")
        .select("*, tasks(title), projects(name)")
        .eq("user_id", current_user["id"])
    )

    if active_only:
        query = query.eq("is_active", True)

    query = query.order("remind_at", desc=False).limit(limit)

    response = query.execute()

    reminders = []
    for r in response.data or []:
        reminder = {
            **r,
            "task_title": r.get("tasks", {}).get("title") if r.get("tasks") else None,
            "project_name": r.get("projects", {}).get("name") if r.get("projects") else None,
        }
        reminder.pop("tasks", None)
        reminder.pop("projects", None)
        reminders.append(reminder)

    return {
        "success": True,
        "data": {
            "reminders": reminders,
            "total": len(reminders),
        },
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_reminder(
    request: ReminderCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new reminder."""
    supabase = get_supabase()

    # Validate task_id if provided
    if request.task_id:
        task = (
            supabase.table("tasks")
            .select("id")
            .eq("id", request.task_id)
            .eq("user_id", current_user["id"])
            .single()
            .execute()
        )
        if not task.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task not found",
            )

    # Validate project_id if provided
    if request.project_id:
        project = (
            supabase.table("projects")
            .select("id")
            .eq("id", request.project_id)
            .eq("user_id", current_user["id"])
            .single()
            .execute()
        )
        if not project.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found",
            )

    reminder_data = {
        "user_id": current_user["id"],
        "title": request.title,
        "message": request.message,
        "remind_at": request.remind_at.isoformat(),
        "frequency": request.frequency.value,
        "task_id": request.task_id,
        "project_id": request.project_id,
        "metadata": request.metadata,
        "is_active": True,
    }

    response = supabase.table("reminders").insert(reminder_data).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reminder",
        )

    return {
        "success": True,
        "data": {"reminder": response.data[0]},
    }


@router.get("/{reminder_id}")
async def get_reminder(
    reminder_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific reminder."""
    supabase = get_supabase()

    response = (
        supabase.table("reminders")
        .select("*, tasks(title), projects(name)")
        .eq("id", reminder_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    reminder = {
        **response.data,
        "task_title": response.data.get("tasks", {}).get("title") if response.data.get("tasks") else None,
        "project_name": response.data.get("projects", {}).get("name") if response.data.get("projects") else None,
    }
    reminder.pop("tasks", None)
    reminder.pop("projects", None)

    return {
        "success": True,
        "data": {"reminder": reminder},
    }


@router.put("/{reminder_id}")
async def update_reminder(
    reminder_id: str,
    request: ReminderUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a reminder."""
    supabase = get_supabase()

    # Verify ownership
    existing = (
        supabase.table("reminders")
        .select("id")
        .eq("id", reminder_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    update_data = {}
    if request.title is not None:
        update_data["title"] = request.title
    if request.message is not None:
        update_data["message"] = request.message
    if request.remind_at is not None:
        update_data["remind_at"] = request.remind_at.isoformat()
    if request.frequency is not None:
        update_data["frequency"] = request.frequency.value
    if request.is_active is not None:
        update_data["is_active"] = request.is_active

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    response = (
        supabase.table("reminders")
        .update(update_data)
        .eq("id", reminder_id)
        .execute()
    )

    return {
        "success": True,
        "data": {"reminder": response.data[0] if response.data else None},
    }


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a reminder."""
    supabase = get_supabase()

    # Verify ownership
    existing = (
        supabase.table("reminders")
        .select("id")
        .eq("id", reminder_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    supabase.table("reminders").delete().eq("id", reminder_id).execute()

    return {
        "success": True,
        "message": "Reminder deleted",
    }


@router.post("/{reminder_id}/snooze")
async def snooze_reminder(
    reminder_id: str,
    minutes: int = Query(default=15, ge=1, le=1440),
    current_user: dict = Depends(get_current_user),
):
    """Snooze a reminder for a specified number of minutes."""
    supabase = get_supabase()

    # Verify ownership
    existing = (
        supabase.table("reminders")
        .select("*")
        .eq("id", reminder_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    from datetime import timedelta
    new_remind_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    response = (
        supabase.table("reminders")
        .update({"remind_at": new_remind_at.isoformat()})
        .eq("id", reminder_id)
        .execute()
    )

    return {
        "success": True,
        "data": {
            "reminder": response.data[0] if response.data else None,
            "snoozed_until": new_remind_at.isoformat(),
        },
    }
