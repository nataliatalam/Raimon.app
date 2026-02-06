"""
Test agent I/O contracts.

Tests for AgentInput and AgentOutput Pydantic models.
"""

import pytest
from datetime import datetime, timezone
from agents.contracts import AgentInput, AgentOutput


@pytest.mark.unit
@pytest.mark.agent
class TestAgentInput:
    """Tests for AgentInput contract."""

    def test_agent_input_required_fields(self):
        """Test that user_id is required."""
        with pytest.raises(ValueError):
            AgentInput()

    def test_agent_input_valid(self):
        """Test creating valid AgentInput."""
        input_data = AgentInput(user_id="user-123")

        assert input_data.user_id == "user-123"
        assert input_data.timestamp is not None
        assert input_data.metadata == {}

    def test_agent_input_with_metadata(self):
        """Test AgentInput with metadata."""
        metadata = {"task_id": "task-456", "priority": "high"}
        input_data = AgentInput(user_id="user-123", metadata=metadata)

        assert input_data.metadata == metadata

    def test_agent_input_custom_timestamp(self):
        """Test AgentInput with custom timestamp."""
        timestamp = "2026-02-05T10:00:00"
        input_data = AgentInput(user_id="user-123", timestamp=timestamp)

        assert input_data.timestamp == timestamp

    def test_agent_input_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated if not provided."""
        before = datetime.now(timezone.utc).isoformat()
        input_data = AgentInput(user_id="user-123")
        after = datetime.now(timezone.utc).isoformat()

        assert before <= input_data.timestamp <= after


@pytest.mark.unit
@pytest.mark.agent
class TestAgentOutput:
    """Tests for AgentOutput contract."""

    def test_agent_output_defaults(self):
        """Test AgentOutput defaults."""
        output = AgentOutput()

        assert output.success is True
        assert output.data == {}
        assert output.error is None
        assert output.execution_time_ms is None

    def test_agent_output_successful(self):
        """Test creating successful AgentOutput."""
        data = {"selected_task": "task-789", "confidence": 0.95}
        output = AgentOutput(
            success=True,
            data=data,
            execution_time_ms=250.5
        )

        assert output.success is True
        assert output.data == data
        assert output.execution_time_ms == 250.5
        assert output.error is None

    def test_agent_output_with_error(self):
        """Test AgentOutput with error."""
        output = AgentOutput(
            success=False,
            error="LLM API timeout",
            execution_time_ms=30000.0
        )

        assert output.success is False
        assert output.error == "LLM API timeout"
        assert output.execution_time_ms == 30000.0

    def test_agent_output_complex_data(self):
        """Test AgentOutput with complex nested data."""
        data = {
            "task_id": "task-1",
            "alternatives": [
                {"id": "task-2", "score": 0.8},
                {"id": "task-3", "score": 0.7},
            ],
            "reasoning": {
                "primary": "high priority",
                "secondary": "short duration",
            },
        }
        output = AgentOutput(success=True, data=data)

        assert output.data == data
        assert len(output.data["alternatives"]) == 2

    def test_agent_output_validation(self):
        """Test AgentOutput field validation."""
        # execution_time_ms should be a number
        with pytest.raises((ValueError, TypeError)):
            AgentOutput(execution_time_ms="not_a_number")

    def test_agent_output_serialization(self):
        """Test AgentOutput can be serialized to dict."""
        output = AgentOutput(
            success=True,
            data={"key": "value"},
            execution_time_ms=100.0
        )

        output_dict = output.model_dump()

        assert output_dict["success"] is True
        assert output_dict["data"]["key"] == "value"
        assert output_dict["execution_time_ms"] == 100.0

    def test_agent_output_json_serialization(self):
        """Test AgentOutput can be converted to JSON."""
        output = AgentOutput(
            success=True,
            data={"key": "value"}
        )

        json_str = output.model_dump_json()

        assert "success" in json_str
        assert "true" in json_str.lower()


@pytest.mark.unit
@pytest.mark.agent
class TestAgentContractIntegration:
    """Tests for AgentInput/Output integration."""

    def test_agent_round_trip(self):
        """Test complete agent input/output flow."""
        # Create input
        input_data = AgentInput(
            user_id="user-123",
            metadata={"task_id": "task-456"}
        )

        # Simulate agent processing
        output = AgentOutput(
            success=True,
            data={"selected": "task-456"},
            execution_time_ms=150.0
        )

        # Verify both contracts are valid
        assert input_data.metadata["task_id"] == output.data["selected"]
        assert output.success is True

    def test_agent_error_flow(self):
        """Test error handling in agent contracts."""
        input_data = AgentInput(user_id="user-123")

        # Simulate error
        output = AgentOutput(
            success=False,
            error="Unable to select task",
            execution_time_ms=2000.0
        )

        # Verify error is properly captured
        assert not output.success
        assert output.error is not None
        assert len(output.data) == 0  # No data on error

    def test_agent_with_empty_metadata(self):
        """Test agent contracts with empty metadata."""
        input_data = AgentInput(
            user_id="user-123",
            metadata={}
        )

        assert input_data.metadata == {}
        assert len(input_data.metadata) == 0

    def test_agent_contract_immutability(self):
        """Test that contracts can be treated as immutable."""
        from pydantic_core import ValidationError
        input_data = AgentInput(user_id="user-123")

        # These should raise errors if models are immutable
        with pytest.raises((AttributeError, TypeError, ValidationError)):
            input_data.user_id = "user-999"
