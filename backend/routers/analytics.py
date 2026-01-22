from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone, timedelta, date
from typing import Optional
from collections import defaultdict
from core.supabase import get_supabase
from core.security import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def parse_date(date_str: str) -> date:
    """Parse date string to date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


@router.get("/time-tracking")
async def get_time_tracking(
    current_user: dict = Depends(get_current_user),
    start_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
):
    """Get time tracking analytics."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Default to last 7 days
    end = date.today() if not end_date else parse_date(end_date)
    start = end - timedelta(days=7) if not start_date else parse_date(start_date)

    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)

    # Get all work sessions in range
    sessions = (
        supabase.table("work_sessions")
        .select("*, tasks(title, project_id, projects(name))")
        .eq("user_id", user_id)
        .gte("start_time", start_dt.isoformat())
        .lt("start_time", end_dt.isoformat())
        .execute()
    )

    # Calculate metrics
    total_focus_time = 0
    daily_breakdown = defaultdict(int)
    project_time = defaultdict(int)
    hourly_distribution = defaultdict(int)

    for session in sessions.data or []:
        start_time = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
        end_time = (
            datetime.fromisoformat(session["end_time"].replace("Z", "+00:00"))
            if session.get("end_time")
            else datetime.now(timezone.utc)
        )

        duration = int((end_time - start_time).total_seconds() / 60)
        total_focus_time += duration

        # Daily breakdown
        day_key = start_time.date().isoformat()
        daily_breakdown[day_key] += duration

        # Project breakdown
        task = session.get("tasks", {})
        project_name = task.get("projects", {}).get("name", "Unknown") if task.get("projects") else "Unknown"
        project_time[project_name] += duration

        # Hourly distribution
        hour = start_time.hour
        hourly_distribution[hour] += duration

    # Find peak hours
    peak_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
    peak_hours_formatted = [f"{h}:00-{h+1}:00" for h, _ in peak_hours]

    # Calculate average daily focus time
    days_count = (end - start).days + 1
    avg_daily_focus = total_focus_time / days_count if days_count > 0 else 0

    return {
        "success": True,
        "data": {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "summary": {
                "total_focus_time": total_focus_time,
                "average_daily_focus": round(avg_daily_focus, 1),
                "total_sessions": len(sessions.data or []),
                "peak_hours": peak_hours_formatted,
            },
            "daily_breakdown": [
                {"date": k, "focus_time": v}
                for k, v in sorted(daily_breakdown.items())
            ],
            "project_breakdown": [
                {"project": k, "focus_time": v}
                for k, v in sorted(project_time.items(), key=lambda x: x[1], reverse=True)
            ],
            "hourly_distribution": [
                {"hour": h, "minutes": hourly_distribution.get(h, 0)}
                for h in range(24)
            ],
        },
    }


