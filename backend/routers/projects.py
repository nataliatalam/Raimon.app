from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
import json
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
from core.supabase import get_supabase, get_supabase_admin
from core.security import get_current_user
from opik import track
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# Helper function to check project ownership
async def get_user_project(project_id, user_id: str):
    """Fetch a project and verify ownership."""
    try:
        supabase = get_supabase_admin()
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
        supabase = get_supabase_admin()

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
        supabase = get_supabase_admin()

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
        logger.error(f"Failed to list projects: {e}", exc_info=True)
        # Return empty list on error instead of 500
        return {
            "success": True,
            "data": {
                "projects": [],
                "total": 0,
            },
        }


@router.post("", status_code=status.HTTP_201_CREATED)
@track(name="project_create_endpoint")
async def create_project(
    request: ProjectCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new project."""
    try:
        supabase = get_supabase_admin()

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
            # Only include known columns to avoid schema errors
            allowed_detail_fields = {"goals", "stakeholders", "resources", "milestones", "deadline", "people"}
            filtered_details = {k: v for k, v in request.details.items() if k in allowed_detail_fields}

            if filtered_details:
                details_data = {
                    "project_id": project["id"],
                    **filtered_details,
                }
                supabase.table("project_details").insert(details_data).execute()

            # Create tasks if provided in details
            tasks_list = request.details.get("tasks", [])
            logger.info(f"Creating project with tasks: {tasks_list}")
            if tasks_list and isinstance(tasks_list, list):
                for task_title in tasks_list:
                    if isinstance(task_title, str) and task_title.strip():
                        task_data = {
                            "project_id": project["id"],
                            "user_id": current_user["id"],
                            "title": task_title.strip(),
                            "status": "todo",
                        }
                        try:
                            result = supabase.table("tasks").insert(task_data).execute()
                            logger.info(f"Created task: {task_title} -> {result.data}")
                        except Exception as task_err:
                            logger.error(f"Failed to create task '{task_title}': {task_err}", exc_info=True)

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
        supabase = get_supabase_admin()

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
        logger.error(f"Failed to list archived projects: {e}", exc_info=True)
        # Return empty list on error instead of 500
        return {
            "success": True,
            "data": {
                "projects": [],
                "total": 0,
            },
        }


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific project by ID with tasks and notes."""
    try:
        project = await get_user_project(project_id, current_user["id"])
        project_with_stats = await get_project_with_stats(project)

        supabase = get_supabase_admin()

        # Get project details if exists (includes notes)
        details_response = (
            supabase.table("project_details")
            .select("*")
            .eq("project_id", str(project_id))
            .execute()
        )
        details = details_response.data[0] if details_response.data else None

        # Get tasks for this project
        tasks_response = (
            supabase.table("tasks")
            .select("*")
            .eq("project_id", str(project_id))
            .order("created_at", desc=False)
            .execute()
        )

        # Format tasks for frontend
        tasks = []
        for task in (tasks_response.data or []):
            tasks.append({
                "id": task["id"],
                "title": task.get("title", ""),
                "completed": task.get("status") == "completed",
                "dueDate": task.get("deadline"),  # Table uses 'deadline' column
                "priority": task.get("priority", "medium"),
                "subtasks": [],  # TODO: fetch subtasks if needed
            })

        # Add tasks and notes to project response
        project_with_stats["tasks"] = tasks
        project_with_stats["notes"] = details.get("notes", "") if details else ""

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
@track(name="project_update_endpoint")
async def update_project(
    project_id: UUID,
    request: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a project including notes and tasks."""
    try:
        # Verify ownership
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase_admin()

        # Build update data for projects table (exclude None values)
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

        # Update projects table if there's data
        if update_data:
            response = (
                supabase.table("projects")
                .update(update_data)
                .eq("id", str(project_id))
                .eq("user_id", current_user["id"])
                .execute()
            )
            project_result = response.data[0] if response.data else None
        else:
            project_result = None

        # Handle notes - store in project_details table
        if request.notes is not None:
            try:
                existing_details = (
                    supabase.table("project_details")
                    .select("id")
                    .eq("project_id", str(project_id))
                    .execute()
                )

                if existing_details.data:
                    supabase.table("project_details").update(
                        {"notes": request.notes}
                    ).eq("project_id", str(project_id)).execute()
                else:
                    supabase.table("project_details").insert(
                        {"project_id": str(project_id), "notes": request.notes}
                    ).execute()
            except Exception as notes_err:
                logger.warning(f"Failed to save notes (column may not exist): {notes_err}")
                # Continue without failing - notes column might not exist

        # Handle tasks - sync with tasks table
        if request.tasks is not None:
            try:
                # Get existing tasks for this project
                existing_tasks = (
                    supabase.table("tasks")
                    .select("id")
                    .eq("project_id", str(project_id))
                    .execute()
                )
                existing_task_ids = {t["id"] for t in (existing_tasks.data or [])}

                # Track which tasks are in the request
                request_task_ids = set()

                for task in request.tasks:
                    # Use correct status values: 'todo', 'in_progress', 'paused', 'on_break', 'blocked', 'completed'
                    task_data = {
                        "project_id": str(project_id),
                        "user_id": current_user["id"],
                        "title": task.title,
                        "status": "completed" if task.completed else "todo",
                    }

                    # Add optional fields using correct column names
                    if task.due_date:
                        task_data["deadline"] = task.due_date  # Table uses 'deadline' not 'due_date'
                    if task.priority:
                        task_data["priority"] = task.priority

                    # Check if this is an existing task (valid UUID format)
                    is_existing = (
                        task.id
                        and task.id in existing_task_ids
                        and len(task.id) == 36  # UUID format check
                        and "-" in task.id
                    )

                    if is_existing:
                        # Update existing task
                        supabase.table("tasks").update(task_data).eq("id", task.id).execute()
                        request_task_ids.add(task.id)
                    else:
                        # Create new task
                        new_task = supabase.table("tasks").insert(task_data).execute()
                        if new_task.data:
                            request_task_ids.add(new_task.data[0]["id"])

                # Delete tasks that are no longer in the request
                tasks_to_delete = existing_task_ids - request_task_ids
                for task_id in tasks_to_delete:
                    supabase.table("tasks").delete().eq("id", task_id).execute()

                # Auto-complete project if all tasks are completed
                if request.tasks:
                    all_completed = all(task.completed for task in request.tasks)
                    has_tasks = len(request.tasks) > 0

                    if has_tasks and all_completed:
                        # Set project status to completed
                        supabase.table("projects").update(
                            {"status": "completed"}
                        ).eq("id", str(project_id)).execute()
                        logger.info(f"Project {project_id} auto-completed - all tasks done")
                    elif has_tasks and not all_completed:
                        # If project was completed but now has incomplete tasks, reactivate it
                        current_project = (
                            supabase.table("projects")
                            .select("status")
                            .eq("id", str(project_id))
                            .single()
                            .execute()
                        )
                        if current_project.data and current_project.data.get("status") == "completed":
                            supabase.table("projects").update(
                                {"status": "active"}
                            ).eq("id", str(project_id)).execute()
                            logger.info(f"Project {project_id} reactivated - has incomplete tasks")

            except Exception as tasks_err:
                logger.error(f"Failed to save tasks: {tasks_err}", exc_info=True)
                # Continue without failing - but log the full error

        # Fetch the updated project to return current state (including auto-completed status)
        updated_project = (
            supabase.table("projects")
            .select("*")
            .eq("id", str(project_id))
            .single()
            .execute()
        )

        return {
            "success": True,
            "data": {"project": updated_project.data if updated_project.data else project_result},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project: {e}", exc_info=True)
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

        supabase = get_supabase_admin()

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

        supabase = get_supabase_admin()

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

        supabase = get_supabase_admin()

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

        supabase = get_supabase_admin()

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

        supabase = get_supabase_admin()

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

        supabase = get_supabase_admin()

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

        supabase = get_supabase_admin()

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

        supabase = get_supabase_admin()

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


# ============================================
# FILE UPLOAD ENDPOINTS
# ============================================

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
]

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/{project_id}/files", status_code=status.HTTP_201_CREATED)
async def upload_project_files(
    project_id: UUID,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload files to a project."""
    try:
        # Verify ownership
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase_admin()
        uploaded_files = []

        for file in files:
            # Validate file type
            if file.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} is not allowed",
                )

            # Read file content
            content = await file.read()

            # Validate file size
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds maximum size of 10MB",
                )

            # Generate unique file path
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            safe_filename = file.filename.replace(" ", "_") if file.filename else "file"
            file_path = f"{current_user['id']}/{project_id}/{timestamp}_{safe_filename}"

            # Upload to Supabase Storage
            try:
                storage_response = supabase.storage.from_("project-files").upload(
                    file_path,
                    content,
                    {"content-type": file.content_type},
                )
            except Exception as storage_error:
                logger.error(f"Storage upload failed: {storage_error}")
                # Continue with database entry even if storage fails
                # This allows the feature to work without storage configured
                file_path = f"pending/{file_path}"

            # Store file reference in database
            file_data = {
                "project_id": str(project_id),
                "file_name": file.filename,
                "file_path": file_path,
                "file_size": len(content),
                "mime_type": file.content_type,
            }

            db_response = supabase.table("project_files").insert(file_data).execute()

            if db_response.data:
                uploaded_files.append({
                    "id": db_response.data[0]["id"],
                    "file_name": file.filename,
                    "file_path": file_path,
                    "file_size": len(content),
                    "mime_type": file.content_type,
                })

        return {
            "success": True,
            "data": {"files": uploaded_files},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload files",
        )


