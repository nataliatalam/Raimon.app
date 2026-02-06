import pytest
from unittest.mock import AsyncMock, patch
from agents.events import EventLogger
from models.contracts import AgentEvent, AppOpenEvent, CheckInSubmittedEvent

# @pytest.mark.asyncio
class TestEventLogger:
    @pytest.fixture
    def event_logger(self):
        return EventLogger()

    def test_create_event_data_app_open(self, event_logger):
        # Test event data creation for app open
        event = AppOpenEvent(
            user_id="test-user",
            timestamp="2024-01-01T09:00:00Z"
        )

        event_data = event_logger._create_event_data(event)

        assert event_data["event_type"] == "APP_OPEN"
        assert event_data["user_id"] == "test-user"
        assert event_data["timestamp"] == "2024-01-01T09:00:00Z"
        assert "metadata" in event_data

    def test_create_event_data_checkin_submitted(self, event_logger):
        # Test event data creation for check-in
        event = CheckInSubmittedEvent(
            user_id="test-user",
            energy_level=8,
            focus_areas=["work", "learning"],
            time_available=90,
            timestamp="2024-01-01T09:15:00Z"
        )

        event_data = event_logger._create_event_data(event)

        assert event_data["event_type"] == "CHECKIN_SUBMITTED"
        assert event_data["energy_level"] == 8
        assert event_data["focus_areas"] == ["work", "learning"]
        assert event_data["time_available"] == 90


    @pytest.mark.asyncio
    async def test_log_event_success(self, event_logger):
        # Setup
        with patch('agents.events.get_supabase') as mock_supabase:
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "event-123",
                "event_type": "APP_OPEN",
                "timestamp": "2024-01-01T09:00:00Z"
            }]

            event = AppOpenEvent(user_id="test-user", timestamp="2024-01-01T09:00:00Z")

            # Execute
            result = await event_logger.log_event(event)

            # Assert
            assert result is True
            mock_supabase.assert_called()
            mock_supabase.return_value.table.assert_called_with("agent_events")

    @pytest.mark.asyncio
    async def test_log_event_failure(self, event_logger):
        # Setup - simulate database error
        with patch('agents.events.get_supabase') as mock_supabase:
            mock_supabase.return_value.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")

            event = AppOpenEvent(user_id="test-user", timestamp="2024-01-01T09:00:00Z")

            # Execute
            result = await event_logger.log_event(event)

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_log_multiple_events(self, event_logger):
        # Setup
        with patch('agents.events.get_supabase') as mock_supabase:
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value.data = [
                {"id": "event-1"}, {"id": "event-2"}
            ]

            events = [
                AppOpenEvent(user_id="test-user", timestamp="2024-01-01T09:00:00Z"),
                CheckInSubmittedEvent(
                    user_id="test-user",
                    energy_level=7,
                    focus_areas=["work"],
                    timestamp="2024-01-01T09:15:00Z"
                )
            ]

            # Execute
            results = await event_logger.log_events(events)

            # Assert
            assert len(results) == 2
            assert all(results)  # All should be successful

    @pytest.mark.asyncio
    async def test_get_user_events(self, event_logger):
        # Setup
        with patch('agents.events.get_supabase') as mock_supabase:
            mock_events = [
                {
                    "id": "event-1",
                    "event_type": "APP_OPEN",
                    "event_data": {"user_id": "test-user"},
                    "timestamp": "2024-01-01T09:00:00Z"
                },
                {
                    "id": "event-2",
                    "event_type": "CHECKIN_SUBMITTED",
                    "event_data": {"energy_level": 8},
                    "timestamp": "2024-01-01T09:15:00Z"
                }
            ]
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = mock_events

            # Execute
            events = await event_logger.get_user_events("test-user", limit=10)

            # Assert
            assert len(events) == 2
            assert events[0]["event_type"] == "APP_OPEN"
            assert events[1]["event_type"] == "CHECKIN_SUBMITTED"

    @pytest.mark.asyncio
    async def test_get_events_by_type(self, event_logger):
        # Setup
        with patch('agents.events.get_supabase') as mock_supabase:
            mock_events = [
                {
                    "id": "event-1",
                    "event_type": "DO_ACTION",
                    "event_data": {"action": "start"},
                    "timestamp": "2024-01-01T10:00:00Z"
                }
            ]
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = mock_events

            # Execute
            events = await event_logger.get_events_by_type("test-user", "DO_ACTION")

            # Assert
            assert len(events) == 1
            assert events[0]["event_type"] == "DO_ACTION"
            assert events[0]["event_data"]["action"] == "start"

    @pytest.mark.asyncio
    async def test_get_system_events(self, event_logger):
        # Setup
        with patch('agents.events.get_supabase') as mock_supabase:
            mock_events = [
                {
                    "id": "event-1",
                    "event_type": "SYSTEM_MAINTENANCE",
                    "event_data": {"action": "backup"},
                    "timestamp": "2024-01-01T02:00:00Z"
                }
            ]
            mock_supabase.return_value.table.return_value.select.return_value.is_.return_value.order.return_value.execute.return_value.data = mock_events

            # Execute
            events = await event_logger.get_system_events()

            # Assert
            assert len(events) == 1
            assert events[0]["event_type"] == "SYSTEM_MAINTENANCE"

    def test_event_data_validation(self, event_logger):
        # Test that event data includes required fields
        event = AppOpenEvent(user_id="test-user", timestamp="2024-01-01T09:00:00Z")

        event_data = event_logger._create_event_data(event)

        required_fields = ["event_type", "timestamp", "metadata"]
        for field in required_fields:
            assert field in event_data

        # User events should include user_id
        assert "user_id" in event_data

    async def test_log_event_with_metadata(self, event_logger):
        # Setup
        with patch('agents.events.get_supabase') as mock_supabase:
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value.data = [{"id": "event-123"}]

            # Create event with additional metadata
            event = AppOpenEvent(
                user_id="test-user",
                timestamp="2024-01-01T09:00:00Z"
            )

            # Execute
            result = await event_logger.log_event(event)

            # Assert
            assert result is True
            # Verify the call includes event data
            mock_supabase.return_value.table.assert_called_with("agent_events")
