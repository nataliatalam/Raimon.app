"""
Test LLM-powered agents.

Tests for agent functionality, contract compliance, and error handling.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agents.contracts import AgentInput, AgentOutput
from agents.llm_agents.base import BaseLLMAgent


@pytest.mark.unit
@pytest.mark.agent
@pytest.mark.anyio
class TestBaseLLMAgent:
    """Tests for BaseLLMAgent base class."""

    def test_base_llm_agent_initialization(self):
        """Test BaseLLMAgent initialization."""
        mock_llm = MagicMock()

        # Create concrete subclass for testing
        class TestAgent(BaseLLMAgent):
            async def process(self, input_data: AgentInput) -> AgentOutput:
                return AgentOutput(success=True, data={})

        agent = TestAgent(llm_service=mock_llm)

        assert agent.llm_service == mock_llm

    def test_base_llm_agent_with_opik(self):
        """Test BaseLLMAgent with Opik tracker."""
        mock_llm = MagicMock()
        mock_opik = MagicMock()

        class TestAgent(BaseLLMAgent):
            async def process(self, input_data: AgentInput) -> AgentOutput:
                return AgentOutput(success=True, data={})

        agent = TestAgent(llm_service=mock_llm, opik_tracker=mock_opik)

        assert agent.opik_tracker == mock_opik

    @pytest.mark.asyncio
    async def test_llm_agent_process_success(self):
        """Test successful LLM agent processing."""
        class SuccessAgent(BaseLLMAgent):
            async def process(self, input_data: AgentInput) -> AgentOutput:
                return AgentOutput(
                    success=True,
                    data={"result": "success"},
                    execution_time_ms=100.0
                )

        agent = SuccessAgent(llm_service=MagicMock())
        input_data = AgentInput(user_id="user-123")

        output = await agent.process(input_data)

        assert output.success is True
        assert output.data["result"] == "success"

    @pytest.mark.asyncio
    async def test_llm_agent_process_failure(self):
        """Test LLM agent processing with error."""
        class FailureAgent(BaseLLMAgent):
            async def process(self, input_data: AgentInput) -> AgentOutput:
                return AgentOutput(
                    success=False,
                    error="LLM API failed",
                    execution_time_ms=5000.0
                )

        agent = FailureAgent(llm_service=MagicMock())
        input_data = AgentInput(user_id="user-123")

        output = await agent.process(input_data)

        assert output.success is False
        assert output.error == "LLM API failed"

    @pytest.mark.asyncio
    async def test_llm_agent_with_metadata(self):
        """Test LLM agent respects input metadata."""
        class MetadataAgent(BaseLLMAgent):
            async def process(self, input_data: AgentInput) -> AgentOutput:
                # Process should use metadata
                task_id = input_data.metadata.get("task_id")
                return AgentOutput(
                    success=True,
                    data={"task_id": task_id}
                )

        agent = MetadataAgent(llm_service=MagicMock())
        input_data = AgentInput(
            user_id="user-123",
            metadata={"task_id": "task-456"}
        )

        output = await agent.process(input_data)

        assert output.data["task_id"] == "task-456"

    @pytest.mark.asyncio
    async def test_llm_agent_execution_time(self):
        """Test LLM agent tracks execution time."""
        import time

        class TimedAgent(BaseLLMAgent):
            async def process(self, input_data: AgentInput) -> AgentOutput:
                # Simulate some work
                await AsyncMock(return_value=None)()
                return AgentOutput(
                    success=True,
                    data={},
                    execution_time_ms=150.0
                )

        agent = TimedAgent(llm_service=MagicMock())
        input_data = AgentInput(user_id="user-123")

        output = await agent.process(input_data)

        assert output.execution_time_ms == 150.0

    def test_llm_agent_abstract_method(self):
        """Test that BaseLLMAgent.process is abstract."""
        # Trying to instantiate BaseLLMAgent directly should fail
        with pytest.raises(TypeError):
            BaseLLMAgent(llm_service=MagicMock())


@pytest.mark.unit
@pytest.mark.agent
@pytest.mark.anyio
class TestLLMAgentPatterns:
    """Tests for common LLM agent patterns."""

    @pytest.mark.asyncio
    async def test_agent_input_validation(self):
        """Test LLM agent validates input contracts."""
        class ValidationAgent(BaseLLMAgent):
            async def process(self, input_data: AgentInput) -> AgentOutput:
                # Verify input is AgentInput instance
                assert isinstance(input_data, AgentInput)
                assert input_data.user_id is not None
                return AgentOutput(success=True, data={})

        agent = ValidationAgent(llm_service=MagicMock())
        input_data = AgentInput(user_id="user-123")

        output = await agent.process(input_data)

        assert output.success is True

    @pytest.mark.asyncio
    async def test_agent_output_validation(self):
        """Test LLM agent produces valid output contracts."""
        class OutputAgent(BaseLLMAgent):
            async def process(self, input_data: AgentInput) -> AgentOutput:
                return AgentOutput(
                    success=True,
                    data={"key": "value"},
                    execution_time_ms=100.0
                )

        agent = OutputAgent(llm_service=MagicMock())
        input_data = AgentInput(user_id="user-123")

        output = await agent.process(input_data)

        # Verify output is valid AgentOutput
        assert isinstance(output, AgentOutput)
        assert output.success is True
        assert isinstance(output.execution_time_ms, float)

    @pytest.mark.asyncio
    async def test_agent_error_with_data(self):
        """Test agent can include data even when error occurs."""
        class PartialErrorAgent(BaseLLMAgent):
            async def process(self, input_data: AgentInput) -> AgentOutput:
                return AgentOutput(
                    success=False,
                    error="Partial failure",
                    data={"partial_result": "something"},
                    execution_time_ms=1000.0
                )

        agent = PartialErrorAgent(llm_service=MagicMock())
        input_data = AgentInput(user_id="user-123")

        output = await agent.process(input_data)

        assert output.success is False
        assert "partial_result" in output.data

    @pytest.mark.asyncio
    async def test_agent_with_opik_decorator(self):
        """Test LLM agent integration with Opik @track decorator."""
        from opik import track

        class TrackedAgent(BaseLLMAgent):
            @track(name="test_agent")
            async def process(self, input_data: AgentInput) -> AgentOutput:
                return AgentOutput(success=True, data={})

        agent = TrackedAgent(llm_service=MagicMock())
        input_data = AgentInput(user_id="user-123")

        # Decorator should not break execution
        output = await agent.process(input_data)

        assert output.success is True
