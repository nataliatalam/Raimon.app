"""
Opik custom evaluators for Raimon observability.

Provides specialized evaluators for assessing quality across multiple dimensions:
- Hallucination detection: Checks for false/unfounded information in LLM outputs
- Motivation quality: Assesses empathy, actionability, and personalization
- Selection accuracy: Validates task selection against constraints and priorities
- Stuck detection: Identifies stuck states and evaluates intervention quality
"""

from opik_utils.evaluators.base import BaseEvaluator, EvaluationScore
from opik_utils.evaluators.hallucination_evaluator import HallucinationEvaluator
from opik_utils.evaluators.motivation_rubric import MotivationRubricEvaluator
from opik_utils.evaluators.selection_accuracy import SelectionAccuracyEvaluator
from opik_utils.evaluators.stuck_detection import StuckDetectionEvaluator

__all__ = [
    "BaseEvaluator",
    "EvaluationScore",
    "HallucinationEvaluator",
    "MotivationRubricEvaluator",
    "SelectionAccuracyEvaluator",
    "StuckDetectionEvaluator",
]
