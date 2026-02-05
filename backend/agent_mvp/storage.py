"""
Storage - Supabase operations for new tables.

New tables to support:
- active_do: Current active task/session
- session_state: User session state persistence
- stuck_episodes: Stuck detection history
- time_models: Time pattern learning data
- insights: Generated insights storage
- xp_ledger: XP transaction history
- gamification_state: User gamification data
- agent_events: Event logging for agents

All operations use get_supabase() helper.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from core.supabase import get_supabase, get_supabase_admin
from opik import track
import logging

logger = logging.getLogger(__name__)

_agent_service_role_warning_logged = False


def _get_agent_supabase():
    """Prefer service-role client for agent writes; fallback safely if missing."""
    global _agent_service_role_warning_logged
    supabase_admin = get_supabase_admin()
    if supabase_admin is get_supabase() and not _agent_service_role_warning_logged:
        logger.warning(
            "SUPABASE_SERVICE_ROLE_KEY missing; agent writes are using anon client and may fail."
        )
        _agent_service_role_warning_logged = True
    return supabase_admin


def _json_safe(value: Any) -> Any:
    """Recursively convert non-JSON-native values (e.g., datetime) to JSON-safe values."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_json_safe(v) for v in value]

    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]

    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(mode="json")
        except Exception:
            return value.model_dump()

    return value


# ===== ACTIVE DO OPERATIONS =====

@track(name="storage_save_active_do")
def save_active_do(active_do: Dict[str, Any]) -> None:
    """Save active do state."""
    # Don't save if no task selected
    if not active_do.get("task"):
        logger.warning(f"⚠️ active_do not saved: no selected task for user {active_do.get('user_id')}")
        return
    
    try:
        supabase = _get_agent_supabase()
        started_at = active_do.get("started_at")
        if hasattr(started_at, 'isoformat'):
            started_at = started_at.isoformat()

        supabase.table("active_do").upsert(
            {
                "user_id": active_do["user_id"],
                "task": active_do.get("task"),
                "selection_reason": active_do.get("selection_reason"),
                "coaching_message": active_do.get("coaching_message"),
                "started_at": started_at,
                "updated_at": datetime.utcnow().isoformat(),
            },
            on_conflict="user_id",
        ).execute()
        logger.info(f"💾 Saved active do for user {active_do['user_id']}")
    except Exception as e:
        # Non-blocking - log and continue
        logger.warning(f"⚠️ Failed to save active do (non-blocking): {str(e)}")


@track(name="storage_get_active_do")
def get_active_do(user_id: str) -> Optional[Dict[str, Any]]:
    """Get active do for user."""
    try:
        supabase = _get_agent_supabase()
        result = supabase.table("active_do").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        # Non-blocking - log and return None
        logger.warning(f"⚠️ Failed to get active do (non-blocking): {str(e)}")
        return None


# ===== SESSION STATE OPERATIONS =====

@track(name="storage_save_session_state")
def save_session_state(user_id: str, state: Dict[str, Any]) -> None:
    """Save session state."""
    try:
        supabase = _get_agent_supabase()
        supabase.table("session_state").upsert({
            "user_id": user_id,
            "state_data": state,
            "updated_at": datetime.utcnow().isoformat(),
        }).execute()
        logger.info(f"💾 Saved session state for user {user_id}")
    except Exception as e:
        # Non-blocking - log and continue
        logger.warning(f"⚠️ Failed to save session state (non-blocking): {str(e)}")


@track(name="storage_get_session_state")
def get_session_state(user_id: str) -> Optional[Dict[str, Any]]:
    """Get session state for user."""
    try:
        supabase = _get_agent_supabase()
        result = supabase.table("session_state").select("*").eq("user_id", user_id).execute()
        if result.data:
            return result.data[0].get("state_data")
        return None
    except Exception as e:
        # Non-blocking - log and return None
        logger.warning(f"⚠️ Failed to get session state (non-blocking): {str(e)}")
        return None


