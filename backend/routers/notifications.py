from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone
from typing import Optional
from models.notification import NotificationType
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    current_user: dict = Depends(get_current_user),
    unread_only: bool = Query(default=False),
    notification_type: Optional[NotificationType] = Query(default=None, alias="type"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
):
    """List notifications for the current user."""
    supabase = get_supabase()

    query = (
        supabase.table("notifications")
        .select("*")
        .eq("user_id", current_user["id"])
    )

    if unread_only:
        query = query.eq("read", False)

    if notification_type:
        query = query.eq("type", notification_type.value)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    response = query.execute()

    # Get total unread count
    unread_count = (
        supabase.table("notifications")
        .select("id", count="exact")
        .eq("user_id", current_user["id"])
        .eq("read", False)
        .execute()
    )

    return {
        "success": True,
        "data": {
            "notifications": response.data or [],
            "total": len(response.data or []),
            "unread_count": unread_count.count or 0,
        },
    }


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a notification as read."""
    supabase = get_supabase()

    # Verify ownership
    notification = (
        supabase.table("notifications")
        .select("id")
        .eq("id", notification_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not notification.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    response = (
        supabase.table("notifications")
        .update({"read": True, "read_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", notification_id)
        .execute()
    )

    return {
        "success": True,
        "data": {"notification": response.data[0] if response.data else None},
    }


@router.put("/read-all")
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user),
):
    """Mark all notifications as read."""
    supabase = get_supabase()

    response = (
        supabase.table("notifications")
        .update({"read": True, "read_at": datetime.now(timezone.utc).isoformat()})
        .eq("user_id", current_user["id"])
        .eq("read", False)
        .execute()
    )

    return {
        "success": True,
        "message": f"Marked {len(response.data or [])} notifications as read",
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a notification."""
    supabase = get_supabase()

    # Verify ownership
    notification = (
        supabase.table("notifications")
        .select("id")
        .eq("id", notification_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not notification.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    supabase.table("notifications").delete().eq("id", notification_id).execute()

    return {
        "success": True,
        "message": "Notification deleted",
    }


# Helper function to create notifications (used internally)
async def create_notification(
    user_id: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    metadata: dict = None,
):
    """Create a new notification for a user."""
    supabase = get_supabase()

    notification_data = {
        "user_id": user_id,
        "type": notification_type.value,
        "title": title,
        "message": message,
        "metadata": metadata or {},
        "read": False,
    }

    response = supabase.table("notifications").insert(notification_data).execute()
    return response.data[0] if response.data else None
