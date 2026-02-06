"""
Orchestrator module for Raimon.

Contains LangGraph orchestration, state management, and event routing.

Modules:
- orchestrator.py: Main RaimonOrchestrator class for event processing
- graph.py: LangGraph workflow definition and compilation
- contracts.py: GraphState and orchestrator-specific data models
- nodes.py: Individual node handler functions for each event type
- edges.py: Conditional routing logic and edge definitions
- validators.py: Validation and fallback logic

Note: Import from submodules directly to avoid circular imports:
  from orchestrator.orchestrator import RaimonOrchestrator
  from orchestrator.nodes import node_start, ...
  from orchestrator.edges import route_event, ...
"""

from orchestrator.contracts import GraphState
# NOTE: Removed eager import of orchestrator.orchestrator to break circular dependency
# Users must import directly: from orchestrator.orchestrator import RaimonOrchestrator
from orchestrator.nodes import (
    node_start,
    node_return_result,
    node_handle_app_open,
    node_handle_checkin,
    node_handle_do_next,
    node_handle_do_action,
    node_handle_day_end,
)
from orchestrator.edges import route_event, get_edge_mappings, get_success_path_edges

__all__ = [
    # Contracts
    "GraphState",
    # Nodes
    "node_start",
    "node_return_result",
    "node_handle_app_open",
    "node_handle_checkin",
    "node_handle_do_next",
    "node_handle_do_action",
    "node_handle_day_end",
    # Edges
    "route_event",
    "get_edge_mappings",
    "get_success_path_edges",
]
