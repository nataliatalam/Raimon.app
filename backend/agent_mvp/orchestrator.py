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
    CheckInToConstraintsRequest,
    DoNextEvent,
    DoActionEvent,
    DayEndEvent,
    DailyCheckIn,
    UserProfileAnalysis,
    TaskCandidate,
    SelectionConstraints,
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
from agent_mvp.llm_do_selector import select_task as llm_select_task
from agent_mvp.llm_coach import generate_coaching_message as llm_generate_coaching_message
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

            # Create a DailyCheckIn from the event data
            # The event only has minimal fields, so we construct a DailyCheckIn with what we have
            from datetime import datetime
            daily_checkin = DailyCheckIn(
                date=datetime.utcnow().isoformat().split('T')[0],  # YYYY-MM-DD format
                energy_level=event.energy_level,
                mood=getattr(event, "mood", None),
                sleep_quality=getattr(event, "sleep_quality", None),
                focus_minutes=event.time_available if event.time_available else None,
                context=getattr(event, "context", None),
                priorities=event.focus_areas if event.focus_areas else [],  # Map focus_areas to priorities
                day_of_week=datetime.utcnow().weekday(),
            )
            
            # For now, use minimal user profile (can be enhanced later)
            user_profile = UserProfileAnalysis()

            # Create the constraint request with proper objects
            constraint_request = CheckInToConstraintsRequest(
                user_id=user_id,
                energy_level=event.energy_level,
                focus_areas=event.focus_areas,
                time_available=getattr(event, "time_available", None),
                check_in_data=daily_checkin,
                user_profile=user_profile,
            )

            logger.info(f"📋 Constraint request created: event_type={type(event).__name__} request_type={type(constraint_request).__name__}")

            if hasattr(self, "agents") and self.agents and "state_adapter_agent" in self.agents:
                constraints = self.agents["state_adapter_agent"].process(constraint_request)
            else:
                constraints = adapt_checkin_to_constraints(constraint_request)

            if hasattr(self, "agents") and self.agents and "priority_engine_agent" in self.agents:
                candidates = self.agents["priority_engine_agent"].process({"constraints": constraints})
            else:
                candidates = []

            if hasattr(self, "agents") and self.agents and "do_selector" in self.agents:
                selection = self.agents["do_selector"].select_task({"candidates": candidates})
            else:
                selection = {"task": None, "reason": ""}

            # Ensure selection has all required fields for storage
            if isinstance(selection, dict):
                from datetime import datetime
                selection["user_id"] = user_id
                if "selection_reason" not in selection:
                    selection["selection_reason"] = selection.get("reason", "No specific reason")
                if "coaching_message" not in selection:
                    selection["coaching_message"] = "Get started with your task!"
                if "started_at" not in selection:
                    selection["started_at"] = datetime.utcnow()
            
            # Try to save to storage, but only if there's a selected task and don't fail if storage is unavailable
            if selection.get("task") and hasattr(self, "storage") and self.storage:
                try:
                    self.storage.save_active_do(selection)
                except Exception as storage_error:
                    logger.warning(f"⚠️ Storage save skipped: {str(storage_error)}")
            elif not selection.get("task"):
                logger.warning(f"⚠️ active_do not saved: no selected task for user {user_id}")

            state.constraints = constraints
            state.success = True

            logger.info(f"✅ Check-in processed for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Check-in processing failed: {str(e)}", exc_info=True)
            state.success = False
            state.error = f"Failed to process check-in: {str(e)}"

        return state

    @track(name="orchestrator_do_next")
    def _handle_do_next(self, state: GraphState) -> GraphState:
        """Handle do_next event - execute full task selection flow."""
        try:
            event = state.current_event
            user_id = event.user_id

            try:
                log_agent_event(user_id, "do_next", {"context": getattr(event, "context", None)})
            except Exception as log_err:
                logger.warning(f"⚠️ log_agent_event failed (non-blocking): {log_err}")

            # Get user profile (handle both dict and Pydantic returns)
            user_profile = None
            try:
                # Create proper UserProfileAnalyzeRequest object
                from agent_mvp.contracts import UserProfileAnalyzeRequest
                profile_request = UserProfileAnalyzeRequest(
                    include_tasks=True,
                    include_sessions=True,
                    include_patterns=True,
                )
                profile_result = analyze_user_profile(user_id, profile_request)
                # If result is a dict, convert to UserProfileAnalysis
                if isinstance(profile_result, dict):
                    user_profile = UserProfileAnalysis(**{k: v for k, v in profile_result.items() if k in UserProfileAnalysis.__fields__})
                else:
                    user_profile = profile_result
            except Exception as e:
                logger.warning(f"Could not fetch user profile: {str(e)}")
                user_profile = UserProfileAnalysis()

            # Get selection constraints if not already available
            if not state.selection_constraints:
                # Get latest check-in from daily_check_ins table using service-role client
                latest_checkin = None
                try:
                    from core.supabase import get_supabase_admin
                    from datetime import date
                    supabase = get_supabase_admin()
                    result = supabase.table("daily_check_ins").select("*").eq("user_id", user_id).eq("date", date.today().isoformat()).execute()
                    if result.data:
                        latest_checkin = result.data[0]
                except Exception as e:
                    logger.warning(f"Could not fetch check-in from daily_check_ins: {str(e)}")
                
                if latest_checkin:
                    # Convert dict to CheckInToConstraintsRequest object
                    checkin_obj = DailyCheckIn(
                        date=latest_checkin.get('date', datetime.utcnow().isoformat().split('T')[0]),
                        energy_level=latest_checkin.get('energy_level', 5),
                        mood=latest_checkin.get('mood'),
                        sleep_quality=latest_checkin.get('sleep_quality'),
                        focus_minutes=None,
                        context=None,
                        priorities=latest_checkin.get('focus_areas', []),
                        day_of_week=datetime.utcnow().weekday(),
                    )
                    
                    constraints_request = CheckInToConstraintsRequest(
                        user_id=user_id,
                        energy_level=checkin_obj.energy_level,
                        focus_areas=checkin_obj.priorities if hasattr(checkin_obj, 'priorities') else [],
                        check_in_data=checkin_obj,
                        user_profile=state.user_profile or user_profile or UserProfileAnalysis(),
                    )
                    state.selection_constraints = adapt_checkin_to_constraints(constraints_request)
                    if not state.constraints:
                        state.constraints = state.selection_constraints
                    logger.info(f"📋 Using check-in constraints: energy={checkin_obj.energy_level}")
                else:
                    # No check-in yet - use default balanced constraints
                    logger.info(f"📋 No check-in found, using default constraints")
                    state.selection_constraints = {
                        "max_minutes": 120,
                        "mode": "balanced",
                        "current_energy": 5,  # Default medium energy
                        "avoid_tags": [],
                        "prefer_priority": None,
                    }
                    if not state.constraints:
                        state.constraints = state.selection_constraints
            if not state.constraints:
                try:
                    recent_checkins = get_user_checkins(user_id, days=1)
                    if recent_checkins:
                        latest_checkin = recent_checkins[0]
                        # Ensure user_profile is a proper Pydantic model
                        profile_for_constraints = user_profile if user_profile else UserProfileAnalysis()
                        checkin_obj = (
                            latest_checkin
                            if isinstance(latest_checkin, DailyCheckIn)
                            else DailyCheckIn(
                                date=latest_checkin.get("date", datetime.utcnow().isoformat().split("T")[0]),
                                energy_level=latest_checkin.get("energy_level", 5),
                                mood=latest_checkin.get("mood"),
                                sleep_quality=latest_checkin.get("sleep_quality"),
                                focus_minutes=latest_checkin.get("focus_minutes"),
                                context=latest_checkin.get("context"),
                                priorities=latest_checkin.get("focus_areas", []),
                                day_of_week=datetime.utcnow().weekday(),
                            )
                        )
                        constraints_request = CheckInToConstraintsRequest(
                            user_id=user_id,
                            energy_level=checkin_obj.energy_level,
                            focus_areas=getattr(checkin_obj, "priorities", []),
                            check_in_data=checkin_obj,
                            user_profile=profile_for_constraints,
                        )
                        state.constraints = adapt_checkin_to_constraints(constraints_request)
                except Exception as e:
                    logger.warning(f"Could not fetch recent check-ins: {str(e)}")

            # Get task candidates
            if state.constraints:
                try:
                    candidates = get_task_candidates(user_id, state.constraints)
                    state.candidates = candidates if candidates else []
                    
                    # Select with LLM DoSelector + LLM Coach (with deterministic fallback)
                    if state.candidates:
                        try:
                            llm_candidates = []
                            for task in state.candidates[:20]:
                                llm_candidates.append(
                                    TaskCandidate(
                                        id=str(task.get("id")),
                                        title=task.get("title") or "Untitled task",
                                        priority=task.get("priority", "medium"),
                                        status=task.get("status", "todo"),
                                        estimated_duration=task.get("estimated_duration"),
                                        due_at=task.get("due_at") or task.get("deadline"),
                                        tags=task.get("tags") or [],
                                        created_at=task.get("created_at"),
                                    )
                                )

                            llm_constraints = (
                                state.constraints
                                if isinstance(state.constraints, SelectionConstraints)
                                else SelectionConstraints(**state.constraints)
                            )

                            selector_output, selector_valid = llm_select_task(
                                candidates=llm_candidates,
                                constraints=llm_constraints,
                                recent_actions={"context": getattr(event, "context", None)},
                            )

                            best_task = next(
                                (
                                    t
                                    for t in state.candidates
                                    if str(t.get("id")) == selector_output.task_id
                                ),
                                None,
                            )
                            if not best_task and state.candidates:
                                best_task = state.candidates[0]

                            if best_task:
                                reason_codes = selector_output.reason_codes or ["fallback_best_overall"]
                                selected_candidate = next(
                                    (
                                        c
                                        for c in llm_candidates
                                        if c.id == str(best_task.get("id"))
                                    ),
                                    llm_candidates[0],
                                )
                                coach_output, coach_valid = llm_generate_coaching_message(
                                    task=selected_candidate,
                                    reason_codes=reason_codes,
                                    mode=llm_constraints.mode,
                                )

                                active_do_payload = {
                                    "user_id": user_id,
                                    "task": best_task.get("id"),
                                    "selection_reason": ",".join(reason_codes),
                                    "coaching_message": coach_output.message,
                                    "started_at": datetime.utcnow().isoformat(),
                                }
                                self.storage.save_active_do(active_do_payload) if self.storage else None

                                state.active_do = {
                                    "task": best_task.get("id"),
                                    "selection_reason": ",".join(reason_codes),
                                    "reason_codes": reason_codes,
                                    "alt_task_ids": selector_output.alt_task_ids,
                                    "selector_valid": selector_valid,
                                    "coach_valid": coach_valid,
                                }
                                state.coach_message = coach_output

                                logger.info(
                                    f"Selected task {best_task.get('id')} for user {user_id} "
                                    f"(selector_valid={selector_valid}, coach_valid={coach_valid})"
                                )
                        except Exception as select_err:
                            logger.warning(f"LLM selection failed, using deterministic fallback: {select_err}")
                            try:
                                scored = []
                                for task in state.candidates[:20]:
                                    priority_score = {"high": 3, "medium": 2, "low": 1}.get(task.get("priority", "medium"), 2)
                                    duration_raw = task.get("estimated_duration", 60)
                                    try:
                                        duration = int(duration_raw) if duration_raw is not None else 60
                                    except (TypeError, ValueError):
                                        duration = 60
                                    time_score = 3 if duration < 30 else (2 if duration < 120 else 1)
                                    score = priority_score * 0.6 + time_score * 0.4
                                    scored.append({"task": task, "score": score})

                                scored.sort(key=lambda x: x["score"], reverse=True)
                                if scored:
                                    best_task = scored[0]["task"]
                                    active_do_payload = {
                                        "user_id": user_id,
                                        "task": best_task.get("id"),
                                        "selection_reason": "fallback_optimal_match",
                                        "coaching_message": f"Ready to start {best_task.get('title', 'your task')}?",
                                        "started_at": datetime.utcnow().isoformat(),
                                    }
                                    self.storage.save_active_do(active_do_payload) if self.storage else None
                                    state.active_do = {
                                        "task": best_task.get("id"),
                                        "selection_reason": "fallback_optimal_match",
                                        "reason_codes": ["fallback_best_overall"],
                                        "alt_task_ids": [],
                                        "selector_valid": False,
                                        "coach_valid": False,
                                    }
                                    logger.info(f"Selected task {best_task.get('id')} for user {user_id} (fallback)")
                            except Exception as fallback_err:
                                logger.warning(f"Active_do fallback selection failed (non-blocking): {fallback_err}")
                    else:
                        logger.warning(
                            f"No task candidates available for user {user_id}. "
                            "Check constraints and task pool."
                        )
                except Exception as e:
                    logger.warning(f"Could not fetch task candidates: {str(e)}")

            state.success = True
            logger.info(f"✅ Do next processed for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Do next processing failed: {str(e)}", exc_info=True)
            state.success = False
            state.error = f"Failed to process do_next: {str(e)}"

        return state

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
        logger.info(f"🎭 Processing event: {type(event).__name__} (type={type(event).__name__})")

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
            final_state_result = self.graph.invoke(initial_state)
            
            # LangGraph can return either a dict or the actual state object
            # Convert dict to GraphState if needed
            if isinstance(final_state_result, dict):
                final_state = GraphState(**final_state_result)
            else:
                final_state = final_state_result

            # Build response
            response = AgentMVPResponse(
                success=final_state.success,
                data=self._extract_response_data(final_state),
            )

            if not final_state.success and final_state.error:
                response.error = final_state.error

            logger.info(f"✅ Event processed successfully: success={final_state.success} response_type={type(response).__name__}")
            response_dict = response.model_dump()
            
            # Flatten event_type to root level for backward compatibility
            if "data" in response_dict and "event_type" in response_dict["data"]:
                response_dict["event_type"] = response_dict["data"]["event_type"]
            
            logger.debug(f"📊 Response dict keys: {list(response_dict.keys())}")
            return response_dict

        except Exception as e:
            logger.error(f"❌ Orchestration failed: {str(e)}", exc_info=True)
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
