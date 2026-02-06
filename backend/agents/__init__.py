"""
Consolidated agents module for Raimon.

Exports all agent factories, base classes, contracts, and event definitions.

Note: Import from submodules directly to avoid circular imports:
  from agents.llm_agents.base import BaseLLMAgent
  from agents.llm_agents.llm_do_selector import select_task
  from agents.deterministic_agents.do_selector import select_optimal_task
"""

# Deterministic Agents (safe to import - don't depend on orchestrator)
from agents.deterministic_agents.base import BaseDeterministicAgent
from agents.deterministic_agents.do_selector import select_optimal_task as do_selector
from agents.deterministic_agents.user_profile_agent import analyze_user_profile as user_profile_agent
from agents.deterministic_agents.state_adapter_agent import adapt_checkin_to_constraints as state_adapter_agent
from agents.deterministic_agents.priority_engine_agent import score_task_priorities as priority_engine_agent
from agents.deterministic_agents.time_learning_agent import learn_time_patterns as time_learning_agent
from agents.deterministic_agents.gamification_rules import update_gamification

# Contracts and events (safe to import)
from agents.contracts import AgentInput, AgentOutput
from agents.events import log_agent_event

# Factory (safe to import)
from agents.factory import AgentFactory, get_factory, reset_factory

# NOTE: Removed eager imports from agents.llm_agents to break circular dependency
# with orchestrator. Users must import directly:
#   from agents.llm_agents.base import BaseLLMAgent
#   from agents.llm_agents.llm_do_selector import select_task

__all__ = [
    # Base classes
    "BaseDeterministicAgent",
    # Contracts
    "AgentInput",
    "AgentOutput",
    # Events
    "log_agent_event",
    # Factory
    "AgentFactory",
    "get_factory",
    "reset_factory",
    # Deterministic Agents
    "do_selector",
    "user_profile_agent",
    "state_adapter_agent",
    "priority_engine_agent",
    "time_learning_agent",
    "update_gamification",
]