# ===== STUCK EPISODES OPERATIONS =====

@track(name="storage_save_stuck_episode")
def save_stuck_episode(episode: Dict[str, Any]) -> None:
    """Save stuck episode."""
    try:
        supabase = get_supabase()
        supabase.table("stuck_episodes").insert({
            "user_id": episode["user_id"],
            "task_id": episode["task_id"],
            "session_id": episode["session_id"],
            "stuck_reason": episode["stuck_reason"],
            "time_stuck": episode["time_stuck"],
            "detected_at": episode["detected_at"].isoformat(),
        }).execute()
        logger.info(f"💾 Saved stuck episode for user {episode['user_id']}")
    except Exception as e:
        logger.error(f"❌ Failed to save stuck episode: {str(e)}")
        raise


@track(name="storage_get_recent_stuck_episodes")
def get_recent_stuck_episodes(user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent stuck episodes."""
    try:
        supabase = get_supabase()
        since = datetime.utcnow() - timedelta(hours=hours)
        result = supabase.table("stuck_episodes").select("*").eq("user_id", user_id).gte("detected_at", since.isoformat()).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get stuck episodes: {str(e)}")
        return []


# ===== TIME MODELS OPERATIONS =====

@track(name="storage_save_time_patterns")
def save_time_patterns(user_id: str, patterns: Dict[str, Any]) -> None:
    """Save learned time patterns."""
    try:
        supabase = get_supabase()
        supabase.table("time_models").upsert({
            "user_id": user_id,
            "patterns": patterns,
            "updated_at": datetime.utcnow().isoformat(),
        }).execute()
        logger.info(f"💾 Saved time patterns for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to save time patterns: {str(e)}")
        raise


@track(name="storage_get_time_patterns")
def get_time_patterns(user_id: str) -> Optional[Dict[str, Any]]:
    """Get learned time patterns."""
    try:
        supabase = get_supabase()
        result = supabase.table("time_models").select("*").eq("user_id", user_id).execute()
        if result.data:
            return result.data[0]["patterns"]
        return None
    except Exception as e:
        logger.error(f"❌ Failed to get time patterns: {str(e)}")
        return None


# ===== INSIGHTS OPERATIONS =====

@track(name="storage_save_session_insights")
def save_session_insights(insights: Dict[str, Any]) -> None:
    """Save session insights."""
    try:
        supabase = get_supabase()
        supabase.table("insights").insert({
            "user_id": insights["user_id"],
            "date": insights["date"].isoformat(),
            "insights": insights["insights"],
            "motivation": insights["motivation"],
            "generated_at": datetime.utcnow().isoformat(),
        }).execute()
        logger.info(f"💾 Saved insights for user {insights['user_id']}")
    except Exception as e:
        logger.error(f"❌ Failed to save insights: {str(e)}")
        raise


@track(name="storage_get_recent_insights")
def get_recent_insights(user_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """Get recent insights."""
    try:
        supabase = get_supabase()
        since = datetime.utcnow() - timedelta(days=days)
        result = supabase.table("insights").select("*").eq("user_id", user_id).gte("date", since.isoformat()).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get insights: {str(e)}")
        return []


# ===== GAMIFICATION OPERATIONS =====

@track(name="storage_save_gamification_state")
def save_gamification_state(user_id: str, state: Dict[str, Any]) -> None:
    """Save gamification state."""
    try:
        supabase = get_supabase()
        supabase.table("gamification_state").upsert({
            "user_id": user_id,
            "total_xp": state["total_xp"],
            "level": state["level"],
            "current_streak": state["current_streak"],
            "longest_streak": state["longest_streak"],
            "last_activity_date": state["last_activity_date"].isoformat() if state["last_activity_date"] else None,
            "updated_at": datetime.utcnow().isoformat(),
        }).execute()
        logger.info(f"💾 Saved gamification state for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to save gamification state: {str(e)}")
        raise


@track(name="storage_get_gamification_state")
def get_gamification_state(user_id: str) -> Optional[Dict[str, Any]]:
    """Get gamification state."""
    try:
        supabase = get_supabase()
        result = supabase.table("gamification_state").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"❌ Failed to get gamification state: {str(e)}")
        return None


# ===== XP LEDGER OPERATIONS =====

@track(name="storage_save_xp_ledger_entry")
def save_xp_ledger_entry(entry: Dict[str, Any]) -> None:
    """Save XP ledger entry."""
    try:
        supabase = get_supabase()
        supabase.table("xp_ledger").insert({
            "user_id": entry["user_id"],
            "action": entry["action"],
            "xp_gained": entry["xp_gained"],
            "total_xp_after": entry["total_xp_after"],
            "metadata": entry["metadata"],
            "timestamp": entry["timestamp"].isoformat(),
        }).execute()
        logger.info(f"💾 Saved XP ledger entry for user {entry['user_id']}")
    except Exception as e:
        logger.error(f"❌ Failed to save XP ledger: {str(e)}")
        raise


@track(name="storage_get_xp_history")
def get_xp_history(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get XP transaction history."""
    try:
        supabase = get_supabase()
        since = datetime.utcnow() - timedelta(days=days)
        result = supabase.table("xp_ledger").select("*").eq("user_id", user_id).gte("timestamp", since.isoformat()).order("timestamp", desc=True).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get XP history: {str(e)}")
        return []


# ===== AGENT EVENTS OPERATIONS =====

@track(name="storage_log_agent_event")
def log_agent_event(user_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
    """Log agent event."""
    try:
        supabase = _get_agent_supabase()
        supabase.table("agent_events").insert({
            "user_id": user_id,
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
        }).execute()
        logger.info(f"📝 Logged agent event: {event_type} for user {user_id}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to log agent event (non-blocking): {str(e)}")


@track(name="storage_get_agent_events")
def get_agent_events(user_id: str, event_type: str = None, hours: int = 24) -> List[Dict[str, Any]]:
    """Get agent events."""
    try:
        supabase = _get_agent_supabase()
        query = supabase.table("agent_events").select("*").eq("user_id", user_id)

        if event_type:
            query = query.eq("event_type", event_type)

        since = datetime.utcnow() - timedelta(hours=hours)
        result = query.gte("timestamp", since.isoformat()).order("timestamp", desc=True).execute()
        return result.data
    except Exception as e:
        logger.warning(f"⚠️ Failed to get agent events (non-blocking): {str(e)}")
        return []


# ===== EXISTING OPERATIONS (from original MVP) =====

@track(name="storage_get_user_sessions")
def get_user_sessions(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get user work sessions."""
    try:
        supabase = _get_agent_supabase()
        since = datetime.utcnow() - timedelta(days=days)
        result = supabase.table("work_sessions").select("*").eq("user_id", user_id).gte("created_at", since.isoformat()).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get user sessions: {str(e)}")
        return []


@track(name="storage_get_user_tasks")
def get_user_tasks(user_id: str, completed_only: bool = False, days: int = 30) -> List[Dict[str, Any]]:
    """Get user tasks."""
    try:
        supabase = _get_agent_supabase()
        query = supabase.table("tasks").select("*").eq("user_id", user_id)

        if completed_only:
            query = query.not_.is_("completed_at", "null")

        since = datetime.utcnow() - timedelta(days=days)
        result = query.gte("created_at", since.isoformat()).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get user tasks: {str(e)}")
        return []


@track(name="storage_get_user_checkins")
def get_user_checkins(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get user daily check-ins."""
    try:
        supabase = _get_agent_supabase()
        since = datetime.utcnow() - timedelta(days=days)
        result = supabase.table("daily_check_ins").select("*").eq("user_id", user_id).gte("created_at", since.isoformat()).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get user checkins: {str(e)}")
        return []


@track(name="storage_save_ai_learning")
def save_ai_learning(
    user_id: str,
    agent_type: str,
    data: Dict[str, Any],
    expires_at: datetime = None,
) -> None:
    """Save AI learning data."""
    # Use service-role client when available to avoid RLS write failures for agent jobs.
    supabase = _get_agent_supabase()
    base_payload = {
        "user_id": user_id,
        "agent_type": agent_type,
        "data": _json_safe(data),
    }
    full_payload = {
        **base_payload,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "updated_at": datetime.utcnow().isoformat(),
    }

    try:
        # Newer schema (migration 003): includes expires_at + updated_at.
        supabase.table("ai_learning_data").upsert(full_payload).execute()
        logger.info(f"Saved AI learning data for user {user_id}, agent {agent_type}")
    except Exception as e:
        error_text = str(e)

        # Compatibility fallback for older schema that lacks expires_at/updated_at.
        if (
            "Could not find the 'expires_at' column" in error_text
            or "Could not find the 'updated_at' column" in error_text
        ):
            try:
                supabase.table("ai_learning_data").insert(base_payload).execute()
                logger.warning(
                    "ai_learning_data legacy schema detected (missing expires_at/updated_at). "
                    "Saved learning with base columns only."
                )
                return
            except Exception as fallback_error:
                logger.error(f"Failed to save AI learning (legacy fallback): {fallback_error}")
                raise

        logger.error(f"Failed to save AI learning: {error_text}")
        raise


def _normalize_constraints(constraints: Any) -> Dict[str, Any]:
    """Normalize constraints from dict/Pydantic into a stable dict shape."""
    if constraints is None:
        return {}

    if isinstance(constraints, dict):
        c = dict(constraints)
    elif hasattr(constraints, "model_dump"):
        c = constraints.model_dump()
    else:
        c = {}

    # Backward/forward compatibility for field names.
    c["current_energy"] = c.get("current_energy", c.get("energy_level", 5))
    c["max_minutes"] = c.get("max_minutes", c.get("max_task_duration", 120))
    c["avoid_tags"] = c.get("avoid_tags") or []
    return c


@track(name="storage_get_task_candidates")
def get_task_candidates(user_id: str, constraints: Any) -> List[Dict[str, Any]]:
    """Get task candidates for selection."""
    try:
        supabase = _get_agent_supabase()
        # Get pending tasks (align with dashboard pending-task definition).
        result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["todo", "in_progress", "paused", "blocked"])
            .execute()
        )

        candidates = []
        normalized = _normalize_constraints(constraints)
        total_tasks = len(result.data or [])
        for task in result.data:
            # Apply basic filtering
            if _task_matches_constraints(task, normalized):
                candidates.append(task)

        logger.info(
            f"Task candidate scan for user {user_id}: total={total_tasks}, "
            f"after_filters={len(candidates)}, energy={normalized.get('current_energy')}, "
            f"max_minutes={normalized.get('max_minutes')}, avoid_tags={len(normalized.get('avoid_tags', []))}"
        )
        return candidates[:20]  # Limit candidates
    except Exception as e:
        logger.error(f"❌ Failed to get task candidates: {str(e)}")
        return []


def _task_matches_constraints(task: Dict[str, Any], constraints: Dict[str, Any]) -> bool:
    """Check if task matches selection constraints."""
    # Energy level check
    energy_req = _estimate_task_energy(task)
    if energy_req > constraints.get("current_energy", 5):
        return False

    # Time check
    duration_raw = task.get("estimated_duration", 60)
    try:
        duration = int(duration_raw) if duration_raw is not None else 60
    except (TypeError, ValueError):
        duration = 60
    if duration > constraints.get("max_minutes", 120):
        return False

    # Avoid-tags check
    task_tags = set((task.get("tags", []) or []))
    avoid_tags = set(constraints.get("avoid_tags", []) or [])
    if avoid_tags and task_tags and task_tags & avoid_tags:
        return False

    return True


def _estimate_task_energy(task: Dict[str, Any]) -> int:
    """Estimate energy requirement for task."""
    priority = task.get("priority", "medium")
    energy_map = {"low": 1, "medium": 3, "high": 4, "urgent": 5}
    return energy_map.get(priority, 3)


# Additional helper functions for new tables
@track(name="storage_get_project_data")
def get_project_data(project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get project data."""
    try:
        supabase = get_supabase()
        result = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"❌ Failed to get project data: {str(e)}")
        return None


@track(name="storage_get_project_tasks")
def get_project_tasks(project_id: str) -> List[Dict[str, Any]]:
    """Get tasks for project."""
    try:
        supabase = get_supabase()
        result = supabase.table("tasks").select("*").eq("project_id", project_id).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get project tasks: {str(e)}")
        return []


@track(name="storage_get_project_sessions")
def get_project_sessions(project_id: str) -> List[Dict[str, Any]]:
    """Get work sessions for project."""
    try:
        supabase = get_supabase()
        result = supabase.table("work_sessions").select("*").eq("project_id", project_id).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get project sessions: {str(e)}")
        return []


@track(name="storage_get_project_checkins")
def get_project_checkins(project_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get check-ins related to project tasks."""
    # This is a simplified implementation - in practice might need more complex logic
    try:
        supabase = get_supabase()
        since = datetime.utcnow() - timedelta(days=days)
        result = supabase.table("daily_check_ins").select("*").gte("created_at", since.isoformat()).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get project checkins: {str(e)}")
        return []


@track(name="storage_get_user_profile")
def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile from ai_learning_data."""
    try:
        supabase = get_supabase()
        result = supabase.table("ai_learning_data").select("*").eq("user_id", user_id).eq("agent_type", "user_profile").execute()
        if result.data:
            return result.data[0]["data"]
        return None
    except Exception as e:
        logger.error(f"❌ Failed to get user profile: {str(e)}")
        return None


@track(name="storage_get_task_dependencies")
def get_task_dependencies(task_id: str) -> Dict[str, List[str]]:
    """Get task dependencies (simplified - assumes dependency table exists)."""
    # This is a placeholder - actual implementation depends on schema
    return {"blocks": [], "blocked_by": []}


@track(name="storage_update_session_status")
def update_session_status(task_id: str, status: str) -> None:
    """Update work session status."""
    try:
        supabase = _get_agent_supabase()
        now_iso = datetime.utcnow().isoformat()
        update_data = {}
        if status == "started":
            update_data["start_time"] = now_iso
        elif status == "completed":
            update_data["end_time"] = now_iso

        if not update_data:
            logger.info(f"ℹ️ No work session fields to update for task {task_id}: {status}")
            return

        supabase.table("work_sessions").update(update_data).eq("task_id", task_id).execute()
        logger.info(f"✅ Updated session timing for task {task_id}: {status}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to update session status (non-blocking): {str(e)}")


@track(name="storage_get_recent_sessions")
def get_recent_sessions(user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent work sessions."""
    try:
        supabase = get_supabase()
        since = datetime.utcnow() - timedelta(hours=hours)
        result = supabase.table("work_sessions").select("*").eq("user_id", user_id).gte("created_at", since.isoformat()).execute()
        return result.data
    except Exception as e:
        logger.error(f"❌ Failed to get recent sessions: {str(e)}")
        return []


@track(name="storage_get_session_patterns")
def get_session_patterns(user_id: str, days: int = 7) -> Dict[str, Any]:
    """Get session patterns for stuck detection.

    Returns a dict with stable keys for downstream consumption.
    """
    fallback = {"recent_sessions": []}
    try:
        supabase = get_supabase()
        since = datetime.utcnow() - timedelta(days=days)
        result = supabase.table("work_sessions").select("*").eq("user_id", user_id).gte("created_at", since.isoformat()).execute()
        return {"recent_sessions": result.data or []}
    except Exception as e:
        logger.error(f"❌ Failed to get session patterns: {str(e)}")
        return fallback
