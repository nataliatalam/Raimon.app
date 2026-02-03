"""
Events - Structured event logging for agents.

Functionality: Log and track agent events for debugging, analytics, and learning.

Event types:
- agent_start: Agent execution started
- agent_success: Agent completed successfully
- agent_error: Agent failed with error
- user_action: User performed action
- system_event: System-level events

All events include user_id, timestamp, and structured data.
"""

from typing import Dict, Any, List
from datetime import datetime
from agent_mvp.storage import log_agent_event
from core.supabase import get_supabase
from agent_mvp.contracts import AppOpenEvent, CheckInSubmittedEvent
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="events_log_agent_start")
def log_agent_start(agent_name: str, user_id: str, input_data: Dict[str, Any]) -> None:
    """Log agent execution start."""
    event_data = {
        "agent": agent_name,
        "input": input_data,
        "phase": "start",
    }
    log_agent_event(user_id, "agent_start", event_data)
    logger.info(f"🚀 Agent {agent_name} started for user {user_id}")


@track(name="events_log_agent_success")
def log_agent_success(agent_name: str, user_id: str, output_data: Dict[str, Any], duration_ms: int = None) -> None:
    """Log agent execution success."""
    event_data = {
        "agent": agent_name,
        "output": output_data,
        "phase": "success",
        "duration_ms": duration_ms,
    }
    log_agent_event(user_id, "agent_success", event_data)
    logger.info(f"✅ Agent {agent_name} succeeded for user {user_id}")


@track(name="events_log_agent_error")
def log_agent_error(agent_name: str, user_id: str, error: str, input_data: Dict[str, Any] = None) -> None:
    """Log agent execution error."""
    event_data = {
        "agent": agent_name,
        "error": error,
        "input": input_data,
        "phase": "error",
    }
    log_agent_event(user_id, "agent_error", event_data)
    logger.error(f"❌ Agent {agent_name} failed for user {user_id}: {error}")


@track(name="events_log_user_action")
def log_user_action(user_id: str, action: str, metadata: Dict[str, Any] = None) -> None:
    """Log user action."""
    event_data = {
        "action": action,
        "metadata": metadata or {},
    }
    log_agent_event(user_id, "user_action", event_data)
    logger.info(f"👤 User {user_id} performed action: {action}")


@track(name="events_log_system_event")
def log_system_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log system-level event (no user context)."""
    # System events don't have user_id, so we use a special user_id
    system_user_id = "system"
    event_data = {
        "event_type": event_type,
        "details": details,
    }
    log_agent_event(system_user_id, "system_event", event_data)
    logger.info(f"🔧 System event: {event_type}")


@track(name="events_log_workflow_start")
def log_workflow_start(workflow_name: str, user_id: str, trigger_event: str) -> None:
    """Log workflow execution start."""
    event_data = {
        "workflow": workflow_name,
        "trigger": trigger_event,
        "phase": "start",
    }
    log_agent_event(user_id, "workflow_start", event_data)
    logger.info(f"🔄 Workflow {workflow_name} started for user {user_id}")


@track(name="events_log_workflow_complete")
def log_workflow_complete(workflow_name: str, user_id: str, success: bool, duration_ms: int = None) -> None:
    """Log workflow execution completion."""
    event_data = {
        "workflow": workflow_name,
        "success": success,
        "phase": "complete",
        "duration_ms": duration_ms,
    }
    log_agent_event(user_id, "workflow_complete", event_data)
    status = "✅" if success else "❌"
    logger.info(f"{status} Workflow {workflow_name} completed for user {user_id}")


@track(name="events_log_task_selection")
def log_task_selection(
    user_id: str,
    selected_task_id: str,
    selection_reason: str,
    candidate_count: int,
    priority_score: float,
) -> None:
    """Log task selection event."""
    event_data = {
        "selected_task_id": selected_task_id,
        "selection_reason": selection_reason,
        "candidate_count": candidate_count,
        "priority_score": priority_score,
    }
    log_agent_event(user_id, "task_selection", event_data)
    logger.info(f"🎯 Task selected for user {user_id}: {selected_task_id}")


@track(name="events_log_stuck_detected")
def log_stuck_detected(
    user_id: str,
    task_id: str,
    stuck_reason: str,
    time_stuck: int,
    microtasks_count: int,
) -> None:
    """Log stuck detection event."""
    event_data = {
        "task_id": task_id,
        "stuck_reason": stuck_reason,
        "time_stuck": time_stuck,
        "microtasks_provided": microtasks_count,
    }
    log_agent_event(user_id, "stuck_detected", event_data)
    logger.info(f"🕳️ Stuck detected for user {user_id} on task {task_id}")


@track(name="events_log_gamification_update")
def log_gamification_update(
    user_id: str,
    action: str,
    xp_gained: int,
    new_level: int,
    streak_change: int,
) -> None:
    """Log gamification update event."""
    event_data = {
        "action": action,
        "xp_gained": xp_gained,
        "new_level": new_level,
        "streak_change": streak_change,
    }
    log_agent_event(user_id, "gamification_update", event_data)
    logger.info(f"🎮 Gamification updated for user {user_id}: +{xp_gained} XP")


@track(name="events_log_insight_generated")
def log_insight_generated(
    user_id: str,
    insight_type: str,
    insight_count: int,
    project_id: str = None,
) -> None:
    """Log insight generation event."""
    event_data = {
        "insight_type": insight_type,
        "insight_count": insight_count,
        "project_id": project_id,
    }
    log_agent_event(user_id, "insight_generated", event_data)
    logger.info(f"💡 Insights generated for user {user_id}: {insight_count} {insight_type}")


@track(name="events_log_motivation_sent")
def log_motivation_sent(
    user_id: str,
    category: str,
    context: str,
    message_length: int,
) -> None:
    """Log motivation message sent."""
    event_data = {
        "category": category,
        "context": context,
        "message_length": message_length,
    }
    log_agent_event(user_id, "motivation_sent", event_data)
    logger.info(f"💪 Motivation sent to user {user_id}: {category}")


def create_event_wrapper(agent_name: str):
    """Create a decorator for automatic event logging."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract user_id from arguments
            user_id = None
            if args and len(args) > 0:
                # Assume first arg after self is user_id
                if hasattr(args[0], '__self__'):  # method
                    user_id = args[1] if len(args) > 1 else None
                else:  # function
                    user_id = args[0]

            if user_id:
                log_agent_start(agent_name, user_id, {"args": len(args), "kwargs": list(kwargs.keys())})

            start_time = datetime.utcnow()

            try:
                result = func(*args, **kwargs)

                if user_id:
                    duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    log_agent_success(agent_name, user_id, {"result_type": type(result).__name__}, duration)

                return result

            except Exception as e:
                if user_id:
                    log_agent_error(agent_name, user_id, str(e), {"args": len(args), "kwargs": list(kwargs.keys())})
                raise

        return wrapper
    return decorator


