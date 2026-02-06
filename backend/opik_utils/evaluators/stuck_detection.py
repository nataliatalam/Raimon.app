"""
Stuck pattern detection evaluator.

Evaluates the accuracy of the stuck pattern detector in identifying when users
are stuck and the quality of suggested interventions (microtasks).
"""

from typing import Dict, Any, Optional, List
from opik_utils.evaluators.base import BaseEvaluator, EvaluationScore


class StuckDetectionEvaluator(BaseEvaluator):
    """
    Evaluates stuck pattern detection and intervention quality.

    Dimensions:
    - Detection Accuracy: Does the system correctly identify stuck states?
    - Pattern Recognition: Are the identified patterns legitimate?
    - Intervention Quality: Are suggested microtasks helpful?
    - Interventions Diversity: Are there varied intervention options?
    - Feasibility: Can user realistically complete suggested tasks?

    Scoring:
    - 1.0: Accurate detection, high-quality diverse interventions
    - 0.75: Good detection with decent interventions
    - 0.5: Moderate detection accuracy, fair interventions
    - 0.25: Poor detection or weak interventions
    - 0.0: False positive or harmful interventions
    """

    def __init__(self):
        """Initialize the stuck detection evaluator."""
        super().__init__(
            name="stuck_detection",
            description="Evaluates stuck pattern detection and intervention quality"
        )

        # Stuck indicators
        self.stuck_patterns = [
            "no_progress",
            "repeated_task_switches",
            "time_exceeded",
            "same_task_repeated",
            "low_motivation",
            "decision_paralysis",
            "environment_block",
        ]

    def evaluate(
        self,
        output: Any,
        ground_truth: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationScore:
        """
        Evaluate stuck detection accuracy and intervention quality.

        Args:
            output: Detection output with is_stuck, patterns, microtasks
            ground_truth: Optional reference (did user actually get unstuck?)
            context: Session context (time_stuck, task history, etc.)

        Returns:
            EvaluationScore with detection and intervention assessment
        """
        if not self.validate_output(output):
            return EvaluationScore(
                score=0.0,
                reasoning="Detection output invalid or missing",
                metadata={"error": "invalid_format"}
            )

        output = self.preprocess_output(output)

        # Extract detection details
        is_stuck = output.get("is_stuck") if isinstance(output, dict) else getattr(output, "is_stuck", False)
        patterns = output.get("patterns", []) if isinstance(output, dict) else getattr(output, "patterns", [])
        microtasks = output.get("microtasks", []) if isinstance(output, dict) else getattr(output, "microtasks", [])

        if not context:
            return EvaluationScore(
                score=0.5,
                reasoning="Detection valid but cannot assess accuracy without context",
                metadata={"is_stuck_detected": is_stuck}
            )

        # Evaluate each dimension
        detection_score = self._evaluate_detection_accuracy(is_stuck, patterns, context, ground_truth)
        pattern_score = self._evaluate_pattern_quality(patterns)
        intervention_score = self._evaluate_intervention_quality(microtasks, context)
        diversity_score = self._evaluate_intervention_diversity(microtasks, context)
        feasibility_score = self._evaluate_feasibility(microtasks, context)

        # Weighted average
        weights = {
            "detection": 0.30,
            "patterns": 0.20,
            "interventions": 0.25,
            "diversity": 0.15,
            "feasibility": 0.10,
        }

        final_score = (
            detection_score * weights["detection"]
            + pattern_score * weights["patterns"]
            + intervention_score * weights["interventions"]
            + diversity_score * weights["diversity"]
            + feasibility_score * weights["feasibility"]
        )

        reasoning = self._generate_reasoning(
            detection_score,
            pattern_score,
            intervention_score,
            diversity_score,
            feasibility_score,
            is_stuck
        )

        metadata = {
            "is_stuck_detected": is_stuck,
            "detection_accuracy": round(detection_score, 2),
            "pattern_quality": round(pattern_score, 2),
            "intervention_quality": round(intervention_score, 2),
            "diversity": round(diversity_score, 2),
            "feasibility": round(feasibility_score, 2),
            "patterns_count": len(patterns) if patterns else 0,
            "microtasks_count": len(microtasks) if microtasks else 0,
        }

        score = EvaluationScore(
            score=round(final_score, 2),
            reasoning=reasoning,
            metadata=metadata
        )

        return self.postprocess_score(score)

    def _evaluate_detection_accuracy(
        self,
        is_stuck: bool,
        patterns: List[str],
        context: Dict[str, Any],
        ground_truth: Optional[Any]
    ) -> float:
        """
        Evaluate if the stuck detection is accurate.

        Returns:
            Score 0-1 where 1 = accurate detection
        """
        # Calculate likelihood of being stuck from context
        likelihood = self._calculate_stuck_likelihood(context)

        # If ground truth provided, use it
        if ground_truth is not None:
            user_actually_stuck = ground_truth.get("is_stuck", False) if isinstance(ground_truth, dict) else bool(ground_truth)
            if is_stuck == user_actually_stuck:
                return 1.0
            else:
                return 0.2  # Wrong detection

        # Without ground truth, evaluate detection reasonableness
        if is_stuck and likelihood > 0.6:
            return 0.8  # Reasonable detection
        elif not is_stuck and likelihood < 0.4:
            return 0.8  # Reasonable non-detection
        elif is_stuck and likelihood > 0.3:
            return 0.6  # Plausible detection
        elif not is_stuck and likelihood > 0.3:
            return 0.4  # Questionable non-detection
        else:
            return 0.3

    def _calculate_stuck_likelihood(self, context: Dict[str, Any]) -> float:
        """
        Calculate likelihood user is stuck based on context.

        Returns:
            Score 0-1 where 1 = definitely stuck
        """
        likelihood = 0.0

        # Time indicators
        time_stuck = context.get("time_stuck", 0)
        if time_stuck > 60:  # More than 1 hour
            likelihood += 0.3
        elif time_stuck > 30:
            likelihood += 0.15

        # Task switch indicators
        task_switches = context.get("task_switches", 0)
        if task_switches > 5:
            likelihood += 0.2
        elif task_switches > 2:
            likelihood += 0.1

        # User state indicators
        if context.get("user_mood") in ["frustrated", "tired", "stuck"]:
            likelihood += 0.2

        if context.get("energy_level", 5) < 3:
            likelihood += 0.15

        # Session indicators
        if context.get("incomplete_tasks", 0) > 3:
            likelihood += 0.15

        # Recent interruptions
        if context.get("interruptions", 0) > 2:
            likelihood += 0.1

        return min(1.0, likelihood)

    def _evaluate_pattern_quality(self, patterns: List[str]) -> float:
        """Evaluate quality of identified patterns."""
        if not patterns:
            return 0.3  # No patterns identified = weak

        score = 0.0
        valid_patterns = 0

        for pattern in patterns:
            if pattern in self.stuck_patterns:
                valid_patterns += 1
                score += 0.7
            else:
                # Unknown pattern - check if it's reasonable
                if any(
                    keyword in pattern.lower()
                    for keyword in ["no", "stuck", "repeat", "block", "time", "progress"]
                ):
                    score += 0.4
                else:
                    score += 0.1

        avg_pattern_score = score / max(len(patterns), 1)
        return min(1.0, avg_pattern_score)

    def _evaluate_intervention_quality(self, microtasks: List[Any], context: Dict[str, Any]) -> float:
        """Evaluate quality of suggested interventions."""
        if not microtasks or len(microtasks) == 0:
            return 0.0  # No interventions = critical failure

        if len(microtasks) > 10:
            return 0.3  # Too many suggestions = overwhelming

        score = 0.0

        for task in microtasks:
            task_dict = task if isinstance(task, dict) else task.__dict__ if hasattr(task, "__dict__") else {}

            # Check if task has clear action/description
            if "action" in task_dict or "description" in task_dict or "title" in task_dict:
                score += 0.15
            else:
                score -= 0.05

            # Check if task is achievable (should be small)
            duration = task_dict.get("estimated_duration", 15)
            if int(duration) <= 15:
                score += 0.2
            elif int(duration) <= 30:
                score += 0.1
            else:
                score -= 0.1

            # Check if task relates to stuck pattern
            if "relates_to_pattern" in task_dict:
                score += 0.15

        avg_score = score / len(microtasks)
        return max(0.0, min(1.0, avg_score))

    def _evaluate_intervention_diversity(self, microtasks: List[Any], context: Dict[str, Any]) -> float:
        """Evaluate diversity of intervention approaches."""
        if not microtasks or len(microtasks) < 2:
            return 0.3  # Single or no intervention = low diversity

        categories = set()

        for task in microtasks:
            task_dict = task if isinstance(task, dict) else task.__dict__ if hasattr(task, "__dict__") else {}
            category = task_dict.get("category", "general")
            categories.add(category)

        diversity = len(categories) / max(len(microtasks), 1)

        # If we have 3+ different types of interventions for 3+ tasks = good diversity
        if len(microtasks) >= 3 and len(categories) >= 2:
            return min(1.0, diversity + 0.3)
        elif len(categories) >= 2:
            return min(1.0, diversity + 0.1)
        else:
            return diversity

    def _evaluate_feasibility(self, microtasks: List[Any], context: Dict[str, Any]) -> float:
        """Evaluate if user can realistically complete the interventions."""
        if not microtasks:
            return 0.5

        user_energy = context.get("energy_level", 5)
        available_time = context.get("time_available", 60)

        total_duration = 0
        feasible_count = 0

        for task in microtasks:
            task_dict = task if isinstance(task, dict) else task.__dict__ if hasattr(task, "__dict__") else {}
            duration = int(task_dict.get("estimated_duration", 15))
            total_duration += duration

            # Check if task is feasible given user state
            if user_energy < 3 and duration > 10:
                # Too demanding for low energy
                pass
            elif user_energy >= 3 or duration <= 10:
                # Feasible
                feasible_count += 1

        # Check if total duration is reasonable
        score = feasible_count / max(len(microtasks), 1)

        if total_duration > available_time:
            score *= 0.7

        return min(1.0, score)

    def _generate_reasoning(
        self,
        detection: float,
        patterns: float,
        interventions: float,
        diversity: float,
        feasibility: float,
        is_stuck: bool
    ) -> str:
        """Generate human-readable feedback."""
        feedback = []

        if is_stuck:
            if detection >= 0.8:
                feedback.append("Correctly identified stuck state")
            elif detection >= 0.5:
                feedback.append("Likely stuck state detection")
            else:
                feedback.append("Stuck detection may be incorrect")
        else:
            if detection >= 0.8:
                feedback.append("Correctly determined user not stuck")
            else:
                feedback.append("No stuck state detected")

        if patterns >= 0.8:
            feedback.append("Clear, valid stuck patterns identified")
        elif patterns >= 0.5:
            feedback.append("Some valid patterns identified")
        else:
            feedback.append("Pattern identification needs improvement")

        if interventions >= 0.7:
            feedback.append("High-quality interventions provided")
        elif interventions >= 0.4:
            feedback.append("Reasonable interventions suggested")
        else:
            feedback.append("Interventions need improvement")

        if diversity >= 0.7:
            feedback.append("Good diversity in intervention approaches")

        if feasibility >= 0.7:
            feedback.append("Interventions are feasible for user")
        elif feasibility >= 0.5:
            feedback.append("Some interventions may be too demanding")

        return ". ".join(feedback) + "."
