"""
Tests for DoSelector contract validation.

Run with: pytest backend/tests/test_agent_mvp/test_selector_contracts.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta
from models.contracts import (
    TaskCandidate,
    SelectionConstraints,
    DoSelectorOutput,
)
from orchestrator.validators import validate_do_selector_output


@pytest.fixture
def sample_task():
    """Create a sample task candidate."""
    return TaskCandidate(
        id="task-abc-123",
        title="Complete project report",
        priority="high",
        status="in_progress",
        estimated_duration=90,
        due_at=datetime.now(timezone.utc) + timedelta(days=1),
        tags=["work", "urgent"],
        created_at=datetime.now(timezone.utc),
    )


def test_do_selector_output_valid_format(sample_task):
    """Test that valid DoSelectorOutput passes validation."""
    output = DoSelectorOutput(
        task_id=sample_task.id,
        reason_codes=["priority_high", "deadline_soon"],
        alt_task_ids=[],
    )

    assert output.task_id == sample_task.id
    assert len(output.reason_codes) == 2
    assert len(output.alt_task_ids) == 0


def test_do_selector_output_requires_task_id():
    """Test that task_id is required and not empty."""
    with pytest.raises(ValueError):
        DoSelectorOutput(
            task_id="",
            reason_codes=[],
            alt_task_ids=[],
        )


def test_do_selector_output_reason_codes_capped():
    """Test that reason_codes is capped at 3 items."""
    with pytest.raises(ValueError):
        DoSelectorOutput(
            task_id="task-1",
            reason_codes=["a", "b", "c", "d"],  # 4 codes, too many
            alt_task_ids=[],
        )


def test_do_selector_output_alt_task_ids_capped():
    """Test that alt_task_ids is capped at 2 items."""
    with pytest.raises(ValueError):
        DoSelectorOutput(
            task_id="task-1",
            reason_codes=["priority_high"],
            alt_task_ids=["task-2", "task-3", "task-4"],  # 3 alts, too many
        )


def test_validate_filters_invalid_alt_task_ids(sample_task):
    """Test that validation filters out alt_task_ids not in candidates."""
    candidates = [sample_task]

    raw_output = {
        "task_id": sample_task.id,
        "reason_codes": ["test"],
        "alt_task_ids": ["task-valid-but-not-in-candidates"],
    }

    result, is_valid = validate_do_selector_output(raw_output, candidates)

    # Should filter out invalid alt_task_ids
    assert result.alt_task_ids == []
    assert result.task_id == sample_task.id


def test_validate_rejects_task_id_not_in_candidates(sample_task):
    """Test that validation rejects task_id not in candidates."""
    candidates = [sample_task]

    raw_output = {
        "task_id": "task-not-in-list",
        "reason_codes": ["test"],
        "alt_task_ids": [],
    }

    result, is_valid = validate_do_selector_output(raw_output, candidates)

    # Should fallback and mark as invalid
    assert is_valid is False
    assert result.task_id in [c.id for c in candidates]


def test_validate_handles_missing_fields(sample_task):
    """Test that validation handles missing or malformed fields."""
    candidates = [sample_task]

    # Missing reason_codes
    raw_output = {
        "task_id": sample_task.id,
        "alt_task_ids": [],
    }

    result, is_valid = validate_do_selector_output(raw_output, candidates)

    # Should create default reason_codes
    assert result.task_id == sample_task.id
    assert isinstance(result.reason_codes, list)


def test_constraints_validate_energy_range():
    """Test that constraints validate energy level 1-10."""
    # Valid
    constraints = SelectionConstraints(current_energy=5)
    assert constraints.current_energy == 5

    # Invalid (too low)
    with pytest.raises(ValueError):
        SelectionConstraints(current_energy=0)

    # Invalid (too high)
    with pytest.raises(ValueError):
        SelectionConstraints(current_energy=11)


def test_constraints_validate_max_minutes_range():
    """Test that constraints validate max_minutes is 5-1440."""
    # Valid
    constraints = SelectionConstraints(max_minutes=120)
    assert constraints.max_minutes == 120

    # Invalid (too low)
    with pytest.raises(ValueError):
        SelectionConstraints(max_minutes=2)

    # Invalid (too high)
    with pytest.raises(ValueError):
        SelectionConstraints(max_minutes=2000)


def test_constraints_validate_mode():
    """Test that mode is one of allowed values."""
    # Valid modes should not raise
    for mode in ["focus", "quick", "learning", "balanced"]:
        constraints = SelectionConstraints(mode=mode)
        assert constraints.mode == mode


def test_task_candidate_requires_title():
    """Test that TaskCandidate requires a non-empty title."""
    with pytest.raises(ValueError):
        TaskCandidate(
            id="task-1",
            title="",  # Empty
            priority="high",
        )


def test_task_candidate_title_max_length():
    """Test that TaskCandidate title has max length."""
    with pytest.raises(ValueError):
        TaskCandidate(
            id="task-1",
            title="x" * 501,  # Over 500 chars
            priority="high",
        )


def test_task_candidate_estimated_duration_bounds():
    """Test that estimated_duration is between 1-1440 minutes."""
    # Valid
    task = TaskCandidate(
        id="task-1",
        title="Test",
        estimated_duration=60,
    )
    assert task.estimated_duration == 60

    # Invalid (0 minutes)
    with pytest.raises(ValueError):
        TaskCandidate(
            id="task-1",
            title="Test",
            estimated_duration=0,
        )

    # Invalid (over 1440 minutes / 24 hours)
    with pytest.raises(ValueError):
        TaskCandidate(
            id="task-1",
            title="Test",
            estimated_duration=2000,
        )
