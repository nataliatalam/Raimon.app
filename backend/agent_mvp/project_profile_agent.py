"""
Project Profile Agent - Project normalization and suggestions.

Functionality: Normalize project data, generate optional suggestions for project structure/priorities.

Inputs: ProjectProfileRequest { project_id, include_suggestions: bool }

Outputs: ProjectProfile { project_id, normalized_data, suggestions? }

Memory:
- reads: projects, tasks (by project), work_sessions (by project)
- writes: ai_learning_data (agent_type=project_profile) if suggestions generated

LLM: Optional (for suggestions only, bounded copy)

Critical guarantees:
- never modifies project/task data
- suggestions are optional and bounded
"""

from typing import Dict, Any, List, Optional
from agent_mvp.contracts import (
    ProjectProfileRequest,
    ProjectProfile,
    ProjectSuggestion,
)
from agent_mvp.storage import get_project_data, get_project_tasks, get_project_sessions, save_ai_learning
from agent_mvp.gemini_client import GeminiClient
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="project_profile_agent")
def analyze_project_profile(
    user_id: str,
    request: ProjectProfileRequest,
) -> ProjectProfile:
    """
    Analyze and normalize project profile.

    Args:
        user_id: User UUID
        request: Project analysis request

    Returns:
        ProjectProfile with normalized data and optional suggestions
    """
    logger.info(f"📁 Analyzing project {request.project_id} for user {user_id}")

    # Get project data
    project = get_project_data(request.project_id, user_id)
    if not project:
        raise ValueError(f"Project {request.project_id} not found")

    # Normalize project data
    normalized = _normalize_project_data(project)

    # Add task statistics
    normalized["task_stats"] = _analyze_project_tasks(request.project_id)

    # Add session statistics
    normalized["session_stats"] = _analyze_project_sessions(request.project_id)

    profile = ProjectProfile(
        project_id=request.project_id,
        normalized_data=normalized,
    )

    # Generate suggestions if requested
    if request.include_suggestions:
        profile.suggestions = _generate_project_suggestions(user_id, normalized)

    logger.info(f"✅ Project profile complete for {request.project_id}")
    return profile


def _normalize_project_data(project: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize project data structure."""
    return {
        "name": project.get("name", ""),
        "description": project.get("description", ""),
        "status": project.get("status", "active"),
        "priority": project.get("priority", "medium"),
        "tags": project.get("tags", []),
        "created_at": project.get("created_at"),
        "deadline": project.get("deadline"),
        "progress_percentage": project.get("progress_percentage", 0),
        "estimated_hours": project.get("estimated_hours"),
    }


def _analyze_project_tasks(project_id: str) -> Dict[str, Any]:
    """Analyze tasks within the project."""
    tasks = get_project_tasks(project_id)

    if not tasks:
        return {"total_tasks": 0, "completed": 0, "completion_rate": 0}

    completed = sum(1 for t in tasks if t.get("status") == "completed")
    total = len(tasks)

    # Priority distribution
    priorities = {}
    for task in tasks:
        pri = task.get("priority", "medium")
        priorities[pri] = priorities.get(pri, 0) + 1

    return {
        "total_tasks": total,
        "completed": completed,
        "completion_rate": round(completed / total, 2) if total > 0 else 0,
        "priority_distribution": priorities,
    }


def _analyze_project_sessions(project_id: str) -> Dict[str, Any]:
    """Analyze work sessions for the project."""
    sessions = get_project_sessions(project_id)

    if not sessions:
        return {"total_sessions": 0, "total_time": 0}

    total_time = sum(s.get("duration_minutes", 0) for s in sessions)
    completed_sessions = sum(1 for s in sessions if s.get("completed_at"))

    return {
        "total_sessions": len(sessions),
        "total_time_minutes": total_time,
        "completed_sessions": completed_sessions,
        "completion_rate": round(completed_sessions / len(sessions), 2) if sessions else 0,
    }


def _generate_project_suggestions(
    user_id: str,
    normalized_data: Dict[str, Any]
) -> List[ProjectSuggestion]:
    """Generate bounded suggestions for project improvement."""
    try:
        client = GeminiClient()

        prompt = f"""
        Analyze this project profile and provide up to 3 specific, actionable suggestions for improvement.
        Focus on productivity, organization, or completion strategies.

        Project Data:
        {normalized_data}

        Return JSON array of suggestions, each with "category", "suggestion", "impact" (high/medium/low).
        Keep each suggestion under 100 characters.
        """

        response = client.generate_json_response(prompt, max_tokens=300)

        if not response or not isinstance(response, list):
            return []

        suggestions = []
        for item in response[:3]:  # Limit to 3
            if isinstance(item, dict) and "suggestion" in item:
                suggestions.append(ProjectSuggestion(
                    category=item.get("category", "general"),
                    suggestion=item["suggestion"][:100],  # Bound length
                    impact=item.get("impact", "medium"),
                ))

        # Save suggestions for learning
        if suggestions:
            save_ai_learning(
                user_id=user_id,
                agent_type="project_profile",
                data={"project_suggestions": [s.model_dump() for s in suggestions]},
            )

        return suggestions

    except Exception as e:
        logger.warning(f"⚠️ Failed to generate project suggestions: {str(e)}")
        return []