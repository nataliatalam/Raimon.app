from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])


class IntegrationType(str, Enum):
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK = "outlook"
    NOTION = "notion"
    TODOIST = "todoist"
    SLACK = "slack"
    GITHUB = "github"
    JIRA = "jira"
    TRELLO = "trello"


class ConnectRequest(BaseModel):
    credentials: Optional[dict] = None
    settings: Optional[dict] = None


class SyncRequest(BaseModel):
    full_sync: bool = False
    sync_options: Optional[dict] = None


# Integration metadata
INTEGRATION_METADATA = {
    IntegrationType.GOOGLE_CALENDAR: {
        "name": "Google Calendar",
        "description": "Sync tasks with Google Calendar events",
        "icon": "calendar",
        "features": ["task_sync", "deadline_reminders", "time_blocking"],
    },
    IntegrationType.OUTLOOK: {
        "name": "Microsoft Outlook",
        "description": "Sync with Outlook calendar and tasks",
        "icon": "mail",
        "features": ["task_sync", "email_integration"],
    },
    IntegrationType.NOTION: {
        "name": "Notion",
        "description": "Sync projects and tasks with Notion databases",
        "icon": "book",
        "features": ["project_sync", "task_sync", "notes"],
    },
    IntegrationType.TODOIST: {
        "name": "Todoist",
        "description": "Import tasks from Todoist",
        "icon": "check-square",
        "features": ["task_import", "two_way_sync"],
    },
    IntegrationType.SLACK: {
        "name": "Slack",
        "description": "Get notifications and updates in Slack",
        "icon": "message-square",
        "features": ["notifications", "task_updates", "reminders"],
    },
    IntegrationType.GITHUB: {
        "name": "GitHub",
        "description": "Link tasks to GitHub issues and PRs",
        "icon": "github",
        "features": ["issue_linking", "pr_tracking", "commit_tracking"],
    },
    IntegrationType.JIRA: {
        "name": "Jira",
        "description": "Sync with Jira issues and projects",
        "icon": "trello",
        "features": ["issue_sync", "sprint_tracking"],
    },
    IntegrationType.TRELLO: {
        "name": "Trello",
        "description": "Sync with Trello boards and cards",
        "icon": "layout",
        "features": ["board_sync", "card_import"],
    },
}


@router.get("")
async def list_integrations(
    current_user: dict = Depends(get_current_user),
):
    """List all available integrations and their status."""
    supabase = get_supabase()

    # Get user's connected integrations
    connected = (
        supabase.table("integrations")
        .select("*")
        .eq("user_id", current_user["id"])
        .execute()
    )

    connected_types = {i["integration_type"]: i for i in (connected.data or [])}

    # Build integration list with status
    integrations = []
    for int_type, metadata in INTEGRATION_METADATA.items():
        connection = connected_types.get(int_type.value)
        integrations.append({
            "type": int_type.value,
            "name": metadata["name"],
            "description": metadata["description"],
            "icon": metadata["icon"],
            "features": metadata["features"],
            "connected": connection is not None,
            "connected_at": connection.get("connected_at") if connection else None,
            "last_synced": connection.get("last_synced_at") if connection else None,
            "status": connection.get("status") if connection else "not_connected",
        })

    return {
        "success": True,
        "data": {
            "integrations": integrations,
            "connected_count": len(connected_types),
        },
    }


