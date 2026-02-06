"""
Test orchestrator graph and state management.

Tests for LangGraph configuration and state transitions.
"""

import pytest
from orchestrator.contracts import GraphState
from datetime import datetime, timezone


@pytest.mark.unit
@pytest.mark.orchestrator
class TestGraphState:
    """Tests for GraphState contract."""

    def test_graph_state_initialization(self):
        """Test basic GraphState creation."""
        state = GraphState(user_id="user-123")

        assert state.user_id == "user-123"
        assert state.success is True
        assert state.error is None

    def test_graph_state_with_mood_and_energy(self):
        """Test GraphState with mood and energy tracking."""
        state = GraphState(
            user_id="user-123",
            mood="motivated",
            energy_level=8
        )

        assert state.mood == "motivated"
        assert state.energy_level == 8

    def test_graph_state_energy_level_validation(self):
        """Test energy_level is validated (1-10 range)."""
        # Valid energy levels
        state1 = GraphState(user_id="user-123", energy_level=1)
        state2 = GraphState(user_id="user-123", energy_level=10)

        assert state1.energy_level == 1
        assert state2.energy_level == 10

        # Invalid energy levels should raise error
        with pytest.raises(ValueError):
            GraphState(user_id="user-123", energy_level=0)

        with pytest.raises(ValueError):
            GraphState(user_id="user-123", energy_level=11)

    def test_graph_state_with_candidates(self):
        """Test GraphState with task candidates."""
        candidates = [
            {"id": "task-1", "title": "Task 1"},
            {"id": "task-2", "title": "Task 2"},
        ]
        state = GraphState(
            user_id="user-123",
            candidates=candidates
        )

        assert len(state.candidates) == 2
        assert state.candidates[0]["id"] == "task-1"

    def test_graph_state_with_constraints(self):
        """Test GraphState with selection constraints."""
        constraints = {
            "max_minutes": 120,
            "mode": "balanced",
            "current_energy": 7
        }
        state = GraphState(
            user_id="user-123",
            constraints=constraints
        )

        assert state.constraints["max_minutes"] == 120

    def test_graph_state_with_active_do(self):
        """Test GraphState tracks active task."""
        active = {
            "task_id": "task-1",
            "reason": "High priority"
        }
        state = GraphState(
            user_id="user-123",
            active_do=active
        )

        assert state.active_do["task_id"] == "task-1"

    def test_graph_state_with_intervention_logs(self):
        """Test GraphState tracks intervention history."""
        logs = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "stuck",
                "action": "micro-task"
            },
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "break",
                "duration_minutes": 15
            }
        ]
        state = GraphState(
            user_id="user-123",
            intervention_logs=logs
        )

        assert len(state.intervention_logs) == 2
        assert state.intervention_logs[0]["type"] == "stuck"

    def test_graph_state_with_opik_trace_id(self):
        """Test GraphState tracks Opik trace ID."""
        state = GraphState(
            user_id="user-123",
            opik_trace_id="trace-abc-123"
        )

        assert state.opik_trace_id == "trace-abc-123"

    def test_graph_state_error_tracking(self):
        """Test GraphState tracks errors."""
        state = GraphState(
            user_id="user-123",
            success=False,
            error="Task selection failed"
        )

        assert state.success is False
        assert state.error == "Task selection failed"

    def test_graph_state_with_all_fields(self):
        """Test GraphState with all fields populated."""
        state = GraphState(
            user_id="user-123",
            current_event={"type": "APP_OPEN"},
            mood="focused",
            energy_level=7,
            candidates=[{"id": "task-1"}],
            constraints={"max_minutes": 60},
            active_do={"task_id": "task-1"},
            coach_message={"message": "Let's do this!"},
            motivation_message={"message": "You got this!"},
            intervention_logs=[],
            opik_trace_id="trace-123",
            success=True,
            error=None
        )

        assert state.user_id == "user-123"
        assert state.mood == "focused"
        assert state.energy_level == 7
        assert len(state.candidates) == 1
        assert state.success is True

    def test_graph_state_serialization(self):
        """Test GraphState can be serialized."""
        state = GraphState(
            user_id="user-123",
            mood="motivated",
            energy_level=8
        )

        state_dict = state.model_dump()

        assert state_dict["user_id"] == "user-123"
        assert state_dict["mood"] == "motivated"
        assert state_dict["energy_level"] == 8

    def test_graph_state_json_roundtrip(self):
        """Test GraphState can be converted to/from JSON."""
        state = GraphState(
            user_id="user-123",
            mood="focused",
            energy_level=7,
            intervention_logs=[
                {"type": "stuck", "time": "2026-02-05T10:00:00"}
            ]
        )

        # Serialize to JSON
        json_str = state.model_dump_json()

        # Deserialize back
        new_state = GraphState.model_validate_json(json_str)

        assert new_state.user_id == state.user_id
        assert new_state.mood == state.mood
        assert new_state.energy_level == state.energy_level
        assert len(new_state.intervention_logs) == 1