# Export class wrapper for test compatibility
class EventLogger:
    """Wrapper class for events module for backward compatibility with tests."""

    def _create_event_data(self, event: Any) -> Dict[str, Any]:
        """Create structured event data from event model."""
        base = {
            "timestamp": getattr(event, "timestamp", datetime.utcnow().isoformat()),
            "metadata": {"version": "1.0"},
        }

        if isinstance(event, AppOpenEvent):
            base.update({
                "event_type": "APP_OPEN",
                "user_id": event.user_id,
            })
        elif isinstance(event, CheckInSubmittedEvent):
            base.update({
                "event_type": "CHECKIN_SUBMITTED",
                "user_id": event.user_id,
                "energy_level": event.energy_level,
                "focus_areas": event.focus_areas,
                "time_available": event.time_available,
            })
        else:
            base.update({
                "event_type": getattr(event, "event_type", "UNKNOWN"),
                "user_id": getattr(event, "user_id", None),
            })

        return base

    async def log_event(self, event: Any) -> bool:
        """Log a single event to storage."""
        try:
            supabase = get_supabase()
            event_data = self._create_event_data(event)
            insert_payload = {
                "event_type": event_data.get("event_type"),
                "user_id": event_data.get("user_id"),
                "event_data": event_data,
                "timestamp": event_data.get("timestamp"),
                "metadata": event_data.get("metadata", {}),
            }
            supabase.table("agent_events").insert(insert_payload).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to log event: {str(e)}")
            return False

    async def log_events(self, events: List[Any]) -> List[bool]:
        """Log multiple events and return success flags."""
        results = []
        for event in events:
            results.append(await self.log_event(event))
        return results

    async def get_user_events(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent events for a user."""
        try:
            supabase = get_supabase()
            result = (
                supabase.table("agent_events")
                .select("*")
                .eq("user_id", user_id)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"❌ Failed to get user events: {str(e)}")
            return []

    async def get_events_by_type(self, user_id: str, event_type: str) -> List[Dict[str, Any]]:
        """Fetch events by type for a user."""
        try:
            supabase = get_supabase()
            result = (
                supabase.table("agent_events")
                .select("*")
                .eq("user_id", user_id)
                .eq("event_type", event_type)
                .order("timestamp", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"❌ Failed to get events by type: {str(e)}")
            return []

    async def get_system_events(self) -> List[Dict[str, Any]]:
        """Fetch system events with no user_id."""
        try:
            supabase = get_supabase()
            result = (
                supabase.table("agent_events")
                .select("*")
                .is_("user_id", "null")
                .order("timestamp", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"❌ Failed to get system events: {str(e)}")
            return []
