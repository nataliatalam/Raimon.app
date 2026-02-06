"""
Task selection accuracy evaluator.

Evaluates how well the LLM-based task selector performs compared to deterministic
selection and validates that selected tasks match the given constraints.
"""

from typing import Dict, Any, Optional, List
from opik_utils.evaluators.base import BaseEvaluator, EvaluationScore


class SelectionAccuracyEvaluator(BaseEvaluator):
    """
    Evaluates task selection accuracy across multiple dimensions.

    Dimensions:
    - Constraint Satisfaction: Does selected task respect energy/time constraints?
    - Priority Alignment: Is the selected task aligned with user priorities?
    - Optimal Match: Is this likely the best task for the current context?
    - Alternative Quality: Are the alternatives well-reasoned?
    - Consistency: Does the selection match the given reasoning codes?

    Scoring:
    - 1.0: Perfect selection - optimal task, satisfies all constraints
    - 0.75: Good selection - appropriate task, minor issues
    - 0.5: Fair selection - acceptable but not optimal
    - 0.25: Poor selection - ignores constraints or priorities
    - 0.0: Invalid selection - violates constraints
    """

    def __init__(self):
        """Initialize the selection accuracy evaluator."""
        super().__init__(
            name="selection_accuracy",
            description="Evaluates task selection accuracy and constraint satisfaction"
        )

    def evaluate(
        self,
        output: Any,
        ground_truth: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationScore:
        """
        Evaluate selection accuracy.

        Args:
            output: Selection output with task_id, reason_codes, alternatives
            ground_truth: Optional reference selection for comparison
            context: Selection context (constraints, candidates, user state)

        Returns:
            EvaluationScore with accuracy assessment
        """
        if not self.validate_output(output):
            return EvaluationScore(
                score=0.0,
                reasoning="Selection output invalid or missing required fields",
                metadata={"error": "invalid_format"}
            )

        output = self.preprocess_output(output)

        if not context:
            # Without context, can only check output validity
            return EvaluationScore(
                score=0.5,
                reasoning="Selection valid but cannot assess accuracy without context",
                metadata={"has_context": False}
            )

        # Extract selection details
        selected_task_id = output.get("task_id") if isinstance(output, dict) else getattr(output, "task_id", None)
        reason_codes = output.get("reason_codes", []) if isinstance(output, dict) else getattr(output, "reason_codes", [])
        alternatives = output.get("alt_task_ids", []) if isinstance(output, dict) else getattr(output, "alt_task_ids", [])

        if not selected_task_id:
            return EvaluationScore(
                score=0.0,
                reasoning="No task selected or task_id missing",
                metadata={"error": "no_selection"}
            )

        # Evaluate each dimension
        constraint_score = self._evaluate_constraint_satisfaction(selected_task_id, context)
        priority_score = self._evaluate_priority_alignment(selected_task_id, context)
        optimal_score = self._evaluate_optimality(selected_task_id, context)
        alternative_score = self._evaluate_alternative_quality(selected_task_id, alternatives, context)
        consistency_score = self._evaluate_consistency(selected_task_id, reason_codes, context)

        # Weighted average (constraint satisfaction is critical)
        weights = {
            "constraints": 0.35,
            "priority": 0.25,
            "optimality": 0.20,
            "alternatives": 0.10,
            "consistency": 0.10,
        }

        final_score = (
            constraint_score * weights["constraints"]
            + priority_score * weights["priority"]
            + optimal_score * weights["optimality"]
            + alternative_score * weights["alternatives"]
            + consistency_score * weights["consistency"]
        )

        # If constraints are violated, significantly penalize
        if constraint_score < 0.5:
            final_score *= 0.7

        reasoning = self._generate_reasoning(
            constraint_score,
            priority_score,
            optimal_score,
            alternative_score,
            consistency_score
        )

        metadata = {
            "selected_task_id": str(selected_task_id),
            "constraint_satisfaction": round(constraint_score, 2),
            "priority_alignment": round(priority_score, 2),
            "optimality": round(optimal_score, 2),
            "alternative_quality": round(alternative_score, 2),
            "consistency": round(consistency_score, 2),
            "reason_codes": reason_codes,
            "alternatives_count": len(alternatives) if alternatives else 0,
        }

        score = EvaluationScore(
            score=round(final_score, 2),
            reasoning=reasoning,
            metadata=metadata
        )

        return self.postprocess_score(score)

    def _evaluate_constraint_satisfaction(self, task_id: str, context: Dict[str, Any]) -> float:
        """
        Evaluate if selected task satisfies constraints.

        Critical dimension: violating constraints = automatic failure.
        """
        candidates = context.get("candidates", [])
        constraints = context.get("constraints", {})

        # Find the selected task
        selected_task = None
        for task in candidates:
            if str(task.get("id")) == str(task_id):
                selected_task = task
                break

        if not selected_task:
            return 0.0  # Task not in candidates = invalid selection

        score = 1.0

        # Check time constraint
        if "max_minutes" in constraints:
            max_minutes = constraints["max_minutes"]
            task_duration = selected_task.get("estimated_duration", 0)
            if task_duration and int(task_duration) > int(max_minutes):
                score *= 0.5  # Violates time constraint

        # Check energy constraint
        if "current_energy" in constraints:
            current_energy = constraints["current_energy"]
            task_difficulty = self._estimate_task_difficulty(selected_task)
            if current_energy < 4 and task_difficulty > 7:
                score *= 0.6  # High difficulty task for low energy

        # Check status constraint (should avoid already completed)
        if selected_task.get("status") == "done":
            score *= 0.7

        # Check priority alignment (if prefer_priority specified)
        if "prefer_priority" in constraints and constraints["prefer_priority"]:
            if selected_task.get("priority") == constraints["prefer_priority"]:
                score = min(1.0, score + 0.1)

        return max(0.0, score)

    def _evaluate_priority_alignment(self, task_id: str, context: Dict[str, Any]) -> float:
        """Evaluate if selection aligns with user priorities."""
        candidates = context.get("candidates", [])
        user_profile = context.get("user_profile", {})

        # Find selected task
        selected_task = next(
            (t for t in candidates if str(t.get("id")) == str(task_id)),
            None
        )

        if not selected_task:
            return 0.0

        score = 0.5  # Start neutral

        # Check if task matches focus areas/priorities
        if "focus_areas" in user_profile:
            focus_areas = user_profile.get("focus_areas", [])
            task_tags = selected_task.get("tags", [])
            if any(tag in focus_areas for tag in task_tags):
                score += 0.3

        # Check priority level
        task_priority = selected_task.get("priority", "medium")
        if task_priority == "high":
            score += 0.15

        # Check if overdue (should prioritize)
        if selected_task.get("overdue"):
            score += 0.2

        return min(1.0, score)

    def _evaluate_optimality(self, task_id: str, context: Dict[str, Any]) -> float:
        """Evaluate if this is likely the optimal task given context."""
        candidates = context.get("candidates", [])

        if not candidates or len(candidates) < 2:
            return 0.8  # Only one choice = decent

        # Find selected task
        selected_task = next(
            (t for t in candidates if str(t.get("id")) == str(task_id)),
            None
        )

        if not selected_task:
            return 0.0

        # Score the selected task
        selected_score = self._calculate_task_fitness(selected_task, context)

        # Compare with top 3 alternatives
        all_scores = [
            (t, self._calculate_task_fitness(t, context))
            for t in candidates
        ]
        all_scores.sort(key=lambda x: x[1], reverse=True)
        top_scores = [s for _, s in all_scores[:3]]

        if not top_scores:
            return 0.5

        # Selected is in top N if within 10% of best
        best_score = top_scores[0]
        if selected_score >= best_score * 0.9:
            return 1.0
        elif selected_score >= best_score * 0.75:
            return 0.8
        elif selected_score >= best_score * 0.6:
            return 0.6
        else:
            return 0.3

    def _evaluate_alternative_quality(
        self,
        task_id: str,
        alternatives: List[str],
        context: Dict[str, Any]
    ) -> float:
        """Evaluate quality of provided alternatives."""
        if not alternatives or len(alternatives) == 0:
            return 0.5  # No alternatives = neutral

        candidates = context.get("candidates", [])
        constraints = context.get("constraints", {})

        score = 0.5  # Start neutral
        valid_alternatives = 0

        for alt_id in alternatives[:3]:  # Check top 3 alternatives
            alt_task = next(
                (t for t in candidates if str(t.get("id")) == str(alt_id)),
                None
            )
            if alt_task:
                # Check if alternative satisfies constraints
                if self._task_satisfies_constraints(alt_task, constraints):
                    valid_alternatives += 1

        # Good alternatives if most are valid and diverse
        if len(alternatives) >= 2 and valid_alternatives >= len(alternatives) - 1:
            score = 0.9
        elif valid_alternatives >= 1:
            score = 0.7
        else:
            score = 0.4

        return score

    def _evaluate_consistency(
        self,
        task_id: str,
        reason_codes: List[str],
        context: Dict[str, Any]
    ) -> float:
        """Evaluate if reason codes match the selection."""
        if not reason_codes:
            return 0.5  # No reasoning provided = neutral

        valid_codes = [
            "highest_priority",
            "time_available",
            "user_goal",
            "lowest_effort",
            "deadline_urgent",
            "focus_area_match",
            "fallback_best_overall",
        ]

        # Check that provided codes are valid
        score = 0.0
        for code in reason_codes:
            if code in valid_codes or code.startswith("fallback_"):
                score += 0.5

        return min(1.0, score / max(len(reason_codes), 1))

    def _calculate_task_fitness(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate fitness score for a task given context."""
        score = 0.0

        # Priority weighting
        priority_weight = {"high": 1.0, "medium": 0.6, "low": 0.3}.get(task.get("priority"), 0.5)
        score += priority_weight * 30

        # Duration weighting (shorter = better for low energy)
        duration = task.get("estimated_duration", 60)
        duration_score = max(0, 30 - (int(duration) / 10))
        score += duration_score

        # Status (should not be completed)
        if task.get("status") != "done":
            score += 20
        else:
            score -= 10

        # Due soon bonus
        if task.get("overdue"):
            score += 15

        return max(0, min(100, score))

    def _task_satisfies_constraints(self, task: Dict[str, Any], constraints: Dict[str, Any]) -> bool:
        """Check if task satisfies hard constraints."""
        # Time constraint
        if "max_minutes" in constraints:
            duration = task.get("estimated_duration", 0)
            if duration and int(duration) > int(constraints["max_minutes"]):
                return False

        # Status constraint
        if task.get("status") == "done":
            return False

        return True

    def _estimate_task_difficulty(self, task: Dict[str, Any]) -> float:
        """Estimate task difficulty (0-10 scale)."""
        priority_difficulty = {"high": 8, "medium": 5, "low": 3}.get(task.get("priority"), 5)
        duration = int(task.get("estimated_duration", 60))
        duration_difficulty = min(10, max(1, duration / 30))
        return (priority_difficulty + duration_difficulty) / 2

    def _generate_reasoning(
        self,
        constraint: float,
        priority: float,
        optimal: float,
        alternatives: float,
        consistency: float
    ) -> str:
        """Generate human-readable feedback."""
        feedback = []

        if constraint >= 0.9:
            feedback.append("Excellently satisfies constraints")
        elif constraint >= 0.7:
            feedback.append("Satisfies constraints")
        elif constraint >= 0.5:
            feedback.append("Mostly satisfies constraints")
        else:
            feedback.append("VIOLATES constraints - selection invalid")

        if priority >= 0.8:
            feedback.append("well-aligned with priorities")
        elif priority >= 0.6:
            feedback.append("reasonably aligned with priorities")
        else:
            feedback.append("poorly aligned with priorities")

        if optimal >= 0.9:
            feedback.append("appears optimal for context")
        elif optimal >= 0.7:
            feedback.append("good match for context")
        elif optimal >= 0.5:
            feedback.append("acceptable match for context")
        else:
            feedback.append("suboptimal choice given alternatives")

        if alternatives >= 0.8:
            feedback.append("good alternatives provided")
        elif alternatives < 0.5:
            feedback.append("alternatives need improvement")

        return ". ".join(feedback) + "."
