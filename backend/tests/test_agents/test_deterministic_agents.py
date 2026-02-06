"""
Test deterministic agents.

Tests for pure logic agents with no LLM calls.
"""

import pytest
from unittest.mock import MagicMock
from agents.contracts import AgentInput, AgentOutput
from agents.deterministic_agents.base import BaseDeterministicAgent


@pytest.mark.unit
@pytest.mark.agent
class TestBaseDeterministicAgent:
    """Tests for BaseDeterministicAgent base class."""

    def test_base_deterministic_agent_initialization(self):
        """Test BaseDeterministicAgent initialization."""
        class TestAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                return AgentOutput(success=True, data={})

        agent = TestAgent()

        assert agent is not None

    def test_deterministic_agent_process_success(self):
        """Test successful deterministic agent processing."""
        class SuccessAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Pure logic - no external calls
                score = len(input_data.user_id) * 10
                return AgentOutput(
                    success=True,
                    data={"score": score},
                    execution_time_ms=1.0
                )

        agent = SuccessAgent()
        input_data = AgentInput(user_id="user-123")

        output = agent.process(input_data)

        assert output.success is True
        assert output.data["score"] == 80  # len("user-123") * 10

    def test_deterministic_agent_process_failure(self):
        """Test deterministic agent with validation error."""
        class ValidationAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Validate input
                if not input_data.user_id:
                    return AgentOutput(
                        success=False,
                        error="Empty user_id",
                        execution_time_ms=0.5
                    )
                return AgentOutput(success=True, data={})

        agent = ValidationAgent()
        input_data = AgentInput(user_id="")

        output = agent.process(input_data)

        assert output.success is False
        assert output.error == "Empty user_id"

    def test_deterministic_agent_with_metadata(self):
        """Test deterministic agent uses input metadata."""
        class MetadataAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Extract and process metadata
                priority = input_data.metadata.get("priority", "low")
                score_multiplier = {"high": 3, "medium": 2, "low": 1}[priority]

                return AgentOutput(
                    success=True,
                    data={"multiplier": score_multiplier}
                )

        agent = MetadataAgent()
        input_data = AgentInput(
            user_id="user-123",
            metadata={"priority": "high"}
        )

        output = agent.process(input_data)

        assert output.data["multiplier"] == 3

    def test_deterministic_agent_determinism(self):
        """Test that deterministic agent produces same output for same input."""
        class DeterministicAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Same input should produce same output
                result = input_data.user_id.upper()
                return AgentOutput(
                    success=True,
                    data={"uppercase": result}
                )

        agent = DeterministicAgent()
        input_data = AgentInput(user_id="test-user")

        output1 = agent.process(input_data)
        output2 = agent.process(input_data)

        assert output1.data == output2.data

    def test_deterministic_agent_execution_time(self):
        """Test deterministic agent execution time is minimal."""
        class FastAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Very fast operation - no I/O
                result = len(input_data.user_id)
                return AgentOutput(
                    success=True,
                    data={"length": result},
                    execution_time_ms=0.1
                )

        agent = FastAgent()
        input_data = AgentInput(user_id="user-123")

        output = agent.process(input_data)

        # Deterministic agents should be very fast
        assert output.execution_time_ms < 10.0


@pytest.mark.unit
@pytest.mark.agent
class TestDeterministicAgentPatterns:
    """Tests for common deterministic agent patterns."""

    def test_agent_scoring_logic(self):
        """Test deterministic agent with scoring logic."""
        class ScoringAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Deterministic scoring based on user_id length
                score = len(input_data.user_id) * 100
                return AgentOutput(
                    success=True,
                    data={"score": score}
                )

        agent = ScoringAgent()

        # Test multiple inputs
        output1 = agent.process(AgentInput(user_id="u"))
        output2 = agent.process(AgentInput(user_id="user-1234"))

        assert output1.data["score"] == 100
        assert output2.data["score"] == 900

    def test_agent_filtering_logic(self):
        """Test deterministic agent with filtering."""
        class FilterAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Filter based on metadata
                items = input_data.metadata.get("items", [])
                filtered = [i for i in items if i > 5]

                return AgentOutput(
                    success=True,
                    data={"filtered": filtered}
                )

        agent = FilterAgent()
        input_data = AgentInput(
            user_id="user-123",
            metadata={"items": [1, 3, 7, 10, 2, 8]}
        )

        output = agent.process(input_data)

        assert output.data["filtered"] == [7, 10, 8]

    def test_agent_data_transformation(self):
        """Test deterministic agent transforms data."""
        class TransformAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Transform user_id to metadata
                return AgentOutput(
                    success=True,
                    data={
                        "user_id": input_data.user_id,
                        "user_id_length": len(input_data.user_id),
                        "is_test_user": input_data.user_id.startswith("test"),
                    }
                )

        agent = TransformAgent()
        input_data = AgentInput(user_id="test-user-123")

        output = agent.process(input_data)

        assert output.data["user_id_length"] == 13
        assert output.data["is_test_user"] is True

    def test_agent_abstract_method(self):
        """Test that BaseDeterministicAgent.process is abstract."""
        # Trying to instantiate without implementing process should fail
        with pytest.raises(TypeError):
            BaseDeterministicAgent()

    def test_agent_error_handling(self):
        """Test deterministic agent error handling."""
        class ErrorHandlingAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                try:
                    # Attempt to process
                    if input_data.user_id == "invalid":
                        raise ValueError("Invalid user")
                    return AgentOutput(success=True, data={})
                except ValueError as e:
                    return AgentOutput(
                        success=False,
                        error=str(e)
                    )

        agent = ErrorHandlingAgent()

        # Test success case
        output_ok = agent.process(AgentInput(user_id="valid"))
        assert output_ok.success is True

        # Test error case
        output_err = agent.process(AgentInput(user_id="invalid"))
        assert output_err.success is False
        assert "Invalid user" in output_err.error


@pytest.mark.unit
@pytest.mark.agent
class TestDeterministicAgentVsLLM:
    """Tests comparing deterministic vs LLM patterns."""

    def test_deterministic_vs_llm_consistency(self):
        """Test deterministic agent is consistent vs simulated LLM."""
        class DeterministicSelector(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Always pick first task
                tasks = input_data.metadata.get("tasks", [])
                return AgentOutput(
                    success=True,
                    data={"selected": tasks[0] if tasks else None}
                )

        agent = DeterministicSelector()
        input_data = AgentInput(
            user_id="user-123",
            metadata={"tasks": ["task-a", "task-b", "task-c"]}
        )

        # Run multiple times
        results = [agent.process(input_data) for _ in range(5)]

        # All should be identical
        assert all(r.data["selected"] == "task-a" for r in results)

    def test_deterministic_reliability(self):
        """Test deterministic agent is always reliable."""
        class ReliableAgent(BaseDeterministicAgent):
            def process(self, input_data: AgentInput) -> AgentOutput:
                # Pure logic should never fail
                return AgentOutput(
                    success=True,
                    data={"processed": True}
                )

        agent = ReliableAgent()

        # Run many times
        for _ in range(100):
            output = agent.process(AgentInput(user_id="user-123"))
            assert output.success is True
