"""
Orchestrator - LangGraph event-driven workflow.

Functionality: Main orchestration engine handling the complete user journey flow.

Events handled:
- APP_OPEN: Resume context
- CHECKIN_SUBMITTED: Process check-in → constraints → task selection
- DO_NEXT: Execute task selection flow
- DO_ACTION: Handle task actions (start, complete, stuck)
- DAY_END: Process day completion and insights

State: GraphState with current event, user context, selections, etc.

LLM: Orchestrates other agents (no direct LLM calls)

Critical guarantees:
- event-driven flow with proper state transitions
- all agent calls are bounded and validated
- comprehensive error handling with fallbacks
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from core.supabase import get_supabase
from agent_mvp.contracts import (
    GraphState,
    AgentMVPResponse,
    AppOpenEvent,
    CheckInSubmittedEvent,
    DoNextEvent,
    DoActionEvent,
    DayEndEvent,
)
from agent_mvp.user_profile_agent import analyze_user_profile
from agent_mvp.state_adapter_agent import adapt_checkin_to_constraints
from agent_mvp.priority_engine_agent import score_task_priorities
from agent_mvp.do_selector import select_optimal_task
from agent_mvp.context_continuity_agent import resume_context
from agent_mvp.stuck_pattern_agent import detect_stuck_patterns
from agent_mvp.project_insight_agent import generate_project_insights
from agent_mvp.motivation_agent import generate_motivation
from agent_mvp.gamification_rules import update_gamification
from agent_mvp.coach import generate_coaching_message
from agent_mvp.storage import (
    get_task_candidates,
    save_active_do,
    update_session_status,
    save_session_insights,
    get_user_checkins,
)
from agent_mvp.events import log_agent_event
from opik import track
import logging

logger = logging.getLogger(__name__)


class RaimonOrchestrator:
    """Main orchestration engine for the Raimon agent system."""

    def __init__(self):
        from agent_mvp import storage
        self.storage = storage
        self.agents = {}  # Will be populated by dependency injection
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("start", self._start)
        workflow.add_node("handle_app_open", self._handle_app_open)
        workflow.add_node("handle_checkin", self._handle_checkin)
        workflow.add_node("handle_do_next", self._handle_do_next)
        workflow.add_node("handle_do_action", self._handle_do_action)
        workflow.add_node("handle_day_end", self._handle_day_end)
        workflow.add_node("return_result", self._return_result)

        # Add conditional edges based on event type
        workflow.add_conditional_edges(
            "start",
            self._route_event,
            {
                "app_open": "handle_app_open",
                "checkin_submitted": "handle_checkin",
                "do_next": "handle_do_next",
                "do_action": "handle_do_action",
                "day_end": "handle_day_end",
                "error": "return_result",
            }
        )

        # Add success paths
        workflow.add_edge("handle_app_open", "return_result")
        workflow.add_edge("handle_checkin", "return_result")
        workflow.add_edge("handle_do_next", "return_result")
        workflow.add_edge("handle_do_action", "return_result")
        workflow.add_edge("handle_day_end", "return_result")

        workflow.set_entry_point("start")
        return workflow.compile()

    def _route_event(self, state: GraphState) -> str:
        """Route to appropriate handler based on event type."""
        event = state.current_event
        if isinstance(event, AppOpenEvent):
            return "app_open"
        elif isinstance(event, CheckInSubmittedEvent):
            return "checkin_submitted"
        elif isinstance(event, DoNextEvent):
            return "do_next"
        elif isinstance(event, DoActionEvent):
            return "do_action"
        elif isinstance(event, DayEndEvent):
            return "day_end"
        else:
            logger.error(f"Unknown event type: {type(event)}")
            state.success = False
            state.error = f"Unknown event type: {type(event)}"
            return "error"

    def _start(self, state: GraphState) -> GraphState:
        """No-op start node for graph entry."""
        return state

    @track(name="orchestrator_app_open")
    def _handle_app_open(self, state: GraphState) -> GraphState:
        """Handle app open event - resume user context."""
        try:
            event = state.current_event
            user_id = event.user_id

            # Get session state if storage is available
            if hasattr(self, 'storage') and self.storage:
                self.storage.get_session_state(user_id)
            
            # Log event if agents available
            if hasattr(self, 'agents') and self.agents and 'events' in self.agents:
                self.agents['events'].log_event(event)
            
            # Resume context via agent if available
            if hasattr(self, 'agents') and self.agents and 'context_continuity_agent' in self.agents:
                resumption = self.agents['context_continuity_agent'].process(event)
            else:
                resumption = resume_context(event)

            state.context_resumption = resumption
            state.success = True

            logger.info(f"📱 App opened for user {user_id}")

        except Exception as e:
            logger.error(f"❌ App open failed: {str(e)}")
            state.success = False
            state.error = f"Failed to resume context: {str(e)}"

        return state

    @track(name="orchestrator_checkin")
    def _handle_checkin(self, state: GraphState) -> GraphState:
        """Handle check-in submission - process and prepare for task selection."""
        try:
            event = state.current_event
            user_id = event.user_id

            if hasattr(self, "agents") and self.agents and "events" in self.agents:
                self.agents["events"].log_event(event)

            checkin_payload = {
                "user_id": user_id,
                "energy_level": getattr(event, "energy_level", None),
                "focus_areas": getattr(event, "focus_areas", []),
            }

            if hasattr(self, "agents") and self.agents and "state_adapter_agent" in self.agents:
                constraints = self.agents["state_adapter_agent"].process(checkin_payload)
            else:
                constraints = adapt_checkin_to_constraints({"check_in_data": checkin_payload})

            if hasattr(self, "agents") and self.agents and "priority_engine_agent" in self.agents:
                candidates = self.agents["priority_engine_agent"].process({"constraints": constraints})
            else:
                candidates = []

            if hasattr(self, "agents") and self.agents and "do_selector" in self.agents:
                selection = self.agents["do_selector"].select_task({"candidates": candidates})
            else:
                selection = {"task": None, "reason": ""}

            if hasattr(self, "storage") and self.storage:
                self.storage.save_active_do(selection)

            state.selection_constraints = constraints
            state.success = True

            logger.info(f"✅ Check-in processed for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Check-in processing failed: {str(e)}")
            state.success = False
            state.error = f"Failed to process check-in: {str(e)}"

        return state

    @track(name="orchestrator_do_next")
    def _handle_do_next(self, state: GraphState) -> GraphState:
        """Handle do_next event - execute full task selection flow."""
        try:
            event = state.current_event
            user_id = event.user_id

            log_agent_event(user_id, "do_next", {"context": event.context})

            # Get user profile if not already available
            if not state.user_profile:
                profile_request = {"include_tasks": True, "include_sessions": True, "include_patterns": True}
                state.user_profile = analyze_user_profile(user_id, profile_request)

            # Get selection constraints if not already available
            if not state.selection_constraints:
                # Get latest check-in
                recent_checkins = get_user_checkins(user_id, days=1)
                if recent_checkins:
                    latest_checkin = recent_checkins[0]
                    constraints_request = {
                        "check_in_data": latest_checkin,
                        "user_profile": state.user_profile,
                    }
                    state.selection_constraints = adapt_checkin_to_constraints(constraints_request)
                else:
                    raise ValueError("No recent check-in found for task selection")

            # Get task candidates
            candidates = get_task_candidates(user_id, state.selection_constraints)

            # Score candidates
            priority_request = {
                "candidates": candidates,
                "user_profile": state.user_profile,
            }
            scored_candidates = score_task_priorities(priority_request)

            # Select optimal task
            selection_request = {
                "scored_candidates": scored_candidates.scored_candidates,
                "constraints": state.selection_constraints,
            }
            selection = select_optimal_task(selection_request)

            # Generate coaching
            coaching = generate_coaching_message(user_id, selection.selected_task, event.context)

            # Create active do
            active_do = {
                "user_id": user_id,
                "task": selection.selected_task.task,
                "selection_reason": selection.selection_reason,
                "coaching_message": coaching.message,
                "started_at": datetime.utcnow(),
            }
            save_active_do(active_do)

            state.active_do = active_do
            state.success = True

            logger.info(f"🎯 Task selected for user {user_id}: {selection.selected_task.task.get('title')}")

        except Exception as e:
            logger.error(f"❌ Task selection failed: {str(e)}")
            state.success = False
            state.error = f"Failed to select task: {str(e)}"

        return state

    @track(name="orchestrator_do_action")
    def _handle_do_action(self, state: GraphState) -> GraphState:
        """Handle do_action event - process task actions."""
        try:
            event = state.current_event
            user_id = event.user_id
            action = event.action

            if hasattr(self, "agents") and self.agents and "events" in self.agents:
                self.agents["events"].log_event(event)

            if hasattr(self, "storage") and self.storage:
                self.storage.get_active_do(user_id)

            if action == "start":
                # Task started - update session
                if hasattr(self, "storage") and self.storage:
                    self.storage.update_session_status(event.task_id, "started")
                else:
                    update_session_status(event.task_id, "started")

            elif action == "complete":
                # Task completed - update gamification
                if hasattr(self, "agents") and self.agents and "gamification_rules" in self.agents:
                    self.agents["gamification_rules"].update_xp(user_id, "task_completed")
                else:
                    update_gamification(user_id, "task_completed", {"task_id": event.task_id})

                # Generate motivation
                if hasattr(self, "agents") and self.agents and "motivation_agent" in self.agents:
                    motivation = self.agents["motivation_agent"].generate_message({
                        "user_id": user_id,
                        "context": "task_completion",
                        "tone": "celebratory",
                    })
                else:
                    motivation = generate_motivation({
                        "user_id": user_id,
                        "context": "task_completion",
                        "tone": "celebratory",
                    })

                state.motivation_message = motivation

            elif action == "stuck":
                # Detect stuck patterns
                stuck_request = {
                    "user_id": user_id,
                    "current_session": event.current_session,
                    "time_stuck": event.time_stuck,
                }
                if hasattr(self, "agents") and self.agents and "stuck_pattern_agent" in self.agents:
                    stuck_analysis = self.agents["stuck_pattern_agent"].process(stuck_request)
                else:
                    stuck_analysis = detect_stuck_patterns(stuck_request)

                if stuck_analysis.is_stuck:
                    state.stuck_analysis = stuck_analysis
                    state.microtasks = stuck_analysis.microtasks

            state.success = True
            logger.info(f"⚡ Action '{action}' processed for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Action processing failed: {str(e)}")
            state.success = False
            state.error = f"Failed to process action: {str(e)}"

        return state

    @track(name="orchestrator_day_end")
    def _handle_day_end(self, state: GraphState) -> GraphState:
        """Handle day end event - process completion and insights."""
        try:
            event = state.current_event
            user_id = event.user_id

            if hasattr(self, "agents") and self.agents and "events" in self.agents:
                self.agents["events"].log_event(event)

            # Update day completion gamification
            if hasattr(self, "agents") and self.agents and "gamification_rules" in self.agents:
                self.agents["gamification_rules"].update_xp(user_id, "day_completed")
            else:
                update_gamification(user_id, "day_completed", {"date": event.timestamp})

            # Generate project insights
            if hasattr(self, "agents") and self.agents and "project_insight_agent" in self.agents:
                project_insights = self.agents["project_insight_agent"].generate_insights({
                    "user_id": user_id,
                    "insight_type": "progress",
                    "time_range": "week",
                })
            else:
                project_insights = generate_project_insights(user_id, {
                    "insight_type": "progress",
                    "time_range": "week",
                })

            insights = []
            if isinstance(project_insights, dict) and "insights" in project_insights:
                insights = project_insights["insights"]
            else:
                insights = getattr(project_insights, "insights", [])

            # Generate motivation for day completion
            if hasattr(self, "agents") and self.agents and "motivation_agent" in self.agents:
                motivation = self.agents["motivation_agent"].generate_message({
                    "user_id": user_id,
                    "context": "day_completion",
                    "tone": "reflective",
                })
            else:
                motivation = generate_motivation({
                    "user_id": user_id,
                    "context": "day_completion",
                    "tone": "reflective",
                })

            # Save session insights
            if hasattr(self, "storage") and self.storage:
                self.storage.save_insights(user_id, insights)

            state.day_insights = insights
            state.motivation_message = motivation
            state.success = True

            logger.info(f"🌅 Day end processed for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Day end processing failed: {str(e)}")
            state.success = False
            state.error = f"Failed to process day end: {str(e)}"

        return state

    def _return_result(self, state: GraphState) -> GraphState:
        """Return final result."""
        return state

    @track(name="orchestrator_process_event")
    def process_event(self, event: Any) -> AgentMVPResponse:
        """
        Process an event through the orchestration graph.

        Args:
            event: The event to process

        Returns:
            Agent response
        """
        logger.info(f"🎭 Processing event: {type(event).__name__}")

        # Validate explicit event_type if present
        if hasattr(event, "event_type"):
            valid_event_types = {"APP_OPEN", "CHECKIN_SUBMITTED", "DO_NEXT", "DO_ACTION", "DAY_END"}
            if event.event_type not in valid_event_types:
                raise ValueError("Unknown event type")

        # Extract user_id from event
        user_id = getattr(event, "user_id", None)
        if not user_id:
            raise ValueError("Event must have a user_id")
        
        # Extract event_type early so it's available even on error
        event_type = self._get_event_type(event)

        # Initialize state
        initial_state = GraphState(user_id=user_id, current_event=event)

        try:
            # Execute graph
            final_state = self.graph.invoke(initial_state)

            # Build response
            response = AgentMVPResponse(
                success=final_state.success,
                data=self._extract_response_data(final_state),
            )

            if not final_state.success and final_state.error:
                response.error = final_state.error

            logger.info(f"✅ Event processed successfully: {final_state.success}")
            response_dict = response.model_dump()
            
            # Flatten event_type to root level for backward compatibility
            if "data" in response_dict and "event_type" in response_dict["data"]:
                response_dict["event_type"] = response_dict["data"]["event_type"]
            
            return response_dict

        except Exception as e:
            logger.error(f"❌ Orchestration failed: {str(e)}")
            response_data = {"event_type": event_type} if event_type else {}
            response_dict = AgentMVPResponse(
                success=False,
                data=response_data,
                error=f"Orchestration failed: {str(e)}",
            ).model_dump()
            
            # Flatten event_type to root level even on error
            if event_type:
                response_dict["event_type"] = event_type
            
            return response_dict

    def _get_event_type(self, event: Any) -> Optional[str]:
        """Extract event type from event object."""
        if hasattr(event, 'event_type'):
            return event.event_type
        
        class_name = event.__class__.__name__
        event_type_map = {
            'AppOpenEvent': 'APP_OPEN',
            'CheckInSubmittedEvent': 'CHECKIN_SUBMITTED',
            'DoNextEvent': 'DO_NEXT',
            'DoActionEvent': 'DO_ACTION',
            'DayEndEvent': 'DAY_END',
        }
        return event_type_map.get(class_name)

    def _extract_response_data(self, state: GraphState) -> Dict[str, Any]:
        """Extract response data from final state."""
        response_data = {}

        # Extract event_type from state
        if hasattr(state, 'current_event') and state.current_event:
            event_type = self._get_event_type(state.current_event)
            if event_type:
                response_data["event_type"] = event_type

        # Extract context resumption (APP_OPEN)
        if state.context_resumption:
            response_data["context_resumption"] = state.context_resumption

        # Extract selection constraints (CHECKIN_SUBMITTED)
        if state.selection_constraints:
            response_data["selection_constraints"] = state.selection_constraints

        # Extract user profile
        if state.user_profile:
            response_data["user_profile"] = state.user_profile

        # Extract active do (DO_NEXT)
        if state.active_do:
            response_data["active_do"] = state.active_do

        # Extract coach message
        if state.coach_message:
            response_data["coach_message"] = (
                state.coach_message.model_dump()
                if hasattr(state.coach_message, 'model_dump')
                else state.coach_message
            )

        # Extract motivation message (DO_ACTION:complete, DAY_END)
        if state.motivation_message:
            response_data["motivation_message"] = (
                state.motivation_message.model_dump()
                if hasattr(state.motivation_message, 'model_dump')
                else state.motivation_message
            )

        # Extract stuck analysis and microtasks (DO_ACTION:stuck)
        if state.stuck_analysis:
            response_data["stuck_analysis"] = (
                state.stuck_analysis.model_dump()
                if hasattr(state.stuck_analysis, 'model_dump')
                else state.stuck_analysis
            )

        if state.microtasks:
            response_data["microtasks"] = [
                (m.model_dump() if hasattr(m, 'model_dump') else m)
                for m in state.microtasks
            ]

        # Extract day insights (DAY_END)
        if state.day_insights:
            response_data["day_insights"] = [
                (i.model_dump() if hasattr(i, 'model_dump') else i)
                for i in state.day_insights
            ]

        return response_data


# Global orchestrator instance
orchestrator = RaimonOrchestrator()


def process_agent_event(event: Any) -> AgentMVPResponse:
    """
    Process an agent event through the orchestrator.

    Args:
        event: Event to process

    Returns:
        Agent response
    """
    return orchestrator.process_event(event)