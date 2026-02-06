"""
Test Opik evaluators.

Tests for quality evaluation of agent outputs and decisions.
"""

import pytest
from opik_utils.evaluators import (
    HallucinationEvaluator,
    MotivationRubricEvaluator,
    SelectionAccuracyEvaluator,
    StuckDetectionEvaluator,
    EvaluationScore,
)


@pytest.mark.unit
@pytest.mark.agent
class TestHallucinationEvaluator:
    """Tests for HallucinationEvaluator."""

    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = HallucinationEvaluator()

        assert evaluator.name == "hallucination_evaluator"
        assert "hallucination" in evaluator.description.lower()

    def test_detect_no_hallucinations(self):
        """Test detecting no hallucinations in truthful output."""
        evaluator = HallucinationEvaluator()
        output = "The task is called Task 1 with priority high."

        score = evaluator.evaluate(output)

        assert isinstance(score, EvaluationScore)
        assert score.score > 0.8  # High score = no hallucinations
        assert "factually" in score.reasoning.lower() or "hallucination" in score.reasoning.lower()

    def test_detect_hallucinations(self):
        """Test detecting hallucinations in output."""
        evaluator = HallucinationEvaluator()
        output = "I created a task that doesn't exist in your system."

        score = evaluator.evaluate(output)

        assert score.score < 0.8  # Lower score = hallucination detected

    def test_evaluate_empty_output(self):
        """Test evaluating empty output."""
        evaluator = HallucinationEvaluator()

        score = evaluator.evaluate("")

        assert isinstance(score, EvaluationScore)

    def test_evaluate_with_ground_truth(self):
        """Test evaluation with ground truth reference."""
        evaluator = HallucinationEvaluator()
        output = "The task is Task 1 with high priority"
        ground_truth = "Task 1 is high priority"

        score = evaluator.evaluate(output, ground_truth=ground_truth)

        assert isinstance(score, EvaluationScore)

    def test_evaluate_with_context(self):
        """Test evaluation with context."""
        evaluator = HallucinationEvaluator()
        output = "I found no tasks available"
        context = {"task_candidates": [{"id": 1}, {"id": 2}]}

        score = evaluator.evaluate(output, context=context)

        # Should flag as hallucination (claims no tasks when tasks exist)
        assert score.score <= 0.8


@pytest.mark.unit
@pytest.mark.agent
class TestMotivationRubricEvaluator:
    """Tests for MotivationRubricEvaluator."""

    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = MotivationRubricEvaluator()

        assert evaluator.name == "motivation_rubric"

    def test_evaluate_good_motivation(self):
        """Test evaluating high-quality motivation message."""
        evaluator = MotivationRubricEvaluator()
        message = "I understand you're feeling tired. Let's break this down into smaller steps. You've got this!"

        score = evaluator.evaluate(message)

        assert isinstance(score, EvaluationScore)
        assert score.score > 0.5  # Good motivation

    def test_evaluate_poor_motivation(self):
        """Test evaluating poor motivation message."""
        evaluator = MotivationRubricEvaluator()
        message = "Do your task."

        score = evaluator.evaluate(message)

        assert score.score < 0.6  # Poor motivation

    def test_evaluate_with_context(self):
        """Test motivation evaluation with context."""
        evaluator = MotivationRubricEvaluator()
        message = "You're feeling stuck. Let's try this smaller version first!"
        context = {
            "event_type": "stuck",
            "user_mood": "frustrated",
            "task_title": "Complete report",
        }

        score = evaluator.evaluate(message, context=context)

        assert isinstance(score, EvaluationScore)
        assert "empathy_score" in score.metadata or "actionability_score" in score.metadata or len(score.metadata) > 0

    def test_motivation_has_dimensions(self):
        """Test motivation score includes all dimensions."""
        evaluator = MotivationRubricEvaluator()
        message = "You understand this is tough. First step: break it down. You can do it!"

        score = evaluator.evaluate(message)

        assert "empathy_score" in score.metadata
        assert "actionability_score" in score.metadata
        assert "personalization_score" in score.metadata
        assert "tone_score" in score.metadata


