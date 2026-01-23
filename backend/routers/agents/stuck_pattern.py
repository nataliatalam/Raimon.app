from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel
from core.supabase import get_supabase
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stuck-pattern", tags=["Stuck Pattern Agent"])


class StuckDetectRequest(BaseModel):
    task_id: str
    session_data: Optional[dict] = None


class SuggestSolutionsRequest(BaseModel):
    task_id: str
    stuck_type: Optional[str] = None
    context: Optional[dict] = None


@router.post("/detect")
async def detect_stuck_pattern(
    request: StuckDetectRequest,
    current_user: dict = Depends(get_current_user),
):
    """Detect if user is stuck on a task."""
    try:
        supabase = get_supabase()

        # Get task
        task = (
            supabase.table("tasks")
            .select("*")
            .eq("id", request.task_id)
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not task.data:
            raise HTTPException(status_code=404, detail="Task not found")

        task_data = task.data[0]

        # Get recent sessions for this task
        sessions = (
            supabase.table("work_sessions")
            .select("*")
            .eq("task_id", request.task_id)
            .order("start_time", desc=True)
            .limit(5)
            .execute()
        )

        session_data = request.session_data or {}
        sessions_list = sessions.data or []

        # Analyze for stuck patterns
        stuck_detected = False
        pattern = None
        severity = "low"

        # Pattern 1: High interruptions
        current_interruptions = session_data.get("interruptions", 0)
        if current_interruptions >= 5:
            stuck_detected = True
            pattern = {
                "type": "frequent_context_switching",
                "severity": "medium",
                "description": f"You've been interrupted {current_interruptions} times, preventing deep focus",
            }
            severity = "medium"

        # Pattern 2: Long session with no progress
        duration = session_data.get("duration", 0)
        progress = session_data.get("progress_made", True)
        if duration > 45 and not progress:
            stuck_detected = True
            pattern = {
                "type": "prolonged_no_progress",
                "severity": "high",
                "description": f"You've been working for {duration} minutes without progress",
            }
            severity = "high"

        # Pattern 3: Multiple short sessions
        if len(sessions_list) >= 3:
            short_sessions = [
                s for s in sessions_list
                if s.get("end_time") and
                (datetime.fromisoformat(s["end_time"].replace("Z", "+00:00")) -
                 datetime.fromisoformat(s["start_time"].replace("Z", "+00:00"))).total_seconds() / 60 < 15
            ]
            if len(short_sessions) >= 3:
                stuck_detected = True
                pattern = {
                    "type": "repeated_short_attempts",
                    "severity": "medium",
                    "description": "Multiple short attempts suggest the task may need to be broken down",
                }
                severity = "medium"

        # Pattern 4: Task has been in progress for too long
        if task_data.get("started_at"):
            started = datetime.fromisoformat(task_data["started_at"].replace("Z", "+00:00"))
            days_in_progress = (datetime.now(timezone.utc) - started).days
            estimated = task_data.get("estimated_duration", 60)
            expected_days = max(1, estimated / 480)  # 8 hours per day

            if days_in_progress > expected_days * 3:
                stuck_detected = True
                pattern = {
                    "type": "prolonged_task",
                    "severity": "high",
                    "description": f"Task has been in progress for {days_in_progress} days, much longer than expected",
                }
                severity = "high"

        # Generate suggestions
        suggestions = get_stuck_suggestions(pattern["type"] if pattern else None, severity)

        # Record detection
        if stuck_detected:
            detection_data = {
                "task_id": request.task_id,
                "user_id": current_user["id"],
                "pattern_type": pattern["type"],
                "description": pattern["description"],
                "severity": severity,
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "suggested_actions": suggestions,
            }
            supabase.table("stuck_pattern_detections").insert(detection_data).execute()

        return {
            "success": True,
            "data": {
                "stuck_detected": stuck_detected,
                "pattern": pattern,
                "suggestions": suggestions,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detect_stuck_pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect stuck pattern",
        )


def get_stuck_suggestions(pattern_type: Optional[str], severity: str) -> List[dict]:
    """Get suggestions based on stuck pattern."""
    base_suggestions = {
        "frequent_context_switching": [
            {"action": "enable_focus_mode", "reason": "Block notifications and interruptions", "priority": 1},
            {"action": "take_short_break", "reason": "Reset your focus", "duration": 5, "priority": 2},
            {"action": "change_environment", "reason": "Find a quieter workspace", "priority": 3},
        ],
        "prolonged_no_progress": [
            {"action": "take_break", "reason": "Step away to clear your mind", "duration": 15, "priority": 1},
            {"action": "break_down_task", "reason": "Split into smaller, manageable pieces", "priority": 2},
            {"action": "ask_for_help", "reason": "Get a fresh perspective", "priority": 3},
            {"action": "switch_task", "reason": "Work on something else and return later", "priority": 4},
        ],
        "repeated_short_attempts": [
            {"action": "break_down_task", "reason": "Task may be too large or unclear", "priority": 1},
            {"action": "clarify_requirements", "reason": "Ensure you understand what's needed", "priority": 2},
            {"action": "identify_blocker", "reason": "What specifically is preventing progress?", "priority": 3},
        ],
        "prolonged_task": [
            {"action": "review_scope", "reason": "Is the task scope still appropriate?", "priority": 1},
            {"action": "get_feedback", "reason": "Check if you're on the right track", "priority": 2},
            {"action": "consider_alternatives", "reason": "Is there a simpler approach?", "priority": 3},
            {"action": "escalate", "reason": "Raise visibility if blocked by external factors", "priority": 4},
        ],
    }

    if pattern_type and pattern_type in base_suggestions:
        return base_suggestions[pattern_type]

    # Default suggestions
    return [
        {"action": "take_break", "reason": "Clear your mind", "duration": 10, "priority": 1},
        {"action": "review_task", "reason": "Re-read the task requirements", "priority": 2},
        {"action": "ask_for_help", "reason": "Get a fresh perspective", "priority": 3},
    ]


@router.get("/analysis")
async def get_stuck_analysis(
    current_user: dict = Depends(get_current_user),
    days: int = 30,
):
    """Get analysis of stuck patterns over time."""
    try:
        supabase = get_supabase()

        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        detections = (
            supabase.table("stuck_pattern_detections")
            .select("*")
            .eq("user_id", current_user["id"])
            .gte("detected_at", start_date)
            .execute()
        )

        data = detections.data or []

        if not data:
            return {
                "success": True,
                "data": {
                    "message": "No stuck patterns detected in this period",
                    "total_detections": 0,
                },
            }

        # Analyze patterns
        pattern_counts = {}
        severity_counts = {"low": 0, "medium": 0, "high": 0}

        for detection in data:
            pattern_type = detection.get("pattern_type", "unknown")
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
            severity = detection.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        most_common = max(pattern_counts.items(), key=lambda x: x[1]) if pattern_counts else (None, 0)

        return {
            "success": True,
            "data": {
                "period_days": days,
                "total_detections": len(data),
                "pattern_breakdown": pattern_counts,
                "severity_breakdown": severity_counts,
                "most_common_pattern": {
                    "type": most_common[0],
                    "count": most_common[1],
                },
                "recommendations": get_pattern_recommendations(most_common[0]),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_stuck_analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stuck analysis",
        )


def get_pattern_recommendations(common_pattern: Optional[str]) -> List[str]:
    """Get recommendations based on most common stuck pattern."""
    recommendations = {
        "frequent_context_switching": [
            "Schedule dedicated focus blocks with notifications off",
            "Communicate your focus times to colleagues",
            "Use 'Do Not Disturb' features on your devices",
        ],
        "prolonged_no_progress": [
            "Practice breaking tasks down before starting",
            "Set smaller milestones within larger tasks",
            "Don't hesitate to ask for help earlier",
        ],
        "repeated_short_attempts": [
            "Spend more time on task planning before execution",
            "Identify dependencies and blockers upfront",
            "Consider if tasks need different skills or resources",
        ],
        "prolonged_task": [
            "Review estimation practices",
            "Set intermediate deadlines for long tasks",
            "Have regular check-ins on long-running work",
        ],
    }

    return recommendations.get(common_pattern, [
        "Track what causes you to get stuck",
        "Build in buffer time for complex tasks",
        "Regular breaks can prevent getting stuck",
    ])


@router.post("/suggest-solutions")
async def suggest_solutions(
    request: SuggestSolutionsRequest,
    current_user: dict = Depends(get_current_user),
):
    """Get personalized solutions for being stuck."""
    try:
        supabase = get_supabase()

        # Get task details
        task = (
            supabase.table("tasks")
            .select("*, projects(name)")
            .eq("id", request.task_id)
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not task.data:
            raise HTTPException(status_code=404, detail="Task not found")

        task_data = task.data[0]

        # Get recent detections for this task
        recent_detections = (
            supabase.table("stuck_pattern_detections")
            .select("pattern_type, severity")
            .eq("task_id", request.task_id)
            .order("detected_at", desc=True)
            .limit(3)
            .execute()
        )

        # Determine stuck type
        stuck_type = request.stuck_type
        if not stuck_type and recent_detections.data:
            stuck_type = recent_detections.data[0].get("pattern_type")

        # Get base suggestions
        suggestions = get_stuck_suggestions(stuck_type, "medium")

        # Add task-specific suggestions
        if task_data.get("estimated_duration", 0) > 120:
            suggestions.insert(0, {
                "action": "time_box",
                "reason": f"Large task ({task_data.get('estimated_duration')} min) - try working in 25-min focused blocks",
                "priority": 0,
            })

        if task_data.get("priority") == "urgent":
            suggestions.append({
                "action": "escalate",
                "reason": "Urgent task - consider getting help to unblock faster",
                "priority": 1,
            })

        return {
            "success": True,
            "data": {
                "task": {
                    "id": task_data["id"],
                    "title": task_data["title"],
                    "project_name": task_data.get("projects", {}).get("name") if task_data.get("projects") else None,
                },
                "stuck_type": stuck_type,
                "solutions": suggestions,
                "encouragement": "Getting stuck is normal - recognizing it is the first step to breaking through!",
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in suggest_solutions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suggest solutions",
        )