@router.get("/productivity-metrics")
async def get_productivity_metrics(
    current_user: dict = Depends(get_current_user),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
):
    """Get productivity metrics and trends."""
    supabase = get_supabase()
    user_id = current_user["id"]

    end = date.today() if not end_date else parse_date(end_date)
    start = end - timedelta(days=7) if not start_date else parse_date(start_date)

    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)

    # Get completed tasks in period
    completed_tasks = (
        supabase.table("tasks")
        .select("id, title, completed_at, estimated_duration, actual_duration, priority")
        .eq("user_id", user_id)
        .eq("status", "completed")
        .gte("completed_at", start_dt.isoformat())
        .lt("completed_at", end_dt.isoformat())
        .execute()
    )

    # Get work sessions
    sessions = (
        supabase.table("work_sessions")
        .select("start_time, end_time, interruptions, energy_before, energy_after")
        .eq("user_id", user_id)
        .gte("start_time", start_dt.isoformat())
        .lt("start_time", end_dt.isoformat())
        .not_.is_("end_time", "null")
        .execute()
    )

    # Get daily check-ins for energy trends
    checkins = (
        supabase.table("daily_check_ins")
        .select("date, energy_level, mood, sleep_quality")
        .eq("user_id", user_id)
        .gte("date", start.isoformat())
        .lte("date", end.isoformat())
        .execute()
    )

    # Calculate metrics
    tasks = completed_tasks.data or []
    total_tasks = len(tasks)

    # Focus time
    total_focus_time = 0
    total_interruptions = 0
    for session in sessions.data or []:
        start_time = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(session["end_time"].replace("Z", "+00:00"))
        total_focus_time += int((end_time - start_time).total_seconds() / 60)
        total_interruptions += session.get("interruptions", 0)

    # Average task duration
    durations = [t["actual_duration"] for t in tasks if t.get("actual_duration")]
    avg_task_duration = sum(durations) / len(durations) if durations else 0

    # Estimation accuracy
    estimation_accuracy = 0
    tasks_with_estimates = [
        t for t in tasks
        if t.get("estimated_duration") and t.get("actual_duration")
    ]
    if tasks_with_estimates:
        accuracies = [
            min(t["estimated_duration"], t["actual_duration"]) /
            max(t["estimated_duration"], t["actual_duration"])
            for t in tasks_with_estimates
        ]
        estimation_accuracy = sum(accuracies) / len(accuracies)

    # Daily breakdown
    daily_breakdown = defaultdict(lambda: {"tasks_completed": 0, "focus_time": 0, "energy_average": None})

    for task in tasks:
        if task.get("completed_at"):
            day = task["completed_at"][:10]
            daily_breakdown[day]["tasks_completed"] += 1

    for session in sessions.data or []:
        start_time = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(session["end_time"].replace("Z", "+00:00"))
        day = start_time.date().isoformat()
        daily_breakdown[day]["focus_time"] += int((end_time - start_time).total_seconds() / 60)

    for checkin in checkins.data or []:
        day = checkin["date"]
        if day in daily_breakdown:
            daily_breakdown[day]["energy_average"] = checkin.get("energy_level")

    # Best day
    best_day = None
    best_day_tasks = 0
    for day, data in daily_breakdown.items():
        if data["tasks_completed"] > best_day_tasks:
            best_day = day
            best_day_tasks = data["tasks_completed"]

    # Calculate productivity score (0-1)
    # Based on: tasks completed, focus time, low interruptions, estimation accuracy
    days_count = (end - start).days + 1
    tasks_per_day = total_tasks / days_count if days_count > 0 else 0
    focus_per_day = total_focus_time / days_count if days_count > 0 else 0

    productivity_score = min(1.0, (
        (min(tasks_per_day / 5, 1) * 0.3) +  # Up to 5 tasks/day
        (min(focus_per_day / 240, 1) * 0.3) +  # Up to 4 hours/day
        (estimation_accuracy * 0.2) +  # Estimation accuracy
        ((1 - min(total_interruptions / (len(sessions.data or []) * 3 + 1), 1)) * 0.2)  # Low interruptions
    ))

    # Energy variance
    energy_levels = [c["energy_level"] for c in (checkins.data or []) if c.get("energy_level")]
    energy_variance = 0
    if len(energy_levels) > 1:
        avg_energy = sum(energy_levels) / len(energy_levels)
        energy_variance = sum((e - avg_energy) ** 2 for e in energy_levels) / len(energy_levels)

    # Trends (compare to previous period)
    prev_start = start - timedelta(days=(end - start).days + 1)
    prev_end = start - timedelta(days=1)
    prev_start_dt = datetime.combine(prev_start, datetime.min.time()).replace(tzinfo=timezone.utc)
    prev_end_dt = datetime.combine(prev_end + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)

    prev_tasks = (
        supabase.table("tasks")
        .select("id")
        .eq("user_id", user_id)
        .eq("status", "completed")
        .gte("completed_at", prev_start_dt.isoformat())
        .lt("completed_at", prev_end_dt.isoformat())
        .execute()
    )

    prev_task_count = len(prev_tasks.data or [])
    task_trend = ((total_tasks - prev_task_count) / prev_task_count) if prev_task_count > 0 else 0

    return {
        "success": True,
        "data": {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "metrics": {
                "total_focus_time": total_focus_time,
                "tasks_completed": total_tasks,
                "average_task_duration": round(avg_task_duration, 1),
                "productivity_score": round(productivity_score, 2),
                "estimation_accuracy": round(estimation_accuracy, 2),
                "total_interruptions": total_interruptions,
                "best_day": {
                    "date": best_day,
                    "tasks_completed": best_day_tasks,
                } if best_day else None,
            },
            "trends": {
                "task_completion_trend": round(task_trend, 2),
                "energy_variance": round(energy_variance, 2),
            },
            "breakdown_by_day": [
                {"date": k, **v}
                for k, v in sorted(daily_breakdown.items())
            ],
        },
    }


@router.get("/project-performance")
async def get_project_performance(
    current_user: dict = Depends(get_current_user),
    project_id: Optional[str] = Query(default=None),
):
    """Get project performance metrics."""
    supabase = get_supabase()
    user_id = current_user["id"]

    # Get projects
    query = supabase.table("projects").select("*").eq("user_id", user_id)
    if project_id:
        query = query.eq("id", project_id)
    else:
        query = query.eq("status", "active")

    projects = query.execute()

    project_metrics = []
    for project in projects.data or []:
        # Get all tasks for this project
        tasks = (
            supabase.table("tasks")
            .select("id, status, priority, estimated_duration, actual_duration, created_at, completed_at")
            .eq("project_id", project["id"])
            .execute()
        )

        task_list = tasks.data or []
        total_tasks = len(task_list)
        completed_tasks = len([t for t in task_list if t["status"] == "completed"])
        in_progress = len([t for t in task_list if t["status"] == "in_progress"])

        # Progress
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Time spent
        sessions = (
            supabase.table("work_sessions")
            .select("start_time, end_time")
            .in_("task_id", [t["id"] for t in task_list])
            .not_.is_("end_time", "null")
            .execute()
        )

        total_time = 0
        for session in sessions.data or []:
            start = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(session["end_time"].replace("Z", "+00:00"))
            total_time += int((end - start).total_seconds() / 60)

        # Velocity (tasks completed per week)
        if task_list:
            first_task = min(t["created_at"] for t in task_list)
            first_date = datetime.fromisoformat(first_task.replace("Z", "+00:00"))
            weeks = max(1, (datetime.now(timezone.utc) - first_date).days / 7)
            velocity = completed_tasks / weeks
        else:
            velocity = 0

        # Status
        if progress >= 100:
            status = "completed"
        elif progress >= 75:
            status = "almost_done"
        elif progress >= 25:
            status = "on_track"
        else:
            status = "just_started"

        project_metrics.append({
            "id": project["id"],
            "name": project["name"],
            "status": status,
            "progress": round(progress, 1),
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "in_progress": in_progress,
                "remaining": total_tasks - completed_tasks,
            },
            "time_spent": total_time,
            "velocity": round(velocity, 2),
            "start_date": project.get("start_date"),
            "target_end_date": project.get("target_end_date"),
        })

    return {
        "success": True,
        "data": {
            "projects": project_metrics,
            "total_projects": len(project_metrics),
        },
    }


