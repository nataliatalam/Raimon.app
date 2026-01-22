from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(prefix="/project-insight", tags=["Project Insight Engine"])


@router.get("/{project_id}/completion-prediction")
async def get_completion_prediction(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Predict project completion based on current progress."""
    supabase = get_supabase()

    # Verify project ownership
    project = (
        supabase.table("projects")
        .select("*")
        .eq("id", project_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all tasks
    tasks = (
        supabase.table("tasks")
        .select("id, status, estimated_duration, actual_duration, created_at, completed_at")
        .eq("project_id", project_id)
        .execute()
    )

    task_list = tasks.data or []
    total_tasks = len(task_list)

    if total_tasks == 0:
        return {
            "success": True,
            "data": {
                "message": "No tasks in project yet",
                "completion_probability": None,
            },
        }

    completed = [t for t in task_list if t["status"] == "completed"]
    in_progress = [t for t in task_list if t["status"] == "in_progress"]
    remaining = [t for t in task_list if t["status"] in ["todo", "paused"]]

    # Calculate velocity
    if completed:
        # Find date range of completions
        completion_dates = [
            datetime.fromisoformat(t["completed_at"].replace("Z", "+00:00"))
            for t in completed if t.get("completed_at")
        ]
        if len(completion_dates) >= 2:
            date_range = (max(completion_dates) - min(completion_dates)).days or 1
            velocity = len(completed) / date_range  # tasks per day
        else:
            velocity = 0.5  # Default assumption
    else:
        velocity = 0.3  # Conservative estimate

    # Estimate remaining work
    remaining_estimated = sum(t.get("estimated_duration", 60) for t in remaining + in_progress)
    completed_actual = sum(t.get("actual_duration", t.get("estimated_duration", 60)) for t in completed)
    completed_estimated = sum(t.get("estimated_duration", 60) for t in completed)

    # Adjust for estimation accuracy
    if completed_estimated > 0:
        estimation_factor = completed_actual / completed_estimated
    else:
        estimation_factor = 1.2  # Assume underestimation

    adjusted_remaining = remaining_estimated * estimation_factor

    # Calculate projected completion
    days_remaining = (len(remaining) + len(in_progress)) / velocity if velocity > 0 else 999
    projected_date = datetime.now(timezone.utc) + timedelta(days=days_remaining)

    # Calculate completion probability
    target_date = None
    if project.data.get("target_end_date"):
        target_date = datetime.fromisoformat(project.data["target_end_date"] + "T23:59:59+00:00")
        days_until_target = (target_date - datetime.now(timezone.utc)).days

        if days_until_target <= 0:
            probability = 0.1 if remaining else 0.9
        elif days_remaining <= days_until_target:
            probability = min(0.95, 0.6 + (days_until_target - days_remaining) / days_until_target * 0.35)
        else:
            overage = days_remaining - days_until_target
            probability = max(0.1, 0.6 - overage / days_until_target * 0.5)
    else:
        probability = 0.7  # No target, moderate confidence

    progress = (len(completed) / total_tasks * 100) if total_tasks > 0 else 0

    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "project_name": project.data["name"],
            "completion_probability": round(probability, 2),
            "projected_completion_date": projected_date.date().isoformat(),
            "target_end_date": project.data.get("target_end_date"),
            "progress": {
                "percentage": round(progress, 1),
                "completed_tasks": len(completed),
                "in_progress_tasks": len(in_progress),
                "remaining_tasks": len(remaining),
                "total_tasks": total_tasks,
            },
            "velocity": {
                "tasks_per_day": round(velocity, 2),
                "estimation_accuracy": round(1 / estimation_factor, 2) if estimation_factor else None,
            },
            "confidence": "high" if len(completed) >= 5 else "medium" if len(completed) >= 2 else "low",
        },
    }


@router.get("/{project_id}/risk-analysis")
async def get_risk_analysis(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Analyze risks for a project."""
    supabase = get_supabase()

    # Verify project ownership
    project = (
        supabase.table("projects")
        .select("*")
        .eq("id", project_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get tasks
    tasks = (
        supabase.table("tasks")
        .select("*")
        .eq("project_id", project_id)
        .execute()
    )

    task_list = tasks.data or []
    risks = []

    # Risk 1: Overdue tasks
    now = datetime.now(timezone.utc)
    overdue = [
        t for t in task_list
        if t.get("deadline") and
        datetime.fromisoformat(t["deadline"].replace("Z", "+00:00")) < now and
        t["status"] != "completed"
    ]
    if overdue:
        risks.append({
            "type": "overdue_tasks",
            "severity": "high" if len(overdue) > 2 else "medium",
            "description": f"{len(overdue)} tasks are overdue",
            "affected_tasks": [t["title"] for t in overdue[:3]],
            "recommendation": "Prioritize overdue tasks or adjust deadlines",
        })

    # Risk 2: Too many high priority tasks
    high_priority = [t for t in task_list if t.get("priority") in ["urgent", "high"] and t["status"] != "completed"]
    if len(high_priority) > 5:
        risks.append({
            "type": "priority_overload",
            "severity": "medium",
            "description": f"{len(high_priority)} high/urgent priority tasks",
            "recommendation": "Re-evaluate priorities - not everything can be urgent",
        })

    # Risk 3: Blocked tasks
    blocked = [t for t in task_list if t.get("status") == "blocked"]
    if blocked:
        risks.append({
            "type": "blocked_tasks",
            "severity": "high" if len(blocked) > 1 else "medium",
            "description": f"{len(blocked)} tasks are blocked",
            "affected_tasks": [t["title"] for t in blocked],
            "recommendation": "Identify and resolve blockers",
        })

    # Risk 4: Target date at risk
    if project.data.get("target_end_date"):
        target = datetime.fromisoformat(project.data["target_end_date"] + "T23:59:59+00:00")
        remaining = [t for t in task_list if t["status"] not in ["completed"]]
        remaining_estimate = sum(t.get("estimated_duration", 60) for t in remaining)
        days_until_target = (target - now).days
        work_days_needed = remaining_estimate / 480  # 8 hours per day

        if work_days_needed > days_until_target:
            risks.append({
                "type": "deadline_risk",
                "severity": "high",
                "description": f"Estimated work ({round(work_days_needed, 1)} days) exceeds time remaining ({days_until_target} days)",
                "recommendation": "Consider scope reduction or deadline extension",
            })

    # Risk 5: Stalled progress
    completed = [t for t in task_list if t["status"] == "completed"]
    if completed:
        last_completion = max(
            datetime.fromisoformat(t["completed_at"].replace("Z", "+00:00"))
            for t in completed if t.get("completed_at")
        )
        days_since_completion = (now - last_completion).days
        if days_since_completion > 7 and len(task_list) - len(completed) > 0:
            risks.append({
                "type": "stalled_progress",
                "severity": "medium",
                "description": f"No task completed in the last {days_since_completion} days",
                "recommendation": "Review blockers and team capacity",
            })

    # Calculate overall risk level
    high_risks = len([r for r in risks if r["severity"] == "high"])
    medium_risks = len([r for r in risks if r["severity"] == "medium"])

    if high_risks >= 2:
        overall_risk = "critical"
    elif high_risks == 1 or medium_risks >= 3:
        overall_risk = "high"
    elif medium_risks >= 1:
        overall_risk = "medium"
    else:
        overall_risk = "low"

    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "project_name": project.data["name"],
            "overall_risk_level": overall_risk,
            "risks": risks,
            "risk_count": {
                "high": high_risks,
                "medium": medium_risks,
                "low": len([r for r in risks if r["severity"] == "low"]),
            },
        },
    }


@router.get("/{project_id}/optimization-suggestions")
async def get_optimization_suggestions(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get optimization suggestions for a project."""
    supabase = get_supabase()

    # Verify project ownership
    project = (
        supabase.table("projects")
        .select("*")
        .eq("id", project_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get tasks
    tasks = (
        supabase.table("tasks")
        .select("*")
        .eq("project_id", project_id)
        .execute()
    )

    task_list = tasks.data or []
    suggestions = []

    # Suggestion 1: Large tasks
    large_tasks = [t for t in task_list if (t.get("estimated_duration") or 0) > 240 and t["status"] != "completed"]
    if large_tasks:
        suggestions.append({
            "type": "break_down_tasks",
            "priority": "high",
            "description": f"{len(large_tasks)} tasks estimated at 4+ hours",
            "action": "Break these into smaller, more manageable pieces",
            "affected_tasks": [t["title"] for t in large_tasks[:3]],
        })

    # Suggestion 2: Tasks without estimates
    no_estimate = [t for t in task_list if not t.get("estimated_duration") and t["status"] != "completed"]
    if no_estimate:
        suggestions.append({
            "type": "add_estimates",
            "priority": "medium",
            "description": f"{len(no_estimate)} tasks have no time estimate",
            "action": "Add estimates to improve planning accuracy",
        })

    # Suggestion 3: Rebalance priorities
    priority_counts = {"urgent": 0, "high": 0, "medium": 0, "low": 0}
    for t in task_list:
        if t["status"] != "completed":
            priority_counts[t.get("priority", "medium")] += 1

    total_incomplete = sum(priority_counts.values())
    if total_incomplete > 0:
        high_ratio = (priority_counts["urgent"] + priority_counts["high"]) / total_incomplete
        if high_ratio > 0.5:
            suggestions.append({
                "type": "rebalance_priorities",
                "priority": "medium",
                "description": f"{int(high_ratio * 100)}% of tasks are high/urgent priority",
                "action": "Re-evaluate - consider if some tasks can be medium or low priority",
            })

    # Suggestion 4: Tasks without deadlines
    no_deadline = [t for t in task_list if not t.get("deadline") and t["status"] not in ["completed"]]
    if len(no_deadline) > total_incomplete * 0.5:
        suggestions.append({
            "type": "add_deadlines",
            "priority": "low",
            "description": f"{len(no_deadline)} tasks have no deadline",
            "action": "Add deadlines to improve prioritization",
        })

    # Suggestion 5: Quick wins available
    quick_wins = [
        t for t in task_list
        if (t.get("estimated_duration") or 60) <= 30 and
        t["status"] == "todo" and
        t.get("priority") in ["medium", "high"]
    ]
    if quick_wins:
        suggestions.append({
            "type": "quick_wins",
            "priority": "info",
            "description": f"{len(quick_wins)} quick tasks (30 min or less) available",
            "action": "Consider tackling these for momentum",
            "affected_tasks": [t["title"] for t in quick_wins[:3]],
        })

    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "project_name": project.data["name"],
            "suggestions": suggestions,
            "summary": {
                "total_tasks": len(task_list),
                "completed": len([t for t in task_list if t["status"] == "completed"]),
                "in_progress": len([t for t in task_list if t["status"] == "in_progress"]),
            },
        },
    }
