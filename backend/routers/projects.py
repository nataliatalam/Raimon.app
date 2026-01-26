from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from models.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectProfileUpdate,
    ProjectGoalsUpdate,
    ProjectResourcesUpdate,
    ProjectTimelineUpdate,
    ProjectStakeholdersUpdate,
    ProjectStatus,
)
from core.supabase import get_supabase
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# Helper function to check project ownership
async def get_user_project(project_id, user_id: str):
    """Fetch a project and verify ownership."""
    try:
        supabase = get_supabase()
        response = (
            supabase.table("projects")
            .select("*")
            .eq("id", str(project_id))
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project",
        )


# Helper function to get project with task stats
async def get_project_with_stats(project: dict) -> dict:
    """Add task statistics to a project."""
    try:
        supabase = get_supabase()

        # Get task counts
        tasks_response = (
            supabase.table("tasks")
            .select("id, status")
            .eq("project_id", project["id"])
            .execute()
        )

        tasks = tasks_response.data or []
        task_count = len(tasks)
        completed_tasks = len([t for t in tasks if t["status"] == "completed"])
        progress = (completed_tasks / task_count * 100) if task_count > 0 else 0

        return {
            **project,
            "task_count": task_count,
            "completed_tasks": completed_tasks,
            "progress": round(progress, 1),
        }
    except Exception:
        # If stats fail, return project without stats
        return {
            **project,
            "task_count": 0,
            "completed_tasks": 0,
            "progress": 0,
        }