@router.get("/goal-progress")
async def get_goal_progress(
    current_user: dict = Depends(get_current_user),
):
    """Get progress towards goals and targets."""
    supabase = get_supabase()
    user_id = current_user["id"]
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Daily goals (today)
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)

    today_completed = (
        supabase.table("tasks")
        .select("id")
        .eq("user_id", user_id)
        .eq("status", "completed")
        .gte("completed_at", today_start.isoformat())
        .lt("completed_at", today_end.isoformat())
        .execute()
    )

    today_sessions = (
        supabase.table("work_sessions")
        .select("start_time, end_time")
        .eq("user_id", user_id)
        .gte("start_time", today_start.isoformat())
        .lt("start_time", today_end.isoformat())
        .execute()
    )

    today_focus = 0
    for s in today_sessions.data or []:
        start = datetime.fromisoformat(s["start_time"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(s["end_time"].replace("Z", "+00:00")) if s.get("end_time") else datetime.now(timezone.utc)
        today_focus += int((end - start).total_seconds() / 60)

    # Weekly goals
    week_start_dt = datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)

    week_completed = (
        supabase.table("tasks")
        .select("id")
        .eq("user_id", user_id)
        .eq("status", "completed")
        .gte("completed_at", week_start_dt.isoformat())
        .execute()
    )

    week_sessions = (
        supabase.table("work_sessions")
        .select("start_time, end_time")
        .eq("user_id", user_id)
        .gte("start_time", week_start_dt.isoformat())
        .not_.is_("end_time", "null")
        .execute()
    )

    week_focus = 0
    for s in week_sessions.data or []:
        start = datetime.fromisoformat(s["start_time"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(s["end_time"].replace("Z", "+00:00"))
        week_focus += int((end - start).total_seconds() / 60)

    # Monthly goals
    month_start_dt = datetime.combine(month_start, datetime.min.time()).replace(tzinfo=timezone.utc)

    month_completed = (
        supabase.table("tasks")
        .select("id")
        .eq("user_id", user_id)
        .eq("status", "completed")
        .gte("completed_at", month_start_dt.isoformat())
        .execute()
    )

    # Get streaks
    streaks = (
        supabase.table("streaks")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    streak_data = {s["streak_type"]: s for s in (streaks.data or [])}

    # Default goals (could be user-configurable later)
    daily_task_goal = 5
    daily_focus_goal = 240  # 4 hours
    weekly_task_goal = 25
    weekly_focus_goal = 1200  # 20 hours

    return {
        "success": True,
        "data": {
            "daily": {
                "tasks": {
                    "completed": len(today_completed.data or []),
                    "goal": daily_task_goal,
                    "progress": min(100, len(today_completed.data or []) / daily_task_goal * 100),
                },
                "focus_time": {
                    "completed": today_focus,
                    "goal": daily_focus_goal,
                    "progress": min(100, today_focus / daily_focus_goal * 100),
                },
            },
            "weekly": {
                "tasks": {
                    "completed": len(week_completed.data or []),
                    "goal": weekly_task_goal,
                    "progress": min(100, len(week_completed.data or []) / weekly_task_goal * 100),
                },
                "focus_time": {
                    "completed": week_focus,
                    "goal": weekly_focus_goal,
                    "progress": min(100, week_focus / weekly_focus_goal * 100),
                },
            },
            "monthly": {
                "tasks_completed": len(month_completed.data or []),
            },
            "streaks": {
                "daily_check_in": {
                    "current": streak_data.get("daily_check_in", {}).get("current_count", 0),
                    "longest": streak_data.get("daily_check_in", {}).get("longest_count", 0),
                },
                "task_completion": {
                    "current": streak_data.get("task_completion", {}).get("current_count", 0),
                    "longest": streak_data.get("task_completion", {}).get("longest_count", 0),
                },
            },
        },
    }
