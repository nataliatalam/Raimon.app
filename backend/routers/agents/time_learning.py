from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel
from collections import defaultdict
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(prefix="/time-learning", tags=["Time Learning Agent"])


class TimeTrackRequest(BaseModel):
    task_id: str
    actual_duration: int
    estimated_duration: Optional[int] = None
    factors: Optional[dict] = None


@router.post("/track")
async def track_time_data(
    request: TimeTrackRequest,
    current_user: dict = Depends(get_current_user),
):
    """Track time data for learning purposes."""
    supabase = get_supabase()

    # Get task details
    task = (
        supabase.table("tasks")
        .select("*")
        .eq("id", request.task_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )

    if not task.data:
        raise HTTPException(status_code=404, detail="Task not found")

    # Calculate accuracy if we have an estimate
    estimated = request.estimated_duration or task.data.get("estimated_duration")
    accuracy = None
    if estimated:
        accuracy = min(estimated, request.actual_duration) / max(estimated, request.actual_duration)

    # Store learning data
    learning_data = {
        "user_id": current_user["id"],
        "task_id": request.task_id,
        "agent_type": "time_learning",
        "data": {
            "actual_duration": request.actual_duration,
            "estimated_duration": estimated,
            "accuracy": accuracy,
            "task_priority": task.data.get("priority"),
            "factors": request.factors or {},
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    supabase.table("ai_learning_data").insert(learning_data).execute()

    # Store prediction for future reference
    if estimated:
        prediction_data = {
            "task_id": request.task_id,
            "predicted_duration": estimated,
            "actual_duration": request.actual_duration,
            "accuracy": accuracy,
            "factors": request.factors,
        }
        supabase.table("task_time_predictions").insert(prediction_data).execute()

    return {
        "success": True,
        "data": {
            "tracked": True,
            "accuracy": round(accuracy, 2) if accuracy else None,
            "feedback": get_accuracy_feedback(accuracy),
        },
    }


def get_accuracy_feedback(accuracy: Optional[float]) -> str:
    """Generate feedback based on estimation accuracy."""
    if accuracy is None:
        return "No estimate to compare"
    if accuracy >= 0.9:
        return "Excellent estimation!"
    elif accuracy >= 0.7:
        return "Good estimate, minor adjustment needed"
    elif accuracy >= 0.5:
        return "Estimate was off - consider breaking down tasks more"
    else:
        return "Large gap between estimate and actual - review task complexity"


@router.get("/predictions")
async def get_time_predictions(
    current_user: dict = Depends(get_current_user),
):
    """Get time predictions and patterns for the user."""
    supabase = get_supabase()

    # Get historical time data
    learning_data = (
        supabase.table("ai_learning_data")
        .select("data")
        .eq("user_id", current_user["id"])
        .eq("agent_type", "time_learning")
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )

    if not learning_data.data:
        return {
            "success": True,
            "data": {
                "message": "Not enough data for predictions yet",
                "predictions": [],
            },
        }

    # Analyze patterns
    by_priority = defaultdict(list)
    total_accuracy = []

    for record in learning_data.data:
        data = record.get("data", {})
        if data.get("accuracy"):
            total_accuracy.append(data["accuracy"])
        if data.get("task_priority") and data.get("actual_duration"):
            by_priority[data["task_priority"]].append(data["actual_duration"])

    # Calculate averages by priority
    priority_predictions = {}
    for priority, durations in by_priority.items():
        avg = sum(durations) / len(durations)
        priority_predictions[priority] = {
            "average_duration": round(avg, 0),
            "sample_size": len(durations),
            "confidence": min(0.95, 0.5 + len(durations) * 0.05),
        }

    # Overall accuracy
    avg_accuracy = sum(total_accuracy) / len(total_accuracy) if total_accuracy else 0

    # Get work sessions for hourly patterns
    sessions = (
        supabase.table("work_sessions")
        .select("start_time, end_time")
        .eq("user_id", current_user["id"])
        .not_.is_("end_time", "null")
        .order("start_time", desc=True)
        .limit(200)
        .execute()
    )

    hourly_productivity = defaultdict(list)
    for session in sessions.data or []:
        start = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(session["end_time"].replace("Z", "+00:00"))
        duration = (end - start).total_seconds() / 60
        hour = start.hour
        hourly_productivity[hour].append(duration)

    # Find peak hours
    hourly_avg = {h: sum(d) / len(d) for h, d in hourly_productivity.items() if d}
    peak_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "success": True,
        "data": {
            "predictions": {
                "by_priority": priority_predictions,
            },
            "performance_insights": {
                "estimation_accuracy": round(avg_accuracy, 2),
                "peak_performance_hours": [f"{h}:00" for h, _ in peak_hours],
                "total_tracked_tasks": len(learning_data.data),
            },
        },
    }


@router.get("/performance-insights")
async def get_performance_insights(
    current_user: dict = Depends(get_current_user),
    days: int = 30,
):
    """Get detailed performance insights."""
    supabase = get_supabase()

    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Get completed tasks
    tasks = (
        supabase.table("tasks")
        .select("estimated_duration, actual_duration, priority, completed_at")
        .eq("user_id", current_user["id"])
        .eq("status", "completed")
        .gte("completed_at", start_date)
        .execute()
    )

    # Get work sessions
    sessions = (
        supabase.table("work_sessions")
        .select("start_time, end_time, interruptions, energy_before, energy_after")
        .eq("user_id", current_user["id"])
        .gte("start_time", start_date)
        .not_.is_("end_time", "null")
        .execute()
    )

    # Calculate insights
    tasks_data = tasks.data or []
    sessions_data = sessions.data or []

    # Estimation accuracy over time
    accuracy_data = []
    for task in tasks_data:
        if task.get("estimated_duration") and task.get("actual_duration"):
            acc = min(task["estimated_duration"], task["actual_duration"]) / max(task["estimated_duration"], task["actual_duration"])
            accuracy_data.append({
                "date": task["completed_at"][:10],
                "accuracy": acc,
            })

    # Average accuracy
    avg_accuracy = sum(a["accuracy"] for a in accuracy_data) / len(accuracy_data) if accuracy_data else 0

    # Improvement trend
    improvement = 0
    if len(accuracy_data) >= 10:
        first_half = sum(a["accuracy"] for a in accuracy_data[len(accuracy_data)//2:]) / (len(accuracy_data) // 2)
        second_half = sum(a["accuracy"] for a in accuracy_data[:len(accuracy_data)//2]) / (len(accuracy_data) // 2)
        improvement = second_half - first_half

    # Session analysis
    total_focus_time = 0
    total_interruptions = 0
    energy_changes = []

    for session in sessions_data:
        start = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(session["end_time"].replace("Z", "+00:00"))
        total_focus_time += (end - start).total_seconds() / 60
        total_interruptions += session.get("interruptions", 0)

        if session.get("energy_before") and session.get("energy_after"):
            energy_changes.append(session["energy_after"] - session["energy_before"])

    avg_session_length = total_focus_time / len(sessions_data) if sessions_data else 0
    avg_energy_change = sum(energy_changes) / len(energy_changes) if energy_changes else 0

    return {
        "success": True,
        "data": {
            "period_days": days,
            "estimation_insights": {
                "average_accuracy": round(avg_accuracy, 2),
                "improvement_trend": round(improvement, 3),
                "tasks_analyzed": len(accuracy_data),
            },
            "session_insights": {
                "total_focus_time": round(total_focus_time, 0),
                "average_session_length": round(avg_session_length, 0),
                "total_interruptions": total_interruptions,
                "interruptions_per_session": round(total_interruptions / len(sessions_data), 1) if sessions_data else 0,
            },
            "energy_insights": {
                "average_energy_change": round(avg_energy_change, 2),
                "interpretation": "Work tends to drain energy" if avg_energy_change < -0.5 else "Energy stays stable during work" if abs(avg_energy_change) <= 0.5 else "Work tends to energize you",
            },
            "recommendations": generate_performance_recommendations(avg_accuracy, avg_session_length, total_interruptions / max(len(sessions_data), 1)),
        },
    }


def generate_performance_recommendations(accuracy: float, avg_session: float, interruptions_per_session: float) -> List[str]:
    """Generate recommendations based on performance data."""
    recommendations = []

    if accuracy < 0.6:
        recommendations.append("Break down tasks into smaller pieces for better estimation")
    if accuracy < 0.8:
        recommendations.append("Add buffer time to estimates (try 1.2x multiplier)")

    if avg_session < 25:
        recommendations.append("Try to extend focus sessions - aim for 25-50 minute blocks")
    elif avg_session > 90:
        recommendations.append("Consider taking breaks every 60-90 minutes")

    if interruptions_per_session > 2:
        recommendations.append("High interruption rate - consider blocking notifications during focus time")

    if not recommendations:
        recommendations.append("Great performance! Keep up the good work.")

    return recommendations
