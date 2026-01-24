from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List
from pydantic import BaseModel
from core.supabase import get_supabase
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/motivation", tags=["Streak & Motivation"])


class CelebrateRequest(BaseModel):
    achievement_type: str
    context: Optional[dict] = None


@router.get("/streaks")
async def get_streaks(
    current_user: dict = Depends(get_current_user),
):
    """Get user's active streaks."""
    try:
        supabase = get_supabase()

        streaks = (
            supabase.table("streaks")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )

        streak_data = []
        for streak in streaks.data or []:
            # Calculate next milestone
            current = streak.get("current_count", 0)
            milestones = [3, 7, 14, 30, 60, 100, 365]
            next_milestone = next((m for m in milestones if m > current), None)

            streak_info = {
                "type": streak["streak_type"],
                "current": current,
                "longest": streak.get("longest_count", current),
                "last_activity": streak.get("last_activity_date"),
                "next_milestone": next_milestone,
                "milestone_reward": get_milestone_reward(streak["streak_type"], next_milestone) if next_milestone else None,
            }
            streak_data.append(streak_info)

        # Add default streaks if not present
        streak_types = [s["type"] for s in streak_data]
        defaults = ["daily_check_in", "task_completion", "focus_session"]
        for default in defaults:
            if default not in streak_types:
                streak_data.append({
                    "type": default,
                    "current": 0,
                    "longest": 0,
                    "next_milestone": 3,
                    "milestone_reward": get_milestone_reward(default, 3),
                })

        return {
            "success": True,
            "data": {
                "active_streaks": streak_data,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_streaks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get streaks",
        )


def get_milestone_reward(streak_type: str, milestone: int) -> str:
    """Get reward description for a milestone."""
    rewards = {
        "daily_check_in": {
            3: "Consistent Starter badge",
            7: "Week Warrior badge",
            14: "Fortnight Focus badge",
            30: "Monthly Master badge",
            60: "Dedication badge",
            100: "Century badge",
            365: "Year Champion badge",
        },
        "task_completion": {
            3: "Task Tackler badge",
            7: "Productivity Pro badge",
            14: "Achievement Hunter badge",
            30: "Task Master badge",
        },
        "focus_session": {
            3: "Focus Finder badge",
            7: "Deep Worker badge",
            14: "Flow State badge",
            30: "Concentration Champion badge",
        },
    }

    return rewards.get(streak_type, {}).get(milestone, f"{milestone}-day streak badge")


@router.get("/badges")
async def get_badges(
    current_user: dict = Depends(get_current_user),
):
    """Get user's earned badges and achievements."""
    try:
        supabase = get_supabase()

        achievements = (
            supabase.table("user_achievements")
            .select("*, achievements(*)")
            .eq("user_id", current_user["id"])
            .order("earned_at", desc=True)
            .execute()
        )

        earned = []
        for ua in achievements.data or []:
            achievement = ua.get("achievements", {})
            earned.append({
                "id": ua["achievement_id"],
                "name": achievement.get("name", "Unknown"),
                "description": achievement.get("description"),
                "icon": achievement.get("icon"),
                "category": achievement.get("category"),
                "points": achievement.get("points", 0),
                "earned_at": ua["earned_at"],
            })

        # Get total points
        total_points = sum(b["points"] for b in earned)

        # Get available achievements
        all_achievements = (
            supabase.table("achievements")
            .select("*")
            .execute()
        )

        earned_ids = [e["id"] for e in earned]
        available = [
            {
                "id": a["id"],
                "name": a["name"],
                "description": a["description"],
                "icon": a.get("icon"),
                "category": a.get("category"),
                "points": a.get("points", 0),
                "requirements": a.get("requirements"),
            }
            for a in (all_achievements.data or [])
            if a["id"] not in earned_ids
        ]

        return {
            "success": True,
            "data": {
                "earned_badges": earned,
                "available_badges": available[:10],  # Show some available
                "total_points": total_points,
                "badge_count": len(earned),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_badges: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get badges",
        )


@router.post("/celebrate")
async def celebrate_achievement(
    request: CelebrateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Record a celebration for an achievement."""
    try:
        supabase = get_supabase()

        # Record the celebration
        celebration_data = {
            "user_id": current_user["id"],
            "agent_type": "motivation",
            "data": {
                "achievement_type": request.achievement_type,
                "context": request.context,
                "celebrated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        supabase.table("ai_learning_data").insert(celebration_data).execute()

        # Generate celebration message
        messages = {
            "task_completed": [
                "Great job completing that task!",
                "Another one done! You're on fire!",
                "Task crushed! Keep up the momentum!",
            ],
            "streak_milestone": [
                "Amazing streak! Consistency is key!",
                "You're building great habits!",
                "Milestone reached! Celebrate your dedication!",
            ],
            "project_completed": [
                "Project completed! That's a major achievement!",
                "You did it! Time to celebrate!",
                "Another project in the books! Well done!",
            ],
            "focus_session": [
                "Great focus session!",
                "Deep work pays off!",
                "Excellent concentration!",
            ],
        }

        import random
        message_list = messages.get(request.achievement_type, ["Great work!"])
        message = random.choice(message_list)

        return {
            "success": True,
            "data": {
                "message": message,
                "celebrated": True,
                "achievement_type": request.achievement_type,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in celebrate_achievement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to celebrate achievement",
        )


@router.get("/challenges")
async def get_challenges(
    current_user: dict = Depends(get_current_user),
):
    """Get available challenges for the user."""
    try:
        supabase = get_supabase()
        today = date.today()

        # Get user's current stats
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        # Tasks completed today
        completed_today = (
            supabase.table("tasks")
            .select("id")
            .eq("user_id", current_user["id"])
            .eq("status", "completed")
            .gte("completed_at", today_start.isoformat())
            .execute()
        )

        # Focus time today
        sessions_today = (
            supabase.table("work_sessions")
            .select("start_time, end_time")
            .eq("user_id", current_user["id"])
            .gte("start_time", today_start.isoformat())
            .execute()
        )

        focus_today = 0
        for s in sessions_today.data or []:
            start = datetime.fromisoformat(s["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(s["end_time"].replace("Z", "+00:00")) if s.get("end_time") else datetime.now(timezone.utc)
            focus_today += int((end - start).total_seconds() / 60)

        # Get streak
        streak = (
            supabase.table("streaks")
            .select("current_count")
            .eq("user_id", current_user["id"])
            .eq("streak_type", "daily_check_in")
            .execute()
        )

        current_streak = streak.data[0].get("current_count", 0) if streak.data else 0

        # Generate challenges
        challenges = []

        # Daily task challenge
        tasks_completed = len(completed_today.data or [])
        challenges.append({
            "id": "daily_tasks",
            "name": "Daily Task Champion",
            "description": "Complete 5 tasks today",
            "type": "daily",
            "target": 5,
            "current": tasks_completed,
            "progress": min(100, tasks_completed / 5 * 100),
            "completed": tasks_completed >= 5,
            "reward_points": 50,
        })

        # Focus challenge
        challenges.append({
            "id": "focus_time",
            "name": "Deep Focus",
            "description": "Accumulate 2 hours of focus time today",
            "type": "daily",
            "target": 120,
            "current": focus_today,
            "progress": min(100, focus_today / 120 * 100),
            "completed": focus_today >= 120,
            "reward_points": 75,
        })

        # Streak challenge
        next_streak_goal = next((m for m in [3, 7, 14, 30] if m > current_streak), 30)
        challenges.append({
            "id": "streak_challenge",
            "name": f"{next_streak_goal}-Day Streak",
            "description": f"Maintain a {next_streak_goal}-day check-in streak",
            "type": "streak",
            "target": next_streak_goal,
            "current": current_streak,
            "progress": min(100, current_streak / next_streak_goal * 100),
            "completed": current_streak >= next_streak_goal,
            "reward_points": next_streak_goal * 10,
        })

        # Weekly challenge (if it's Monday-Friday)
        if today.weekday() < 5:
            week_start = today - timedelta(days=today.weekday())
            week_start_dt = datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)

            week_completed = (
                supabase.table("tasks")
                .select("id")
                .eq("user_id", current_user["id"])
                .eq("status", "completed")
                .gte("completed_at", week_start_dt.isoformat())
                .execute()
            )

            week_count = len(week_completed.data or [])
            challenges.append({
                "id": "weekly_tasks",
                "name": "Weekly Warrior",
                "description": "Complete 20 tasks this week",
                "type": "weekly",
                "target": 20,
                "current": week_count,
                "progress": min(100, week_count / 20 * 100),
                "completed": week_count >= 20,
                "reward_points": 150,
            })

        return {
            "success": True,
            "data": {
                "challenges": challenges,
                "active_count": len([c for c in challenges if not c["completed"]]),
                "completed_today": len([c for c in challenges if c["completed"] and c["type"] == "daily"]),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_challenges: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get challenges",
        )
