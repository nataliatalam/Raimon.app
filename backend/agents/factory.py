"""
Agent factory for dependency injection.

Creates and manages agent instances with proper dependencies.
"""

from typing import Optional, Dict, Any
from agents.llm_agents.base import BaseLLMAgent
from agents.deterministic_agents.base import BaseDeterministicAgent
from services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating agent instances.

    Manages agent instantiation and dependency injection.
    Provides singleton access to LLMService for all agents.
    """

    def __init__(self, llm_service: Optional[LLMService] = None, opik_tracker=None, storage=None, config=None, **kwargs):
        """
        Initialize agent factory.

        Args:
            llm_service: LLM service instance (defaults to LLMService() if not provided)
            opik_tracker: Opik tracker instance (optional)
            storage: Storage service instance (optional)
            config: Configuration dictionary (optional)
            **kwargs: Additional arguments (unused, for forward compatibility)
        """
        self.llm_service = llm_service or LLMService()
        self.opik_tracker = opik_tracker
        self.storage = storage
        self.config = config or {}
        self._agents: Dict[str, Any] = {}
        logger.info(f"[INFO] AgentFactory initialized with LLMService: {self.llm_service.__class__.__name__}")

    def create_llm_agent(
        self,
        agent_class: type,
        **kwargs
    ) -> BaseLLMAgent:
        """
        Create an LLM-powered agent.

        Args:
            agent_class: Agent class to instantiate
            **kwargs: Additional arguments to pass to agent

        Returns:
            Instantiated agent
        """
        try:
            agent = agent_class(
                llm_service=self.llm_service,
                opik_tracker=self.opik_tracker,
                **kwargs
            )
            logger.info(f"✅ Created LLM agent: {agent_class.__name__}")
            return agent
        except Exception as e:
            logger.error(f"❌ Failed to create LLM agent: {e}")
            raise

    def create_deterministic_agent(
        self,
        agent_class: type,
        **kwargs
    ) -> BaseDeterministicAgent:
        """
        Create a deterministic agent.

        Args:
            agent_class: Agent class to instantiate
            **kwargs: Additional arguments to pass to agent

        Returns:
            Instantiated agent
        """
        try:
            agent = agent_class(**kwargs)
            logger.info(f"✅ Created deterministic agent: {agent_class.__name__}")
            return agent
        except Exception as e:
            logger.error(f"❌ Failed to create deterministic agent: {e}")
            raise

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """
        Get a cached agent instance.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(agent_name)

    def register_agent(self, agent_name: str, agent: Any) -> None:
        """
        Register an agent for later retrieval.

        Args:
            agent_name: Name to register the agent under
            agent: Agent instance
        """
        self._agents[agent_name] = agent
        logger.info(f"✅ Registered agent: {agent_name}")

    def list_agents(self) -> Dict[str, str]:
        """
        List all registered agents.

        Returns:
            Dict of agent names and their types
        """
        return {
            name: type(agent).__name__
            for name, agent in self._agents.items()
        }


# Global factory instance
_factory: Optional[AgentFactory] = None


def get_factory(
    llm_service: Optional[LLMService] = None,
    opik_tracker=None,
    storage=None,
    config=None,
    **kwargs
) -> AgentFactory:
    """
    Get the global agent factory instance.

    Creates singleton if needed. Automatically creates LLMService if not provided.

    Args:
        llm_service: LLM service instance (optional, creates default LLMService if not provided)
        opik_tracker: Opik tracker (optional, for initialization)
        storage: Storage service (optional)
        config: Configuration dictionary (optional)
        **kwargs: Additional arguments (unused, for forward compatibility)

    Returns:
        Global AgentFactory instance
    """
    global _factory
    if _factory is None:
        _factory = AgentFactory(
            llm_service=llm_service,
            opik_tracker=opik_tracker,
            storage=storage,
            config=config,
            **kwargs
        )
        logger.info("[INFO] Global AgentFactory created with LLMService")
    return _factory


def reset_factory() -> None:
    """Reset the global factory instance."""
    global _factory
    _factory = None
