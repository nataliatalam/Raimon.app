import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent_mvp.orchestrator import RaimonOrchestrator
from agent_mvp.contracts import (
    AppOpenEvent, CheckInSubmittedEvent, DoActionEvent,
    DayEndEvent, UserProfile, GamificationState
)


class TestRaimonOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        return RaimonOrchestrator()

    @pytest.fixture
    def mock_storage(self):
        return AsyncMock()

    @pytest.fixture
    def mock_agents(self):
        return {
            'user_profile_agent': AsyncMock(),
            'project_profile_agent': AsyncMock(),
            'priority_engine_agent': AsyncMock(),
            'state_adapter_agent': AsyncMock(),
            'time_learning_agent': AsyncMock(),
            'context_continuity_agent': AsyncMock(),
            'stuck_pattern_agent': AsyncMock(),
            'project_insight_agent': AsyncMock(),
            'motivation_agent': AsyncMock(),
            'do_selector': AsyncMock(),
            'gamification_rules': AsyncMock(),
            'coach': AsyncMock(),
            'events': AsyncMock()
        }

    @patch('agent_mvp.orchestrator.get_supabase')
    def test_process_app_open_event(self, mock_supabase, orchestrator, mock_storage, mock_agents):
        # Setup
        event = AppOpenEvent(user_id="test-user", timestamp="2024-01-01T00:00:00Z")
        mock_storage.get_session_state.return_value = None
        mock_agents['context_continuity_agent'].process.return_value = {"resumed": False}

        with patch.object(orchestrator, 'storage', mock_storage), \
             patch.object(orchestrator, 'agents', mock_agents):

            # Execute
            result = orchestrator.process_event(event)

            # Assert
            assert result["event_type"] == "APP_OPEN"
            mock_storage.get_session_state.assert_called_once_with("test-user")
            mock_agents['context_continuity_agent'].process.assert_called_once()
            mock_agents['events'].log_event.assert_called_once()

    @patch('agent_mvp.orchestrator.get_supabase')
    def test_process_checkin_submitted_event(self, mock_supabase, orchestrator, mock_storage, mock_agents):
        # Setup
        event = CheckInSubmittedEvent(
            user_id="test-user",
            energy_level=7,
            focus_areas=["work", "personal"],
            timestamp="2024-01-01T00:00:00Z"
        )
        mock_agents['state_adapter_agent'].process.return_value = {"constraints": []}
        mock_agents['priority_engine_agent'].process.return_value = {"candidates": []}
        mock_agents['do_selector'].select_task.return_value = {"task": {}, "reason": "test"}

        with patch.object(orchestrator, 'storage', mock_storage), \
             patch.object(orchestrator, 'agents', mock_agents):

            # Execute
            result = orchestrator.process_event(event)

            # Assert
            assert result["event_type"] == "CHECKIN_SUBMITTED"
            mock_agents['state_adapter_agent'].process.assert_called_once()
            mock_agents['priority_engine_agent'].process.assert_called_once()
            mock_agents['do_selector'].select_task.assert_called_once()
            mock_storage.save_active_do.assert_called_once()

    @patch('agent_mvp.orchestrator.get_supabase')
    def test_process_do_action_event(self, mock_supabase, orchestrator, mock_storage, mock_agents):
        # Setup
        event = DoActionEvent(
            user_id="test-user",
            action="start",
            task_id="task-123",
            timestamp="2024-01-01T00:00:00Z"
        )
        mock_storage.get_active_do.return_value = {"task": {"id": "task-123"}}

        with patch.object(orchestrator, 'storage', mock_storage), \
             patch.object(orchestrator, 'agents', mock_agents):

            # Execute
            result = orchestrator.process_event(event)

            # Assert
            assert result["event_type"] == "DO_ACTION"
            mock_storage.get_active_do.assert_called_once_with("test-user")
            mock_agents['events'].log_event.assert_called_once()

    @patch('agent_mvp.orchestrator.get_supabase')
    def test_process_day_end_event(self, mock_supabase, orchestrator, mock_storage, mock_agents):
        # Setup
        event = DayEndEvent(user_id="test-user", timestamp="2024-01-01T00:00:00Z")
        mock_agents['project_insight_agent'].generate_insights.return_value = {"insights": []}
        mock_agents['motivation_agent'].generate_message.return_value = "Great job!"
        mock_agents['gamification_rules'].update_xp.return_value = {"xp_gained": 10}

        with patch.object(orchestrator, 'storage', mock_storage), \
             patch.object(orchestrator, 'agents', mock_agents):

            # Execute
            result = orchestrator.process_event(event)

            # Assert
            assert result["event_type"] == "DAY_END"
            mock_agents['project_insight_agent'].generate_insights.assert_called_once()
            mock_agents['motivation_agent'].generate_message.assert_called_once()
            mock_agents['gamification_rules'].update_xp.assert_called_once()
            mock_storage.save_insights.assert_called_once()

    def test_invalid_event_type(self, orchestrator):
        # Setup
        event = MagicMock()
        event.event_type = "INVALID_EVENT"

        # Execute & Assert
        with pytest.raises(ValueError, match="Unknown event type"):
            orchestrator.process_event(event)