@pytest.mark.unit
@pytest.mark.orchestrator
class TestGraphStateTransitions:
    """Tests for GraphState transitions in workflow."""

    def test_app_open_state_transition(self):
        """Test state transition for APP_OPEN event."""
        # Initial state
        state = GraphState(user_id="user-123")

        # Simulate APP_OPEN handler updating state
        state.current_event = {"type": "APP_OPEN"}
        state.context_resumption = {"context": "previous_session"}

        assert state.current_event["type"] == "APP_OPEN"

    def test_checkin_state_transition(self):
        """Test state transition for CHECKIN event."""
        state = GraphState(user_id="user-123")

        # Simulate CHECKIN handler
        state.current_event = {"type": "CHECKIN_SUBMITTED"}
        state.mood = "energetic"
        state.energy_level = 8
        state.constraints = {"max_minutes": 120}

        assert state.mood == "energetic"
        assert state.energy_level == 8

    def test_do_next_state_transition(self):
        """Test state transition for DO_NEXT event."""
        state = GraphState(user_id="user-123")

        # Simulate DO_NEXT handler
        state.current_event = {"type": "DO_NEXT"}
        state.candidates = [
            {"id": "task-1", "priority": "high"},
            {"id": "task-2", "priority": "low"}
        ]
        state.active_do = {"task_id": "task-1"}

        assert len(state.candidates) == 2
        assert state.active_do["task_id"] == "task-1"

    def test_do_action_state_transition(self):
        """Test state transition for DO_ACTION event."""
        state = GraphState(user_id="user-123")

        # Simulate DO_ACTION handler
        state.current_event = {
            "type": "DO_ACTION",
            "action": "complete"
        }
        state.motivation_message = {"message": "Great job!"}

        assert state.current_event["action"] == "complete"

    def test_day_end_state_transition(self):
        """Test state transition for DAY_END event."""
        state = GraphState(user_id="user-123")

        # Simulate DAY_END handler
        state.current_event = {"type": "DAY_END"}
        state.day_insights = [
            {"type": "completion", "tasks_completed": 5},
            {"type": "summary", "total_time": 480}
        ]

        assert len(state.day_insights) == 2

    def test_error_state_transition(self):
        """Test state transition on error."""
        state = GraphState(user_id="user-123")

        # Simulate error
        state.success = False
        state.error = "Task selection failed"
        state.intervention_logs.append({
            "type": "error",
            "message": "Task selection failed"
        })

        assert state.success is False
        assert len(state.intervention_logs) == 1

    def test_intervention_logging(self):
        """Test intervention logs are properly tracked."""
        state = GraphState(user_id="user-123")

        # Log multiple interventions
        state.intervention_logs.append({"type": "stuck", "time": "10:00"})
        state.intervention_logs.append({"type": "break", "time": "10:30"})
        state.intervention_logs.append({"type": "resume", "time": "10:45"})

        assert len(state.intervention_logs) == 3
        assert state.intervention_logs[0]["type"] == "stuck"
        assert state.intervention_logs[2]["type"] == "resume"
