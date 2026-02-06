"""
Test orchestrator routing and edge logic.

Tests for event routing and conditional edge handling.
"""

import pytest
from orchestrator.edges import route_event
from orchestrator.contracts import GraphState
from models.contracts import (
    AppOpenEvent,
    CheckInSubmittedEvent,
    DoNextEvent,
    DoActionEvent,
    DayEndEvent,
)


@pytest.mark.unit
@pytest.mark.orchestrator
class TestEventRouting:
    """Tests for orchestrator event routing."""

    def test_route_app_open_event(self):
        """Test routing for APP_OPEN event."""
        state = GraphState(
            user_id="user-123",
            current_event=AppOpenEvent(user_id="user-123")
        )

        route = route_event(state)

        assert route == "app_open"

    def test_route_checkin_event(self):
        """Test routing for CHECKIN_SUBMITTED event."""
        event = CheckInSubmittedEvent(
            user_id="user-123",
            energy_level=7,
            mood="motivated",
            focus_areas=["work"],
            time_available=120
        )
        state = GraphState(user_id="user-123", current_event=event)

        route = route_event(state)

        assert route == "checkin_submitted"

    def test_route_do_next_event(self):
        """Test routing for DO_NEXT event."""
        state = GraphState(
            user_id="user-123",
            current_event=DoNextEvent(user_id="user-123")
        )

        route = route_event(state)

        assert route == "do_next"

    def test_route_do_action_event(self):
        """Test routing for DO_ACTION event."""
        event = DoActionEvent(
            user_id="user-123",
            action="start",
            task_id="task-1",
            current_session={},
            time_stuck=0
        )
        state = GraphState(user_id="user-123", current_event=event)

        route = route_event(state)

        assert route == "do_action"

    def test_route_day_end_event(self):
        """Test routing for DAY_END event."""
        event = DayEndEvent(
            user_id="user-123",
            timestamp="2026-02-05T18:00:00"
        )
        state = GraphState(user_id="user-123", current_event=event)

        route = route_event(state)

        assert route == "day_end"

    def test_route_unknown_event(self):
        """Test routing for unknown event type."""
        state = GraphState(
            user_id="user-123",
            current_event={"type": "UNKNOWN_EVENT"}
        )

        route = route_event(state)

        assert route == "error"
        assert state.success is False

    def test_route_none_event(self):
        """Test routing when current_event is None."""
        state = GraphState(
            user_id="user-123",
            current_event=None
        )

        route = route_event(state)

        assert route == "error"
        assert state.success is False


@pytest.mark.unit
@pytest.mark.orchestrator
class TestEventRoutingConsistency:
    """Tests for event routing consistency."""

    def test_routing_is_deterministic(self):
        """Test that routing is deterministic for same event."""
        event = AppOpenEvent(user_id="user-123")
        state = GraphState(user_id="user-123", current_event=event)

        route1 = route_event(state)

        # Create identical state
        state2 = GraphState(user_id="user-123", current_event=event)
        route2 = route_event(state2)

        assert route1 == route2

    def test_routing_independent_of_state(self):
        """Test that routing only depends on event type."""
        event = DoNextEvent(user_id="user-123")

        # State with minimal fields
        state1 = GraphState(user_id="user-123", current_event=event)
        route1 = route_event(state1)

        # State with many fields populated
        state2 = GraphState(
            user_id="user-123",
            current_event=event,
            mood="energetic",
            energy_level=9,
            candidates=[{"id": "task-1"}],
            constraints={"max_minutes": 60}
        )
        route2 = route_event(state2)

        assert route1 == route2 == "do_next"

    def test_all_event_types_routed(self):
        """Test that all expected event types are routed."""
        event_types = {
            "app_open": AppOpenEvent(user_id="user-123"),
            "checkin_submitted": CheckInSubmittedEvent(
                user_id="user-123",
                energy_level=5,
                mood=None,
                focus_areas=[],
                time_available=None
            ),
            "do_next": DoNextEvent(user_id="user-123"),
            "do_action": DoActionEvent(
                user_id="user-123",
                action="start",
                task_id="task-1",
                current_session={},
                time_stuck=0
            ),
            "day_end": DayEndEvent(
                user_id="user-123",
                timestamp="2026-02-05T18:00:00"
            ),
        }

        for expected_route, event in event_types.items():
            state = GraphState(user_id="user-123", current_event=event)
            route = route_event(state)
            assert route == expected_route


@pytest.mark.unit
@pytest.mark.orchestrator
class TestEdgeMappings:
    """Tests for edge mappings and success paths."""

    def test_conditional_edge_mapping(self):
        """Test conditional edge mappings are correct."""
        from orchestrator.edges import get_edge_mappings

        mappings = get_edge_mappings()

        assert mappings["app_open"] == "handle_app_open"
        assert mappings["checkin_submitted"] == "handle_checkin"
        assert mappings["do_next"] == "handle_do_next"
        assert mappings["do_action"] == "handle_do_action"
        assert mappings["day_end"] == "handle_day_end"
        assert mappings["error"] == "return_result"

    def test_success_path_edges(self):
        """Test success path edges point to return_result."""
        from orchestrator.edges import get_success_path_edges

        edges = get_success_path_edges()

        # All handlers should have edges to return_result
        handler_edges = [e for e in edges]
        assert len(handler_edges) == 5

        for source, target in handler_edges:
            assert target == "return_result"
            assert source in [
                "handle_app_open",
                "handle_checkin",
                "handle_do_next",
                "handle_do_action",
                "handle_day_end"
            ]

    def test_edge_completeness(self):
        """Test all handlers have success edges."""
        from orchestrator.edges import get_success_path_edges, get_edge_mappings

        handlers_in_mappings = [
            v for k, v in get_edge_mappings().items()
            if v != "return_result" and k != "error"
        ]

        edges = get_success_path_edges()
        handlers_with_edges = [source for source, _ in edges]

        assert set(handlers_with_edges) == set(handlers_in_mappings)


@pytest.mark.unit
@pytest.mark.orchestrator
class TestErrorHandling:
    """Tests for error routing and handling."""

    def test_error_route_on_malformed_event(self):
        """Test error route for malformed events."""
        state = GraphState(
            user_id="user-123",
            current_event={"invalid": "structure"}
        )

        route = route_event(state)

        assert route == "error"

    def test_error_route_updates_state(self):
        """Test that error routing updates state properly."""
        state = GraphState(
            user_id="user-123",
            current_event={"unknown": "event"}
        )

        original_success = state.success
        original_error = state.error

        route = route_event(state)

        # State should be updated with error
        assert state.success is False
        assert state.error is not None
        assert route == "error"

    def test_error_route_preserves_user_id(self):
        """Test that error route preserves user_id."""
        user_id = "important-user-123"
        state = GraphState(
            user_id=user_id,
            current_event={"invalid": "event"}
        )

        route_event(state)

        assert state.user_id == user_id
