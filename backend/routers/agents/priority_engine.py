from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(prefix="/priority-engine", tags=["Priority Engine"])


class PriorityAnalyzeRequest(BaseModel):
    project_id: Optional[str] = None
    context: Optional[dict] = None


class RerankRequest(BaseModel):
    task_ids: List[str]
    criteria: Optional[dict] = None


def calculate_priority_score(task: dict, context: dict) -> tuple[float, List[str]]:
    """Calculate priority score for a task."""
    score = 0.0
    reasons = []

    current_energy = context.get("current_energy", 5)
    time_available = context.get("time_available", 120)
    deadline_pressure = context.get("deadline_pressure", "medium")

    # Priority weight
    priority_weights = {"urgent": 40, "high": 30, "medium": 20, "low": 10}
    priority = task.get("priority", "medium")
    score += priority_weights.get(priority, 20)
    if priority in ["urgent", "high"]:
        reasons.append(f"{priority.capitalize()} priority task")

    # Deadline urgency
    if task.get("deadline"):
        try:
            deadline = datetime.fromisoformat(task["deadline"].replace("Z", "+00:00"))
            hours_until = (deadline - datetime.now(timezone.utc)).total_seconds() / 3600

            if hours_until < 0:
                score += 50
                reasons.append("Task is overdue")
            elif hours_until < 24:
                score += 35
                reasons.append("Due within 24 hours")
            elif hours_until < 72:
                score += 20
                reasons.append("Due within 3 days")
        except:
            pass

    # Time fit
    estimated = task.get("estimated_duration") or 30
    if estimated <= time_available:
        score += 15
        if estimated <= time_available * 0.5:
            reasons.append("Fits well within available time")
    else:
        score -= 10

    # Energy match
    task_complexity = min(10, estimated // 15 + 2)
    if abs(current_energy - task_complexity) <= 2:
        score += 10
        reasons.append("Matches your current energy level")

    # Deadline pressure context
    if deadline_pressure == "high" and task.get("deadline"):
        score += 10

    return score, reasons


@router.post("/analyze")
async def analyze_priorities(
    request: PriorityAnalyzeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Analyze and prioritize tasks."""
    supabase = get_supabase()

    query = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .in_("status", ["todo", "in_progress", "paused"])
    )

    if request.project_id:
        query = query.eq("project_id", request.project_id)

    response = query.execute()
    tasks = response.data or []

    context = request.context or {
        "current_energy": 5,
        "time_available": 120,
        "deadline_pressure": "medium",
    }

    # Score and rank tasks
    prioritized = []
    for task in tasks:
        score, reasons = calculate_priority_score(task, context)
        prioritized.append({
            "task_id": task["id"],
            "title": task["title"],
            "project_name": task.get("projects", {}).get("name") if task.get("projects") else None,
            "priority": task["priority"],
            "priority_score": round(score, 2),
            "reasons": reasons,
            "estimated_duration": task.get("estimated_duration"),
            "deadline": task.get("deadline"),
        })

    prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

    # Generate analysis
    analysis = {
        "workload_balance": "optimal" if len(tasks) <= 10 else "heavy",
        "risk_factors": [],
        "optimization_suggestions": [],
    }

    overdue = [t for t in tasks if t.get("deadline") and datetime.fromisoformat(t["deadline"].replace("Z", "+00:00")) < datetime.now(timezone.utc)]
    if overdue:
        analysis["risk_factors"].append(f"{len(overdue)} overdue tasks need immediate attention")

    high_priority = [t for t in tasks if t.get("priority") in ["urgent", "high"]]
    if len(high_priority) > 5:
        analysis["optimization_suggestions"].append("Consider re-evaluating priorities - too many high-priority tasks")

    return {
        "success": True,
        "data": {
            "prioritized_tasks": prioritized[:10],
            "analysis": analysis,
            "total_tasks": len(tasks),
        },
    }


@router.get("/recommendations")
async def get_recommendations(
    current_user: dict = Depends(get_current_user),
    limit: int = 5,
):
    """Get task recommendations based on current context."""
    supabase = get_supabase()

    # Get user's current state
    today = datetime.now(timezone.utc).date().isoformat()
    checkin = (
        supabase.table("daily_check_ins")
        .select("energy_level")
        .eq("user_id", current_user["id"])
        .eq("date", today)
        .single()
        .execute()
    )

    energy = checkin.data.get("energy_level", 5) if checkin.data else 5

    # Get tasks
    tasks = (
        supabase.table("tasks")
        .select("*, projects(name)")
        .eq("user_id", current_user["id"])
        .in_("status", ["todo", "in_progress", "paused"])
        .execute()
    )

    context = {"current_energy": energy, "time_available": 120, "deadline_pressure": "medium"}

    prioritized = []
    for task in tasks.data or []:
        score, reasons = calculate_priority_score(task, context)
        prioritized.append({
            "task_id": task["id"],
            "title": task["title"],
            "project_name": task.get("projects", {}).get("name") if task.get("projects") else None,
            "score": round(score, 2),
            "reasons": reasons,
        })

    prioritized.sort(key=lambda x: x["score"], reverse=True)

    return {
        "success": True,
        "data": {
            "recommendations": prioritized[:limit],
            "context": {"energy_level": energy},
        },
    }


@router.post("/rerank-tasks")
async def rerank_tasks(
    request: RerankRequest,
    current_user: dict = Depends(get_current_user),
):
    """Rerank a specific set of tasks."""
    supabase = get_supabase()

    tasks = (
        supabase.table("tasks")
        .select("*")
        .eq("user_id", current_user["id"])
        .in_("id", request.task_ids)
        .execute()
    )

    context = request.criteria or {"current_energy": 5, "time_available": 120}

    reranked = []
    for task in tasks.data or []:
        score, reasons = calculate_priority_score(task, context)
        reranked.append({
            "task_id": task["id"],
            "title": task["title"],
            "original_priority": task["priority"],
            "computed_score": round(score, 2),
            "reasons": reasons,
        })

    reranked.sort(key=lambda x: x["computed_score"], reverse=True)

    return {
        "success": True,
        "data": {
            "reranked_tasks": reranked,
            "criteria_used": context,
        },
    }
