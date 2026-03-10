from abc import ABC, abstractmethod
from typing import Generic, Optional

from ..core.context import EvaluationContext
from ..core.results import EvaluationResult
from ..core.types import EvaluationStatus, T


class EvaluatorError(Exception):
    """Base exception for evaluator-related errors."""

    pass


class MaxRetriesExceededError(EvaluatorError):
    """Raised when max retries are exceeded."""

    pass


class BaseEvaluator(ABC, Generic[T]):
    """
    Abstract base class for all evaluators in the SwarmTask framework.

    Evaluators are responsible for:
    1. Evaluating results against specific criteria
    2. Generating improvement prompts when evaluation fails
    3. Managing their own retry state
    """

    def __init__(self, max_retries: int = 3, name: Optional[str] = None):
        """
        Initialize the evaluator.

        Args:
            max_retries: Maximum number of retry attempts allowed
            name: Optional name for the evaluator. Defaults to class name if not provided
        """
        self.max_retries = max_retries
        self.name = name or self.__class__.__name__
        self._attempt_count = 0

    @property
    def attempts(self) -> int:
        """Current number of attempts made."""
        return self._attempt_count

    @property
    def attempts_remaining(self) -> int:
        """Number of retry attempts remaining."""
        return max(0, self.max_retries - self._attempt_count)

    @property
    def can_retry(self) -> bool:
        """Whether the evaluator can make another attempt."""
        return self.attempts_remaining > 0

    @abstractmethod
    async def evaluate(
        self, result: T, context: EvaluationContext[T]
    ) -> EvaluationResult:
        """
        Evaluate the result according to the evaluator's criteria.

        Args:
            result: The result to evaluate
            context: Current evaluation context containing history and metadata

        Returns:
            EvaluationResult indicating success/failure and any feedback
        """
        raise NotImplementedError

    @abstractmethod
    async def get_improvement_prompt(
        self,
        result: T,
        evaluation_result: EvaluationResult,
        context: EvaluationContext[T],
    ) -> str:
        """
        Generate a prompt to improve the result based on evaluation feedback.

        Args:
            result: The result that failed evaluation
            evaluation_result: The evaluation result containing failure details
            context: Current evaluation context

        Returns:
            A string prompt suggesting how to improve the result
        """
        raise NotImplementedError

    def create_error_result(self, error: Exception) -> EvaluationResult:
        """
        Create a standardized error result from an exception.
        Commonly used utility for error handling.
        """
        return EvaluationResult(
            status=EvaluationStatus.FAILED,
            success=False,
            message=str(error),
            metadata={"error_type": type(error).__name__, "evaluator": self.name},
        )

    async def evaluate_safely(
        self, result: T, context: EvaluationContext[T]
    ) -> EvaluationResult:
        """
        Safely execute evaluation with retry checking.
        Main utility method for evaluation execution.
        """
        try:
            return await self.evaluate(result, context)
        except Exception as e:
            return self.create_error_result(e)

    async def __call__(
        self, result: T, context: EvaluationContext[T]
    ) -> EvaluationResult:
        """Execute the evaluation process and manage retry state."""

        if not self.can_retry:
            raise MaxRetriesExceededError(
                f"Evaluator '{self.name}' exceeded max retries ({self.max_retries})"
            )

        self._attempt_count += 1
        return await self.evaluate_safely(result, context)

    def reset(self) -> None:
        """Reset the evaluator's attempt counter."""
        self._attempt_count = 0
