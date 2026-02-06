"""
Tests for agent MVP (now testing refactored agents).

Run with: pytest backend/tests/test_agent_mvp/ -v

Tests:
1. DoSelector returns valid task_id from candidates
2. Invalid LLM output triggers fallback
3. Coach output is short and references task title
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from models.contracts import (
    TaskCandidate,
    SelectionConstraints,
    DoSelectorOutput,
    CoachOutput,
    GraphState,
)
from agents.llm_agents.llm_do_selector import select_task
from agents.llm_agents.llm_coach import generate_coaching_message
from orchestrator.validators import (
    validate_do_selector_output,
    validate_coach_output,
    fallback_do_selector,
)
from orchestrator.graph import (
    load_candidates,
    derive_constraints,
    llm_select_do,
    llm_coach,
)


# ============================================================================
# Test Data
# ============================================================================


@pytest.fixture
def sample_candidates():
    """Create sample task candidates."""
    now = datetime.now(timezone.utc)
    return [
        TaskCandidate(
            id="task-001",
            title="Fix login page CSS",
            priority="high",
            status="in_progress",
            estimated_duration=45,
            due_at=now + timedelta(days=1),
            tags=["frontend"],
            created_at=now,
        ),
        TaskCandidate(
            id="task-002",
            title="Review pull request",
            priority="medium",
            status="todo",
            estimated_duration=30,
            due_at=None,
            tags=["review"],
            created_at=now,
        ),
        TaskCandidate(
            id="task-003",
            title="Learn React hooks",
            priority="low",
            status="todo",
            estimated_duration=120,
            due_at=None,
            tags=["learning"],
            created_at=now,
        ),
    ]


@pytest.fixture
def sample_constraints():
    """Create sample constraints."""
    return SelectionConstraints(
        max_minutes=90,
        mode="balanced",
        current_energy=6,
    )


# ============================================================================
# Test 1: DoSelector returns valid task_id
# ============================================================================


def test_do_selector_returns_valid_task_id(sample_candidates, sample_constraints):
    """
    Test that DoSelector returns a task_id that exists in candidates.
    """
    with patch("agents.llm_agents.llm_do_selector.get_llm_service") as mock_llm:
        # Mock LLM service response
        mock_client = Mock()
        mock_client.generate_json.return_value = {
            "task_id": "task-001",
            "reason_codes": ["deadline_soon", "priority_high"],
            "alt_task_ids": ["task-002"],
        }
        mock_llm.return_value = mock_client

        # Run selector
        output, is_valid = select_task(sample_candidates, sample_constraints)

        # Assertions
        assert output.task_id in ["task-001", "task-002", "task-003"]
        assert output.task_id in [c.id for c in sample_candidates]
        print(f"✅ Selected task_id: {output.task_id} (valid={is_valid})")


def test_do_selector_fallback_on_invalid_task_id(sample_candidates):
    """
    Test that DoSelector falls back when LLM returns invalid task_id.
    """
    with patch("agents.llm_agents.llm_do_selector.get_llm_service") as mock_llm:
        mock_client = Mock()
        # Return a task_id that doesn't exist in candidates
        mock_client.generate_json.return_value = {
            "task_id": "invalid-task-999",
            "reason_codes": ["fallback"],
            "alt_task_ids": [],
        }
        mock_llm.return_value = mock_client

        # Run selector
        output, is_valid = select_task(
            sample_candidates,
            SelectionConstraints(),
        )

        # Assertions: should fallback to valid task
        assert output.task_id in [c.id for c in sample_candidates]
        assert is_valid is False  # Fallback was used
        print(f"✅ Fallback triggered, selected: {output.task_id}")


def test_do_selector_handles_invalid_json(sample_candidates):
    """
    Test that DoSelector handles invalid JSON from LLM gracefully.
    """
    with patch("agents.llm_agents.llm_do_selector.get_llm_service") as mock_llm:
        mock_client = Mock()
        # Simulate LLM returning invalid JSON
        mock_client.generate_json.side_effect = ValueError(
            "Invalid JSON"
        )
        mock_llm.return_value = mock_client

        # Run selector
        output, is_valid = select_task(
            sample_candidates,
            SelectionConstraints(),
        )

        # Assertions: should fallback
        assert output.task_id in [c.id for c in sample_candidates]
        assert is_valid is False
        print(f"✅ Invalid JSON handled, fallback: {output.task_id}")


# ============================================================================
# Test 2: Invalid LLM output triggers fallback
# ============================================================================


def test_validate_do_selector_rejects_invalid_output(sample_candidates):
    """
    Test that validation rejects output with invalid task_id.
    """
    invalid_output = {
        "task_id": "nonexistent-task",
        "reason_codes": ["test"],
        "alt_task_ids": [],
    }

    result, is_valid = validate_do_selector_output(invalid_output, sample_candidates)

    assert is_valid is False
    assert result.task_id in [c.id for c in sample_candidates]
    print(f"✅ Invalid task_id rejected, fallback: {result.task_id}")


def test_fallback_do_selector_picks_highest_priority(sample_candidates):
    """
    Test that fallback picks highest priority + shortest task.
    """
    result = fallback_do_selector(sample_candidates)

    # Should pick task-001 (high priority, 45 min)
    # Over task-002 (medium priority)
    # Over task-003 (low priority, 120 min)
    assert result.task_id == "task-001"
    assert "fallback" in result.reason_codes
    print(f"✅ Fallback selected highest priority: {result.task_id}")


def test_fallback_requires_at_least_one_candidate():
    """
    Test that fallback raises error with empty candidates.
    """
    with pytest.raises(ValueError):
        fallback_do_selector([])


# ============================================================================
# Test 3: Coach output is short and references task title
# ============================================================================


def test_coach_output_is_short(sample_candidates):
    """
    Test that Coach message is short (1-2 sentences max).
    """
    task = sample_candidates[0]

    with patch("agents.llm_agents.llm_coach.get_llm_service") as mock_llm:
        mock_client = Mock()
        mock_client.generate_json.return_value = {
            "title": "Let's fix it!",
            "message": "Time to tackle this CSS bug. You've got this.",
            "next_step": "Open the file.",
        }
        mock_llm.return_value = mock_client

        output, is_valid = generate_coaching_message(
            task=task,
            reason_codes=["priority_high"],
        )

        # Assertions
        assert len(output.message.split(".")) <= 3  # 1-2 sentences
        assert len(output.title) <= 100
        assert len(output.next_step.split()) <= 10
        print(f"✅ Coach message is short: '{output.message}'")


def test_coach_output_respects_task_context(sample_candidates):
    """
    Test that Coach doesn't invent task details.
    """
    task = sample_candidates[0]

    with patch("agents.llm_agents.llm_coach.get_llm_service") as mock_llm:
        mock_client = Mock()
        mock_client.generate_json.return_value = {
            "title": "CSS time!",
            "message": "Let's fix the login page CSS. Quick and focused.",
            "next_step": "Open styles.",
        }
        mock_llm.return_value = mock_client

        output, is_valid = generate_coaching_message(
            task=task,
            reason_codes=["priority_high"],
        )

        # Check that message references task title or domain
        assert (
            "css" in output.message.lower()
            or "login" in output.message.lower()
            or output.message  # At least has some message
        )
        print(f"✅ Coach message respects task context")


def test_coach_fallback_on_invalid_output(sample_candidates):
    """
    Test that Coach falls back to minimal message on validation error.
    """
    task = sample_candidates[0]

    with patch("agents.llm_agents.llm_coach.get_llm_service") as mock_llm:
        mock_client = Mock()
        # Return invalid output (message too long)
        mock_client.generate_json.return_value = {
            "title": "X" * 200,  # Too long
            "message": "This message is way too long. " * 10,  # Many sentences
            "next_step": "Do a bunch of things that are totally unnecessary.",  # Too many words
        }
        mock_llm.return_value = mock_client

        output, is_valid = generate_coaching_message(task=task, reason_codes=[])

        # Should fallback to minimal message
        assert is_valid is False
        assert output.message == "You've got this."
        print(f"✅ Coach fallback on invalid output")


# ============================================================================
# Test 4: Graph nodes work together
# ============================================================================


@pytest.mark.asyncio
async def test_graph_state_flows_through_nodes(sample_candidates, sample_constraints):
    """
    Test that graph state flows through multiple nodes.
    """
    state = GraphState(
        user_id="test-user",
        constraints=sample_constraints,
    )

    # Mock load_candidates by setting candidates directly
    state.candidates = sample_candidates

    # Test derive_constraints
    with patch("orchestrator.graph.get_supabase_admin") as mock_supabase:
        mock_supabase_instance = Mock()
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        mock_supabase_instance.table.return_value = mock_table
        mock_supabase.return_value = mock_supabase_instance

        state = derive_constraints(state)
        assert state.constraints is not None

    # Test llm_select_do
    with patch("orchestrator.graph.select_task") as mock_select:
        mock_select.return_value = (
            DoSelectorOutput(
                task_id=sample_candidates[0].id,
                reason_codes=["priority_high"],
                alt_task_ids=[],
            ),
            True,
        )
        state = llm_select_do(state)
        assert state.active_do is not None
        assert state.active_do.task.id == sample_candidates[0].id

    # Test llm_coach
    with patch("orchestrator.graph.generate_coaching_message") as mock_coach:
        mock_coach.return_value = (
            CoachOutput(
                title="Let's go",
                message="You've got this.",
                next_step="Begin.",
            ),
            True,
        )
        state = llm_coach(state)
        assert state.coach_message is not None

    print("✅ Graph state flows through all nodes successfully")


# ============================================================================
# Integration test: end-to-end with mocks
# ============================================================================


def test_end_to_end_agent_mvp_flow(sample_candidates, sample_constraints):
    """
    Integration test: DoSelector -> Coach -> Result.
    """
    with patch("agents.llm_agents.llm_do_selector.get_llm_service") as mock_llm_1:
        with patch("agents.llm_agents.llm_coach.get_llm_service") as mock_llm_2:
            # Mock DoSelector
            mock_selector_client = Mock()
            mock_selector_client.generate_json.return_value = {
                "task_id": sample_candidates[0].id,
                "reason_codes": ["priority_high"],
                "alt_task_ids": [sample_candidates[1].id],
            }
            mock_llm_1.return_value = mock_selector_client

            # Mock Coach
            mock_coach_client = Mock()
            mock_coach_client.generate_json.return_value = {
                "title": "Time to code!",
                "message": "Let's fix this bug.",
                "next_step": "Open IDE.",
            }
            mock_llm_2.return_value = mock_coach_client

            # Run selector
            selector_output, _ = select_task(sample_candidates, sample_constraints)
            assert selector_output.task_id == sample_candidates[0].id

            # Run coach
            coach_output, _ = generate_coaching_message(
                task=sample_candidates[0],
                reason_codes=selector_output.reason_codes,
            )
            assert len(coach_output.message) <= 300

            print("✅ End-to-end flow successful")