@router.post("/{integration_type}/connect")
async def connect_integration(
    integration_type: IntegrationType,
    request: ConnectRequest,
    current_user: dict = Depends(get_current_user),
):
    """Connect to an integration."""
    supabase = get_supabase()

    # Check if already connected
    existing = (
        supabase.table("integrations")
        .select("id")
        .eq("user_id", current_user["id"])
        .eq("integration_type", integration_type.value)
        .single()
        .execute()
    )

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Already connected to {integration_type.value}",
        )

    # In a real implementation, this would:
    # 1. Initiate OAuth flow for the service
    # 2. Store encrypted credentials
    # 3. Verify the connection

    # For now, we'll create a pending connection
    integration_data = {
        "user_id": current_user["id"],
        "integration_type": integration_type.value,
        "status": "pending",
        "settings": request.settings or {},
        "connected_at": datetime.now(timezone.utc).isoformat(),
    }

    response = supabase.table("integrations").insert(integration_data).execute()

    metadata = INTEGRATION_METADATA.get(integration_type, {})

    return {
        "success": True,
        "data": {
            "integration": {
                "type": integration_type.value,
                "name": metadata.get("name"),
                "status": "pending",
                "connected_at": integration_data["connected_at"],
            },
            "message": f"Connection to {metadata.get('name', integration_type.value)} initiated",
            "next_steps": "Complete OAuth authorization to finish setup",
        },
    }


@router.delete("/{integration_type}/disconnect")
async def disconnect_integration(
    integration_type: IntegrationType,
    current_user: dict = Depends(get_current_user),
):
    """Disconnect from an integration."""
    supabase = get_supabase()

    # Verify connection exists
    existing = (
        supabase.table("integrations")
        .select("id")
        .eq("user_id", current_user["id"])
        .eq("integration_type", integration_type.value)
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not connected to {integration_type.value}",
        )

    # Delete the integration
    supabase.table("integrations").delete().eq("id", existing.data["id"]).execute()

    metadata = INTEGRATION_METADATA.get(integration_type, {})

    return {
        "success": True,
        "message": f"Disconnected from {metadata.get('name', integration_type.value)}",
    }


@router.post("/{integration_type}/sync")
async def sync_integration(
    integration_type: IntegrationType,
    request: SyncRequest,
    current_user: dict = Depends(get_current_user),
):
    """Sync data with an integration."""
    supabase = get_supabase()

    # Verify connection exists
    integration = (
        supabase.table("integrations")
        .select("*")
        .eq("user_id", current_user["id"])
        .eq("integration_type", integration_type.value)
        .single()
        .execute()
    )

    if not integration.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not connected to {integration_type.value}",
        )

    if integration.data.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integration is not active. Please reconnect.",
        )

    # In a real implementation, this would:
    # 1. Fetch data from the external service
    # 2. Sync tasks, projects, etc.
    # 3. Handle conflicts

    # Update last synced timestamp
    supabase.table("integrations").update({
        "last_synced_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", integration.data["id"]).execute()

    metadata = INTEGRATION_METADATA.get(integration_type, {})

    # Simulated sync results
    sync_results = {
        "items_synced": 0,
        "items_created": 0,
        "items_updated": 0,
        "errors": [],
    }

    return {
        "success": True,
        "data": {
            "integration": integration_type.value,
            "sync_type": "full" if request.full_sync else "incremental",
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "results": sync_results,
            "message": f"Sync with {metadata.get('name', integration_type.value)} completed",
        },
    }


@router.get("/{integration_type}/status")
async def get_integration_status(
    integration_type: IntegrationType,
    current_user: dict = Depends(get_current_user),
):
    """Get detailed status of an integration."""
    supabase = get_supabase()

    integration = (
        supabase.table("integrations")
        .select("*")
        .eq("user_id", current_user["id"])
        .eq("integration_type", integration_type.value)
        .single()
        .execute()
    )

    if not integration.data:
        metadata = INTEGRATION_METADATA.get(integration_type, {})
        return {
            "success": True,
            "data": {
                "type": integration_type.value,
                "name": metadata.get("name"),
                "connected": False,
                "status": "not_connected",
            },
        }

    metadata = INTEGRATION_METADATA.get(integration_type, {})

    return {
        "success": True,
        "data": {
            "type": integration_type.value,
            "name": metadata.get("name"),
            "connected": True,
            "status": integration.data.get("status"),
            "connected_at": integration.data.get("connected_at"),
            "last_synced_at": integration.data.get("last_synced_at"),
            "settings": integration.data.get("settings", {}),
            "features": metadata.get("features", []),
        },
    }
