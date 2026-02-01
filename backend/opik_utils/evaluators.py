"""
Opik evaluators for Raimon agents
Implements hallucination detection, graded rubrics, and quality checks
"""
from opik.evaluation.metrics import Hallucination, ContextPrecision, AnswerRelevance
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class RaimonEvaluator:
    """
    Custom evaluators for Raimon agents

    Usage:
        evaluator = RaimonEvaluator()
        result = evaluator.evaluate_priority_recommendation(
            task_input=task_data,
            agent_output=result,
            user_history=user_task_history
        )

        if not result["is_trustworthy"]:
            logger.warning(f"Hallucination detected: {result}")
    """

    def __init__(self, hallucination_threshold: float = 0.3):
        """
        Initialize evaluators

        Args:
            hallucination_threshold: Score below which output is considered hallucinated
        """
        self.hallucination_detector = Hallucination(threshold=hallucination_threshold)
        self.precision_checker = ContextPrecision()
        self.relevance_checker = AnswerRelevance()

    def evaluate_priority_recommendation(
        self,
        task_input: Dict[str, Any],
        agent_output: Dict[str, Any],
        user_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Checks if priority recommendation is grounded in facts

        Args:
            task_input: Original task data
            agent_output: Agent's recommendation
            user_history: User's task history for context

        Returns:
            Dict with evaluation scores and trustworthiness flag
        """
        try:
            # Convert to strings for evaluation
            input_str = str(task_input)
            output_str = agent_output.get("reasoning", str(agent_output))
            context_str = str(user_history)

            # Check for hallucinations
            hallucination_score = self.hallucination_detector.score(
                input=input_str,
                output=output_str,
                context=context_str
            )

            # Check context usage precision
            precision_score = self.precision_checker.score(
                input=input_str,
                output=output_str,
                context=context_str
            )

            # Check relevance
            relevance_score = self.relevance_checker.score(
                input=input_str,
                output=output_str
            )

            # Determine trustworthiness
            is_trustworthy = (
                hallucination_score < 0.3 and
                precision_score > 0.7 and
                relevance_score > 0.7
            )

            return {
                "hallucination_risk": hallucination_score,
                "context_precision": precision_score,
                "answer_relevance": relevance_score,
                "is_trustworthy": is_trustworthy,
                "recommendation": "accept" if is_trustworthy else "review"
            }

        except Exception as e:
            logger.error(f"Error in evaluation: {e}")
            return {
                "hallucination_risk": 1.0,
                "context_precision": 0.0,
                "answer_relevance": 0.0,
                "is_trustworthy": False,
                "recommendation": "error",
                "error": str(e)
            }

    def evaluate_time_prediction(
        self,
        task_data: Dict[str, Any],
        predicted_duration: int,
        similar_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates time prediction against similar past tasks

        Args:
            task_data: Current task information
            predicted_duration: AI predicted duration (minutes)
            similar_tasks: List of similar completed tasks

        Returns:
            Dict with confidence score and reasoning
        """
        if not similar_tasks:
            return {
                "confidence": 0.5,
                "reasoning": "No similar tasks found for comparison",
                "is_reliable": False
            }

        # Calculate average duration of similar tasks
        similar_durations = [
            t.get("actual_duration", t.get("estimated_duration", 0))
            for t in similar_tasks
        ]
        avg_similar = sum(similar_durations) / len(similar_durations) if similar_durations else 0

        # Calculate deviation
        if avg_similar > 0:
            deviation = abs(predicted_duration - avg_similar) / avg_similar
            confidence = max(0, 1 - deviation)
        else:
            confidence = 0.5

        is_reliable = confidence > 0.7

        return {
            "confidence": round(confidence, 2),
            "predicted_duration": predicted_duration,
            "avg_similar_duration": round(avg_similar, 0),
            "is_reliable": is_reliable,
            "reasoning": f"Based on {len(similar_tasks)} similar tasks (avg: {avg_similar:.0f} min)"
        }


class MotivationRubricEvaluator:
    """
    Graded rubric evaluator for motivation agent messages

    Evaluates messages on:
    - Empathy (0-5): Understanding of user frustration
    - Actionability (0-5): Provides concrete next steps
    - Personalization (0-5): References user-specific context
    """

    RUBRIC = {
        "empathy": {
            "description": "Message shows understanding of user frustration",
            "scale": 5,
            "weight": 0.3,
            "criteria": [
                "Acknowledges user's feelings",
                "Shows understanding of situation",
                "Non-judgmental tone"
            ]
        },
        "actionability": {
            "description": "Provides concrete next steps",
            "scale": 5,
            "weight": 0.5,
            "criteria": [
                "Clear action items",
                "Specific recommendations",
                "Practical advice"
            ]
        },
        "personalization": {
            "description": "References user-specific context",
            "scale": 5,
            "weight": 0.2,
            "criteria": [
                "Uses user's name or data",
                "References past tasks",
                "Context-aware suggestions"
            ]
        }
    }

    def __init__(self):
        self.rubric = self.RUBRIC

    def evaluate_message(
        self,
        message: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate motivation message against rubric

        Args:
            message: The motivation message to evaluate
            user_context: Context about the user

        Returns:
            Dict with scores and overall rating
        """
        scores = {}

        # Simple keyword-based evaluation (in production, use LLM-as-judge)

        # Empathy score
        empathy_keywords = ["understand", "feel", "frustrat", "difficult", "challenging"]
        empathy_count = sum(1 for kw in empathy_keywords if kw in message.lower())
        scores["empathy"] = min(5, empathy_count)

        # Actionability score
        action_keywords = ["try", "can", "start", "next", "step", "do", "complete"]
        action_count = sum(1 for kw in action_keywords if kw in message.lower())
        scores["actionability"] = min(5, action_count)

        # Personalization score
        user_name = user_context.get("name", "")
        has_name = user_name.lower() in message.lower() if user_name else False
        has_context = any(str(v).lower() in message.lower() for v in user_context.values() if v)
        scores["personalization"] = (
            3 if has_name else
            2 if has_context else
            1
        )

        # Calculate weighted overall score
        overall_score = sum(
            scores[criterion] * self.rubric[criterion]["weight"]
            for criterion in scores
        )

        # Convert to 0-1 scale
        overall_score = overall_score / 5

        return {
            "scores": scores,
            "overall_score": round(overall_score, 2),
            "rating": self._get_rating(overall_score),
            "feedback": self._generate_feedback(scores)
        }

    def _get_rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "acceptable"
        else:
            return "needs_improvement"

    def _generate_feedback(self, scores: Dict[str, int]) -> List[str]:
        """Generate improvement feedback"""
        feedback = []

        if scores["empathy"] < 3:
            feedback.append("Add more empathetic language to acknowledge user feelings")

        if scores["actionability"] < 3:
            feedback.append("Include clearer action items and next steps")

        if scores["personalization"] < 2:
            feedback.append("Use more user-specific context in the message")

        return feedback


class StuckPatternEvaluator:
    """
    Evaluator for stuck pattern detection accuracy

    Measures:
    - Detection recall: Did we catch actual stuck states?
    - False positive rate: How often do we incorrectly flag stuck?
    """

    def __init__(self):
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.true_negatives = 0

    def evaluate_detection(
        self,
        ai_detected_stuck: bool,
        user_confirmed_stuck: bool
    ) -> Dict[str, Any]:
        """
        Evaluate a single stuck detection

        Args:
            ai_detected_stuck: Whether AI flagged stuck state
            user_confirmed_stuck: Whether user confirmed being stuck

        Returns:
            Dict with classification result
        """
        if ai_detected_stuck and user_confirmed_stuck:
            self.true_positives += 1
            result = "true_positive"
        elif ai_detected_stuck and not user_confirmed_stuck:
            self.false_positives += 1
            result = "false_positive"
        elif not ai_detected_stuck and user_confirmed_stuck:
            self.false_negatives += 1
            result = "false_negative"
        else:
            self.true_negatives += 1
            result = "true_negative"

        return {
            "result": result,
            "metrics": self.get_metrics()
        }

    def get_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        total = (
            self.true_positives +
            self.false_positives +
            self.false_negatives +
            self.true_negatives
        )

        if total == 0:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "accuracy": 0.0
            }

        precision = (
            self.true_positives / (self.true_positives + self.false_positives)
            if (self.true_positives + self.false_positives) > 0 else 0.0
        )

        recall = (
            self.true_positives / (self.true_positives + self.false_negatives)
            if (self.true_positives + self.false_negatives) > 0 else 0.0
        )

        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )

        accuracy = (
            (self.true_positives + self.true_negatives) / total
        )

        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1_score, 3),
            "accuracy": round(accuracy, 3)
        }

    def reset(self):
        """Reset counters"""
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.true_negatives = 0


# Global instances for easy import
raimon_evaluator = RaimonEvaluator()
motivation_rubric = MotivationRubricEvaluator()
stuck_pattern_eval = StuckPatternEvaluator()