@router.get("")
async def list_projects(
    current_user: dict = Depends(get_current_user),
    status_filter: Optional[ProjectStatus] = Query(default=None, alias="status"),
    include_archived: bool = Query(default=False),
):
    """List all projects for the authenticated user."""
    try:
        supabase = get_supabase()

        query = supabase.table("projects").select("*").eq("user_id", current_user["id"])

        # Filter by status
        if status_filter:
            query = query.eq("status", status_filter.value)
        elif not include_archived:
            query = query.neq("status", "archived")

        query = query.order("priority", desc=True).order("created_at", desc=True)

        response = query.execute()

        # Add stats to each project
        projects_with_stats = []
        for project in response.data or []:
            project_with_stats = await get_project_with_stats(project)
            projects_with_stats.append(project_with_stats)

        return {
            "success": True,
            "data": {
                "projects": projects_with_stats,
                "total": len(projects_with_stats),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list projects",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new project."""
    try:
        supabase = get_supabase()

        # Prepare project data
        project_data = {
            "user_id": current_user["id"],
            "name": request.name,
            "description": request.description,
            "priority": request.priority,
            "color": request.color,
            "icon": request.icon,
            "status": "active",
        }

        if request.start_date:
            project_data["start_date"] = request.start_date.isoformat()
        if request.target_end_date:
            project_data["target_end_date"] = request.target_end_date.isoformat()

        # Insert project
        response = supabase.table("projects").insert(project_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project",
            )

        project = response.data[0]

        # Create project_details record if details provided
        if request.details:
            details_data = {
                "project_id": project["id"],
                **request.details,
            }
            supabase.table("project_details").insert(details_data).execute()

        return {
            "success": True,
            "data": {"project": project},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )


@router.get("/graveyard")
async def list_archived_projects(
    current_user: dict = Depends(get_current_user),
):
    """List all archived projects (graveyard)."""
    try:
        supabase = get_supabase()

        response = (
            supabase.table("projects")
            .select("*")
            .eq("user_id", current_user["id"])
            .eq("status", "archived")
            .order("archived_at", desc=True)
            .execute()
        )

        projects_with_stats = []
        for project in response.data or []:
            project_with_stats = await get_project_with_stats(project)
            projects_with_stats.append(project_with_stats)

        return {
            "success": True,
            "data": {
                "projects": projects_with_stats,
                "total": len(projects_with_stats),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list archived projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list archived projects",
        )


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific project by ID."""
    try:
        project = await get_user_project(project_id, current_user["id"])
        project_with_stats = await get_project_with_stats(project)

        # Get project details if exists
        supabase = get_supabase()
        details_response = (
            supabase.table("project_details")
            .select("*")
            .eq("project_id", str(project_id))
            .execute()
        )

        details = details_response.data[0] if details_response.data else None

        return {
            "success": True,
            "data": {
                "project": project_with_stats,
                "details": details,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get project",
        )


@router.put("/{project_id}")
async def update_project(
    project_id: UUID,
    request: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a project."""
    try:
        # Verify ownership
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase()

        # Build update data (exclude None values)
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.status is not None:
            update_data["status"] = request.status.value
        if request.priority is not None:
            update_data["priority"] = request.priority
        if request.color is not None:
            update_data["color"] = request.color
        if request.icon is not None:
            update_data["icon"] = request.icon
        if request.start_date is not None:
            update_data["start_date"] = request.start_date.isoformat()
        if request.target_end_date is not None:
            update_data["target_end_date"] = request.target_end_date.isoformat()

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        response = (
            supabase.table("projects")
            .update(update_data)
            .eq("id", str(project_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        return {
            "success": True,
            "data": {"project": response.data[0] if response.data else None},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project",
        )


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    permanent: bool = Query(default=False),
):
    """Delete a project. By default, archives it. Use permanent=true to hard delete."""
    try:
        # Verify ownership
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase()

        if permanent:
            # Hard delete - cascades to tasks, details, etc.
            supabase.table("projects").delete().eq("id", str(project_id)).execute()
            return {
                "success": True,
                "message": "Project permanently deleted",
            }
        else:
            # Soft delete - archive
            response = (
                supabase.table("projects")
                .update(
                    {
                        "status": "archived",
                        "archived_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .eq("id", str(project_id))
                .execute()
            )
            return {
                "success": True,
                "message": "Project archived",
                "data": {"project": response.data[0] if response.data else None},
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project",
        )


@router.post("/{project_id}/archive")
async def archive_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Archive a project."""
    try:
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase()

        response = (
            supabase.table("projects")
            .update(
                {
                    "status": "archived",
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", str(project_id))
            .execute()
        )

        return {
            "success": True,
            "message": "Project archived",
            "data": {"project": response.data[0] if response.data else None},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive project",
        )


@router.post("/{project_id}/restore")
async def restore_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Restore an archived project."""
    try:
        project = await get_user_project(project_id, current_user["id"])

        if project["status"] != "archived":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not archived",
            )

        supabase = get_supabase()

        response = (
            supabase.table("projects")
            .update(
                {
                    "status": "active",
                    "archived_at": None,
                }
            )
            .eq("id", str(project_id))
            .execute()
        )

        return {
            "success": True,
            "message": "Project restored",
            "data": {"project": response.data[0] if response.data else None},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore project",
        )


# Project Details Endpoints


@router.put("/{project_id}/profile")
async def update_project_profile(
    project_id: UUID,
    request: ProjectProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update project profile (name, description, color, icon)."""
    try:
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase()

        update_data = request.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        response = (
            supabase.table("projects")
            .update(update_data)
            .eq("id", str(project_id))
            .execute()
        )

        return {
            "success": True,
            "data": {"project": response.data[0] if response.data else None},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project profile",
        )


@router.put("/{project_id}/goals")
async def update_project_goals(
    project_id: UUID,
    request: ProjectGoalsUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update project goals."""
    try:
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase()

        # Upsert into project_details
        existing = (
            supabase.table("project_details")
            .select("id")
            .eq("project_id", str(project_id))
            .execute()
        )

        if existing.data:
            supabase.table("project_details").update(
                {"goals": request.goals}
            ).eq("project_id", project_id).execute()
        else:
            supabase.table("project_details").insert(
                {"project_id": project_id, "goals": request.goals}
            ).execute()

        return {
            "success": True,
            "data": {"goals": request.goals},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project goals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project goals",
        )


@router.put("/{project_id}/resources")
async def update_project_resources(
    project_id: UUID,
    request: ProjectResourcesUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update project resources."""
    try:
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase()

        resources_data = [r.model_dump() for r in request.resources]

        existing = (
            supabase.table("project_details")
            .select("id")
            .eq("project_id", str(project_id))
            .execute()
        )

        if existing.data:
            supabase.table("project_details").update(
                {"resources": resources_data}
            ).eq("project_id", project_id).execute()
        else:
            supabase.table("project_details").insert(
                {"project_id": project_id, "resources": resources_data}
            ).execute()

        return {
            "success": True,
            "data": {"resources": resources_data},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project resources",
        )


@router.put("/{project_id}/timeline")
async def update_project_timeline(
    project_id: UUID,
    request: ProjectTimelineUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update project timeline."""
    try:
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase()

        # Update dates on projects table
        project_update = {}
        if request.start_date is not None:
            project_update["start_date"] = request.start_date.isoformat()
        if request.target_end_date is not None:
            project_update["target_end_date"] = request.target_end_date.isoformat()

        if project_update:
            supabase.table("projects").update(project_update).eq("id", str(project_id)).execute()

        # Update milestones in project_details
        if request.milestones is not None:
            existing = (
                supabase.table("project_details")
                .select("id")
                .eq("project_id", str(project_id))
                .execute()
            )

            if existing.data:
                supabase.table("project_details").update(
                    {"milestones": request.milestones}
                ).eq("project_id", project_id).execute()
            else:
                supabase.table("project_details").insert(
                    {"project_id": project_id, "milestones": request.milestones}
                ).execute()

        return {
            "success": True,
            "data": {
                "start_date": request.start_date,
                "target_end_date": request.target_end_date,
                "milestones": request.milestones,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project timeline",
        )


@router.put("/{project_id}/stakeholders")
async def update_project_stakeholders(
    project_id: UUID,
    request: ProjectStakeholdersUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update project stakeholders."""
    try:
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase()

        stakeholders_data = [s.model_dump() for s in request.stakeholders]

        existing = (
            supabase.table("project_details")
            .select("id")
            .eq("project_id", str(project_id))
            .execute()
        )

        if existing.data:
            supabase.table("project_details").update(
                {"stakeholders": stakeholders_data}
            ).eq("project_id", project_id).execute()
        else:
            supabase.table("project_details").insert(
                {"project_id": project_id, "stakeholders": stakeholders_data}
            ).execute()

        return {
            "success": True,
            "data": {"stakeholders": stakeholders_data},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project stakeholders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project stakeholders",
        )
