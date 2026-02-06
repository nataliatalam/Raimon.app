"""
Orchestrator edge routing and conditional logic for LangGraph.

Extracted from orchestrator.py - contains the edge definitions and conditional routing
that determines the workflow path based on event type.
"""

from typing import Any, Optional
from orchestrator.contracts import GraphState
from models.contracts import (
    AppOpenEvent,
    CheckInSubmittedEvent,
    DoNextEvent,
    DoActionEvent,
    DayEndEvent,
)
import logging

logger = logging.getLogger(__name__)


def route_event(state: GraphState) -> str:
    """
    Route to appropriate handler based on event type.

    This is the conditional edge function used in the LangGraph workflow.
    It determines which node to execute next based on the event type in the state.

    Args:
        state: Current GraphState containing the current_event

    Returns:
        String identifier for the next node:
        - "app_open" for AppOpenEvent
        - "checkin_submitted" for CheckInSubmittedEvent
        - "do_next" for DoNextEvent
        - "do_action" for DoActionEvent
        - "day_end" for DayEndEvent
        - "error" for unknown event types
    """
    event = state.current_event

    if isinstance(event, AppOpenEvent):
        logger.debug(f"Routing to app_open handler for user {event.user_id}")
        return "app_open"
    elif isinstance(event, CheckInSubmittedEvent):
        logger.debug(f"Routing to checkin_submitted handler for user {event.user_id}")
        return "checkin_submitted"
    elif isinstance(event, DoNextEvent):
        logger.debug(f"Routing to do_next handler for user {event.user_id}")
        return "do_next"
    elif isinstance(event, DoActionEvent):
        logger.debug(f"Routing to do_action handler for user {event.user_id}")
        return "do_action"
    elif isinstance(event, DayEndEvent):
        logger.debug(f"Routing to day_end handler for user {event.user_id}")
        return "day_end"
    else:
        logger.error(f"Unknown event type: {type(event)}")
        state.success = False
        state.error = f"Unknown event type: {type(event)}"
        return "error"


def get_edge_mappings() -> dict:
    """
    Get the complete edge mapping for the LangGraph workflow.

    Returns:
        Dictionary mapping from conditional edge results to target nodes.
        Structure:
        {
            "app_open": "handle_app_open",
            "checkin_submitted": "handle_checkin",
            "do_next": "handle_do_next",
            "do_action": "handle_do_action",
            "day_end": "handle_day_end",
            "error": "return_result",
        }
    """
    return {
        "app_open": "handle_app_open",
        "checkin_submitted": "handle_checkin",
        "do_next": "handle_do_next",
        "do_action": "handle_do_action",
        "day_end": "handle_day_end",
        "error": "return_result",
    }


def get_success_path_edges() -> list:
    """
    Get the success path edges for the LangGraph workflow.

    All handler nodes have a success path to return_result node.

    Returns:
        List of tuples representing edges:
        [
            ("handle_app_open", "return_result"),
            ("handle_checkin", "return_result"),
            ("handle_do_next", "return_result"),
            ("handle_do_action", "return_result"),
            ("handle_day_end", "return_result"),
        ]
    """
    return [
        ("handle_app_open", "return_result"),
        ("handle_checkin", "return_result"),
        ("handle_do_next", "return_result"),
        ("handle_do_action", "return_result"),
        ("handle_day_end", "return_result"),
    ]
