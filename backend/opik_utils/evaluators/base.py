"""
Base evaluator abstract class for Opik custom evaluators.

Defines the interface that all custom evaluators must implement for quality assessment
of agent outputs and orchestrator decisions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EvaluationScore(BaseModel):
    """
    Standard evaluation score output.

    Attributes:
        score: Numeric score (typically 0-1 or 0-100 scale)
        reasoning: Human-readable explanation of the score
        metadata: Additional evaluation-specific data
    """

    score: float = Field(..., description="Evaluation score")
    reasoning: str = Field(..., description="Explanation of the score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional evaluation metadata"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="When evaluation was performed"
    )

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class BaseEvaluator(ABC):
    """
    Abstract base class for all Opik evaluators.

    Custom evaluators should inherit from this class and implement the evaluate() method.
    Each evaluator focuses on a specific quality dimension of agent outputs.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize the evaluator.

        Args:
            name: Evaluator name (e.g., "hallucination_evaluator")
            description: Human-readable description of what this evaluator measures
        """
        self.name = name
        self.description = description

    @abstractmethod
    def evaluate(
        self,
        output: Any,
        ground_truth: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationScore:
        """
        Evaluate the quality of an output.

        Args:
            output: The output to evaluate (agent response, decision, etc.)
            ground_truth: Optional reference output for comparison
            context: Optional additional context for evaluation

        Returns:
            EvaluationScore with numeric score and reasoning
        """
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.name})"

    def validate_output(self, output: Any) -> bool:
        """
        Validate that the output is in the expected format.

        Subclasses can override to implement custom validation.

        Args:
            output: The output to validate

        Returns:
            True if valid, False otherwise
        """
        return output is not None

    def preprocess_output(self, output: Any) -> Any:
        """
        Preprocess the output before evaluation.

        Subclasses can override for custom preprocessing.

        Args:
            output: Raw output

        Returns:
            Preprocessed output
        """
        return output

    def postprocess_score(self, score: EvaluationScore) -> EvaluationScore:
        """
        Postprocess the evaluation score.

        Subclasses can override for custom postprocessing.

        Args:
            score: Raw evaluation score

        Returns:
            Postprocessed score
        """
        return score
