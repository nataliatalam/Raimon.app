import pytest
from unittest.mock import AsyncMock, patch
from agent_mvp.do_selector import DoSelector
from agent_mvp.contracts import (
    PriorityCandidates, TaskCandidate, UserProfile,
    CheckInConstraints, SelectionResult
)


class TestDoSelector:
    @pytest.fixture
    def do_selector(self):
        return DoSelector()

    @pytest.fixture
    def mock_storage(self):
        return AsyncMock()

    @pytest.fixture
    def sample_user_profile(self):
        return UserProfile(
            user_id="test-user",
            energy_patterns={"morning": "high", "afternoon": "medium"},
            focus_preferences=["deep_work", "meetings"],
            time_preferences={"work_hours": "9-17"},
            productivity_patterns={"peak_hours": ["10-12"]},
            task_completion_history=[]
        )

    @pytest.fixture
    def sample_constraints(self):
        return CheckInConstraints(
            energy_level=7,
            focus_areas=["work", "personal"],
            time_available=120,  # 2 hours
            current_context="office"
        )

    @pytest.fixture
    def sample_candidates(self):
        return PriorityCandidates(
            candidates=[
                TaskCandidate(
                    id="task-1",
                    title="High priority task",
                    priority="high",
                    estimated_duration=30,
                    project="work",
                    tags=["urgent"],
                    due_date="2024-01-02"
                ),
                TaskCandidate(
                    id="task-2",
                    title="Medium priority task",
                    priority="medium",
                    estimated_duration=60,
                    project="personal",
                    tags=["planning"],
                    due_date=None
                ),
                TaskCandidate(
                    id="task-3",
                    title="Low priority task",
                    priority="low",
                    estimated_duration=15,
                    project="work",
                    tags=["maintenance"],
                    due_date=None
                )
            ]
        )

    def test_calculate_task_score(self, do_selector, sample_user_profile, sample_constraints):
        # Test scoring logic
        candidate = TaskCandidate(
            id="task-1",
            title="Test task",
            priority="high",
            estimated_duration=30,
            project="work",
            tags=["urgent"],
            due_date="2024-01-02"
        )

        score = do_selector._calculate_task_score(
            candidate, sample_user_profile, sample_constraints
        )

        # Should have base score from priority (high = 100)
        # Plus bonuses for matching focus area, time fit, etc.
        assert score >= 100  # Minimum from high priority
        assert isinstance(score, float)

    def test_filter_candidates_by_constraints(self, do_selector, sample_candidates, sample_constraints):
        # Test constraint filtering
        filtered = do_selector._filter_candidates_by_constraints(
            sample_candidates.candidates, sample_constraints
        )

        # All sample tasks should fit within 2 hours
        assert len(filtered) == 3

        # Test with tight time constraint
        tight_constraints = CheckInConstraints(
            energy_level=7,
            focus_areas=["work"],
            time_available=20,  # Only 20 minutes
            current_context="office"
        )

        filtered_tight = do_selector._filter_candidates_by_constraints(
            sample_candidates.candidates, tight_constraints
        )

        # Should only include tasks that fit in 20 minutes
        assert len(filtered_tight) == 1  # Only the 15-minute task

    def test_select_best_task(self, do_selector, sample_candidates, sample_user_profile, sample_constraints):
        # Test task selection
        result = do_selector._select_best_task(
            sample_candidates.candidates, sample_user_profile, sample_constraints
        )

        assert result is not None
        assert result.id in ["task-1", "task-2", "task-3"]
        assert result.score >= 0

    @patch('agent_mvp.do_selector.get_supabase')
    async def test_select_task_full_flow(self, mock_supabase, do_selector, mock_storage,
                                       sample_user_profile, sample_constraints, sample_candidates):
        # Setup mocks
        mock_storage.get_user_profile.return_value = sample_user_profile

        with patch.object(do_selector, 'storage', mock_storage):
            # Execute
            result = await do_selector.select_task(
                user_id="test-user",
                constraints=sample_constraints,
                candidates=sample_candidates
            )

            # Assert
            assert isinstance(result, SelectionResult)
            assert result.task is not None
            assert result.selection_reason is not None
            assert result.coaching_message is not None
            assert len(result.selection_reason) > 0
            assert len(result.coaching_message) > 0

            mock_storage.get_user_profile.assert_called_once_with("test-user")

    @patch('agent_mvp.do_selector.get_supabase')
    async def test_select_task_no_candidates(self, mock_supabase, do_selector, mock_storage,
                                          sample_user_profile, sample_constraints):
        # Setup with no candidates
        empty_candidates = PriorityCandidates(candidates=[])
        mock_storage.get_user_profile.return_value = sample_user_profile

        with patch.object(do_selector, 'storage', mock_storage):
            # Execute
            result = await do_selector.select_task(
                user_id="test-user",
                constraints=sample_constraints,
                candidates=empty_candidates
            )

            # Assert - should return a fallback task
            assert isinstance(result, SelectionResult)
            assert result.task is not None
            assert "no suitable tasks" in result.selection_reason.lower()

    def test_energy_time_alignment(self, do_selector):
        # Test energy alignment scoring
        # High energy + short task = good alignment
        score1 = do_selector._calculate_energy_alignment(9, 15)  # High energy, short task
        score2 = do_selector._calculate_energy_alignment(3, 120)  # Low energy, long task
        score3 = do_selector._calculate_energy_alignment(7, 60)  # Medium energy, medium task

        assert score1 > score2  # High energy + short task should score better
        assert score3 > score2  # Medium alignment better than poor alignment

    def test_context_matching(self, do_selector):
        # Test context matching
        task_tags = ["meeting", "urgent", "planning"]
        focus_areas = ["work", "meetings"]

        score = do_selector._calculate_context_match(task_tags, focus_areas)
        assert score >= 0
        assert score <= 100

        # Perfect match should score high
        perfect_score = do_selector._calculate_context_match(["work", "urgent"], ["work", "urgent"])
        assert perfect_score > score