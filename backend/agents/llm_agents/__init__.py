"""
LLM-powered agents for Raimon.

These agents make LLM calls (Gemini, Claude, etc.) with fallbacks.
"""

from agents.llm_agents.base import BaseLLMAgent, AgentInput, AgentOutput
from agents.llm_agents.context_continuity_agent import resume_context
from agents.llm_agents.stuck_pattern_agent import detect_stuck_patterns
from agents.llm_agents.project_insight_agent import generate_project_insights
from agents.llm_agents.motivation_agent import generate_motivation
from agents.llm_agents.llm_do_selector import select_task
from agents.llm_agents.llm_coach import generate_coaching_message

__all__ = [
    "BaseLLMAgent",
    "AgentInput",
    "AgentOutput",
    "resume_context",
    "detect_stuck_patterns",
    "generate_project_insights",
    "generate_motivation",
    "select_task",
    "generate_coaching_message",
]
