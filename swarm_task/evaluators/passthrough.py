"""Passthrough evaluator that always succeeds.

Use this when you want to run a task through SwarmTask
but skip actual evaluation (use_eval_loop=False case).
"""

from typing import Generic, TypeVar

from ..core.context import EvaluationContext
from ..core.results import EvaluationResult
from ..core.types import EvaluationStatus
from .base import BaseEvaluator

T = TypeVar("T")


class PassthroughEvaluator(BaseEvaluator[T], Generic[T]):
    """Evaluator that always passes without checking.

    This evaluator is used when you want to run a task through SwarmTask
    infrastructure but bypass actual evaluation. It always returns success
    on the first attempt with no retries.

    Example:
        evaluator = VisionEvaluator(...) if use_eval_loop else PassthroughEvaluator()
        task = SwarmTask(evaluators=[evaluator], ...)
    """

    def __init__(self, name: str = "passthrough") -> None:
        """Initialize the passthrough evaluator.

        Args:
            name: Optional name for the evaluator. Defaults to "passthrough".
        """
        super().__init__(max_retries=1, name=name)

    async def evaluate(
        self,
        result: T,
        context: EvaluationContext[T],
    ) -> EvaluationResult:
        """Always return success.

        Args:
            result: The result to evaluate (ignored)
            context: Current evaluation context (ignored)

        Returns:
            EvaluationResult with success=True
        """
        return EvaluationResult(
            status=EvaluationStatus.SUCCESS,
            success=True,
            message="Passthrough - no evaluation performed",
        )

    async def get_improvement_prompt(
        self,
        result: T,
        evaluation_result: EvaluationResult,
        context: EvaluationContext[T],
    ) -> str:
        """No improvement needed - this evaluator always passes.

        Args:
            result: The result that failed evaluation (never called)
            evaluation_result: The evaluation result (never called)
            context: Current evaluation context (never called)

        Returns:
            Empty string (never called since evaluate always succeeds)
        """
        return ""
