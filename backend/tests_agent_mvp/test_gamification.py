import pytest
from unittest.mock import AsyncMock, patch
from agent_mvp.gamification_rules import GamificationRules
from agent_mvp.contracts import GamificationState, XpTransaction


class TestGamificationRules:
    @pytest.fixture
    def gamification_rules(self):
        return GamificationRules()

    @pytest.fixture
    def mock_storage(self):
        return AsyncMock()

    def test_calculate_level(self, gamification_rules):
        # Test level calculation
        assert gamification_rules._calculate_level(0) == 1
        assert gamification_rules._calculate_level(99) == 1
        assert gamification_rules._calculate_level(100) == 2
        assert gamification_rules._calculate_level(299) == 2
        assert gamification_rules._calculate_level(300) == 3

    def test_calculate_xp_for_task_completion(self, gamification_rules):
        # Test XP calculation for task completion
        assert gamification_rules._calculate_xp_for_task_completion("high") == 20
        assert gamification_rules._calculate_xp_for_task_completion("medium") == 15
        assert gamification_rules._calculate_xp_for_task_completion("low") == 10
        assert gamification_rules._calculate_xp_for_task_completion("unknown") == 10

    def test_calculate_xp_for_session_completion(self, gamification_rules):
        # Test XP calculation for session completion
        assert gamification_rules._calculate_xp_for_session_completion(25) == 5  # 25 minutes
        assert gamification_rules._calculate_xp_for_session_completion(60) == 10  # 1 hour
        assert gamification_rules._calculate_xp_for_session_completion(120) == 15  # 2 hours

    def test_update_streak(self, gamification_rules):
        # Test streak updates
        # First activity
        state = GamificationState(
            user_id="test-user",
            total_xp=0,
            level=1,
            current_streak=0,
            longest_streak=0,
            last_activity_date=None
        )
        updated_state = gamification_rules._update_streak(state, "2024-01-01")
        assert updated_state.current_streak == 1
        assert updated_state.longest_streak == 1

        # Consecutive day
        state.last_activity_date = "2023-12-31"
        updated_state = gamification_rules._update_streak(state, "2024-01-01")
        assert updated_state.current_streak == 2

        # Broken streak
        state.last_activity_date = "2023-12-29"
        updated_state = gamification_rules._update_streak(state, "2024-01-01")
        assert updated_state.current_streak == 1

    async def test_update_xp_task_completion(self, gamification_rules, mock_storage):
        # Setup
        with patch('agent_mvp.gamification_rules.get_supabase') as mock_supabase:
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
                "total_xp": 50,
                "level": 1,
                "current_streak": 2,
                "longest_streak": 3,
                "last_activity_date": "2024-01-01"
            }]

            with patch.object(gamification_rules, 'storage', mock_storage):
                # Execute
                result = await gamification_rules.update_xp(
                    user_id="test-user",
                    action="task_completed",
                    priority="high",
                    date="2024-01-02"
                )

                # Assert
                assert result["xp_gained"] == 20
                assert result["new_total_xp"] == 70
                assert result["new_level"] == 1
                mock_storage.save_xp_transaction.assert_called_once()
                mock_storage.update_gamification_state.assert_called_once()

    async def test_update_xp_session_completion(self, gamification_rules, mock_storage):
        # Setup
        with patch('agent_mvp.gamification_rules.get_supabase') as mock_supabase:
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
                "total_xp": 0,
                "level": 1,
                "current_streak": 0,
                "longest_streak": 0,
                "last_activity_date": None
            }]

            with patch.object(gamification_rules, 'storage', mock_storage):
                # Execute
                result = await gamification_rules.update_xp(
                    user_id="test-user",
                    action="session_completed",
                    session_duration_minutes=60,
                    date="2024-01-01"
                )

                # Assert
                assert result["xp_gained"] == 10
                assert result["new_total_xp"] == 10
                assert result["new_level"] == 1
                mock_storage.save_xp_transaction.assert_called_once()
                mock_storage.update_gamification_state.assert_called_once()

    async def test_get_gamification_state(self, gamification_rules):
        # Setup
        with patch('agent_mvp.gamification_rules.get_supabase') as mock_supabase:
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
                "total_xp": 150,
                "level": 2,
                "current_streak": 5,
                "longest_streak": 7,
                "last_activity_date": "2024-01-01"
            }]

            # Execute
            result = await gamification_rules.get_gamification_state("test-user")

            # Assert
            assert result.total_xp == 150
            assert result.level == 2
        assert result.current_streak == 5