@pytest.mark.unit
@pytest.mark.agent
class TestSelectionAccuracyEvaluator:
    """Tests for SelectionAccuracyEvaluator."""

    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = SelectionAccuracyEvaluator()

        assert evaluator.name == "selection_accuracy"

    def test_evaluate_valid_selection(self):
        """Test evaluating valid task selection."""
        evaluator = SelectionAccuracyEvaluator()
        output = {
            "task_id": "task-1",
            "reason_codes": ["high_priority", "time_available"],
            "alt_task_ids": ["task-2", "task-3"]
        }
        context = {
            "candidates": [
                {"id": "task-1", "priority": "high", "status": "todo"},
                {"id": "task-2", "priority": "low", "status": "todo"},
            ],
            "constraints": {"max_minutes": 120, "prefer_priority": "high"}
        }

        score = evaluator.evaluate(output, context=context)

        assert isinstance(score, EvaluationScore)
        assert score.score >= 0.5

    def test_evaluate_constraint_violation(self):
        """Test evaluating selection that violates constraints."""
        evaluator = SelectionAccuracyEvaluator()
        output = {
            "task_id": "task-long",
            "reason_codes": ["fallback"],
            "alt_task_ids": []
        }
        context = {
            "candidates": [
                {"id": "task-long", "priority": "low", "estimated_duration": 500},
            ],
            "constraints": {"max_minutes": 60}
        }

        score = evaluator.evaluate(output, context=context)

        # Should have lower score due to constraint violation
        assert score.score < 0.7

    def test_selection_has_dimension_scores(self):
        """Test selection score includes dimension metrics."""
        evaluator = SelectionAccuracyEvaluator()
        output = {
            "task_id": "task-1",
            "reason_codes": ["optimal"],
            "alt_task_ids": ["task-2"]
        }
        context = {
            "candidates": [
                {"id": "task-1", "priority": "high", "status": "todo"}
            ],
            "constraints": {"max_minutes": 120}
        }

        score = evaluator.evaluate(output, context=context)

        assert "constraint_satisfaction" in score.metadata
        assert "priority_alignment" in score.metadata


@pytest.mark.unit
@pytest.mark.agent
class TestStuckDetectionEvaluator:
    """Tests for StuckDetectionEvaluator."""

    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = StuckDetectionEvaluator()

        assert evaluator.name == "stuck_detection"

    def test_evaluate_correct_stuck_detection(self):
        """Test evaluating correct stuck detection."""
        evaluator = StuckDetectionEvaluator()
        output = {
            "is_stuck": True,
            "patterns": ["time_exceeded", "no_progress"],
            "microtasks": [
                {"action": "take_break", "duration": 10},
                {"action": "scale_down", "new_duration": 15}
            ]
        }
        context = {
            "time_stuck": 120,
            "task_switches": 3,
            "user_mood": "frustrated"
        }

        score = evaluator.evaluate(output, context=context)

        assert isinstance(score, EvaluationScore)
        assert score.score > 0.5  # Reasonable detection

    def test_evaluate_stuck_detection_with_interventions(self):
        """Test evaluating stuck detection with interventions."""
        evaluator = StuckDetectionEvaluator()
        output = {
            "is_stuck": True,
            "patterns": ["decision_paralysis"],
            "microtasks": [
                {"action": "pick_option", "options": ["A", "B", "C"]},
                {"action": "timer", "minutes": 5}
            ]
        }

        score = evaluator.evaluate(output, context={})

        assert isinstance(score, EvaluationScore)
        assert len(score.metadata) > 0  # Has metadata

    def test_stuck_detection_no_interventions_penalty(self):
        """Test that no interventions result in lower score."""
        evaluator = StuckDetectionEvaluator()
        output = {
            "is_stuck": True,
            "patterns": ["stuck"],
            "microtasks": []  # No interventions
        }

        score = evaluator.evaluate(output, context={})

        assert score.score < 0.7  # Lower score without interventions


@pytest.mark.unit
@pytest.mark.agent
class TestEvaluatorConsistency:
    """Tests for evaluator consistency and reliability."""

    def test_evaluator_produces_score_object(self):
        """Test all evaluators produce EvaluationScore."""
        evaluators = [
            HallucinationEvaluator(),
            MotivationRubricEvaluator(),
            SelectionAccuracyEvaluator(),
            StuckDetectionEvaluator(),
        ]

        output = "test output"

        for evaluator in evaluators:
            score = evaluator.evaluate(output)
            assert isinstance(score, EvaluationScore)
            assert 0 <= score.score <= 1
            assert isinstance(score.reasoning, str)
            assert isinstance(score.metadata, dict)

    def test_score_object_serialization(self):
        """Test EvaluationScore can be serialized."""
        score = EvaluationScore(
            score=0.85,
            reasoning="Good output",
            metadata={"dimension": "test"}
        )

        # Convert to dict
        score_dict = score.model_dump()

        assert score_dict["score"] == 0.85
        assert score_dict["reasoning"] == "Good output"

        # Convert to JSON
        json_str = score.model_dump_json()
        assert "0.85" in json_str