@router.get("/{project_id}/files")
async def list_project_files(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """List all files for a project."""
    try:
        # Verify ownership
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase_admin()

        response = (
            supabase.table("project_files")
            .select("*")
            .eq("project_id", str(project_id))
            .order("uploaded_at", desc=True)
            .execute()
        )

        return {
            "success": True,
            "data": {"files": response.data or []},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list project files: {e}", exc_info=True)
        # Return empty list on error instead of 500
        return {
            "success": True,
            "data": {"files": []},
        }


@router.delete("/{project_id}/files/{file_id}")
async def delete_project_file(
    project_id: UUID,
    file_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Delete a file from a project."""
    try:
        # Verify project ownership
        await get_user_project(project_id, current_user["id"])

        supabase = get_supabase_admin()

        # Get file record
        file_response = (
            supabase.table("project_files")
            .select("*")
            .eq("id", str(file_id))
            .eq("project_id", str(project_id))
            .execute()
        )

        if not file_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        file_record = file_response.data[0]

        # Delete from storage (ignore errors if storage not configured)
        try:
            if not file_record["file_path"].startswith("pending/"):
                supabase.storage.from_("project-files").remove([file_record["file_path"]])
        except Exception as storage_error:
            logger.warning(f"Could not delete file from storage: {storage_error}")

        # Delete database record
        supabase.table("project_files").delete().eq("id", str(file_id)).execute()

        return {
            "success": True,
            "message": "File deleted",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file",
        )


# Alternative create endpoint that accepts FormData with files
@router.post("/with-files", status_code=status.HTTP_201_CREATED)
async def create_project_with_files(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    priority: int = Form(0),
    color: Optional[str] = Form(None),
    icon: Optional[str] = Form(None),
    target_end_date: Optional[str] = Form(None),
    details: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    current_user: dict = Depends(get_current_user),
):
    """Create a new project with optional file uploads."""
    try:
        supabase = get_supabase_admin()

        # Prepare project data
        project_data = {
            "user_id": current_user["id"],
            "name": name,
            "description": description,
            "priority": priority,
            "color": color,
            "icon": icon,
            "status": "active",
        }

        if target_end_date:
            project_data["target_end_date"] = target_end_date

        # Insert project
        response = supabase.table("projects").insert(project_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project",
            )

        project = response.data[0]

        # Parse and save project details
        if details:
            try:
                details_dict = json.loads(details)
                # Only include known columns to avoid schema errors
                allowed_detail_fields = {"goals", "stakeholders", "resources", "milestones", "deadline", "people"}
                filtered_details = {k: v for k, v in details_dict.items() if k in allowed_detail_fields}

                if filtered_details:
                    details_data = {
                        "project_id": project["id"],
                        **filtered_details,
                    }
                    supabase.table("project_details").insert(details_data).execute()

                # Create tasks if provided in details
                tasks_list = details_dict.get("tasks", [])
                if tasks_list and isinstance(tasks_list, list):
                    for task_title in tasks_list:
                        if isinstance(task_title, str) and task_title.strip():
                            task_data = {
                                "project_id": project["id"],
                                "user_id": current_user["id"],
                                "title": task_title.strip(),
                                "status": "todo",
                            }
                            try:
                                supabase.table("tasks").insert(task_data).execute()
                            except Exception as task_err:
                                logger.warning(f"Failed to create task: {task_err}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in details field: {details}")

        # Upload files if provided
        uploaded_files = []
        if files:
            supabase_admin = get_supabase_admin()
            for file in files:
                if not file.filename:
                    continue

                # Validate file type
                if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
                    continue

                content = await file.read()

                # Skip files that are too large
                if len(content) > MAX_FILE_SIZE:
                    continue

                # Generate file path
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                safe_filename = file.filename.replace(" ", "_")
                file_path = f"{current_user['id']}/{project['id']}/{timestamp}_{safe_filename}"

                # Try to upload to storage
                try:
                    supabase_admin.storage.from_("project-files").upload(
                        file_path,
                        content,
                        {"content-type": file.content_type or "application/octet-stream"},
                    )
                except Exception as storage_error:
                    logger.warning(f"Storage upload failed: {storage_error}")
                    file_path = f"pending/{file_path}"

                # Save file record
                file_data = {
                    "project_id": project["id"],
                    "file_name": file.filename,
                    "file_path": file_path,
                    "file_size": len(content),
                    "mime_type": file.content_type,
                }

                db_response = supabase.table("project_files").insert(file_data).execute()
                if db_response.data:
                    uploaded_files.append(db_response.data[0])

        return {
            "success": True,
            "data": {
                "project": project,
                "files": uploaded_files,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create project with files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )
