import logging
from typing import Any, Callable, Coroutine, Optional, TypeVar

from ..core.context import EvaluationContext
from ..core.results import EvaluationResult
from .base import BaseEvaluator

R = TypeVar("R")  # Type for the result being evaluated
logger = logging.getLogger("swarm_task")


class CustomEvaluator(BaseEvaluator[R]):
    """
    Evaluator that uses a custom evaluation function.
    """

    def __init__(
        self,
        evaluator_fn: Callable[
            [R, EvaluationContext[R]], Coroutine[Any, Any, EvaluationResult]
        ],
        improvement_prompt_fn: Optional[
            Callable[
                [R, EvaluationResult, EvaluationContext[R]], Coroutine[Any, Any, str]
            ]
        ] = None,
        max_retries: int = 3,
        name: str = "CustomEvaluator",
    ):
        """
        Initialize the custom evaluator.

        Args:
            evaluator_fn: Async function that performs the evaluation
            improvement_prompt_fn: Optional async function to generate improvement prompts
            max_retries: Maximum number of retry attempts
            name: Name of the evaluator
        """
        super().__init__(max_retries=max_retries, name=name)
        logger.info("CustomEvaluator initialized successfully")
        self.evaluator_fn = evaluator_fn
        self.improvement_prompt_fn = improvement_prompt_fn

    async def evaluate(
        self, result: R, context: EvaluationContext[R]
    ) -> EvaluationResult:
        """
        Execute the custom evaluation function.
        """
        logger.info("Evaluating result with CustomEvaluator")
        return await self.evaluator_fn(result, context)

    async def get_improvement_prompt(
        self,
        result: R,
        evaluation_result: EvaluationResult,
        context: EvaluationContext[R],
    ) -> str:
        """
        Generate improvement prompt using custom function if provided.
        """
        logger.info("Generating improvement prompt for CustomEvaluator")
        if self.improvement_prompt_fn:
            return await self.improvement_prompt_fn(result, evaluation_result, context)

        # Default improvement prompt if no custom function provided
        prompt = (
            f"The previous result failed evaluation by {self.name}. "
            f"Please review and improve based on the following feedback:\n"
            f"{evaluation_result.message}"
        )
        logger.info("Default improvement prompt generated: %s", prompt)
        return prompt

    async def evaluate_with_feedback(
        self, result: R, context: EvaluationContext[R], add_to_history: bool = True
    ) -> tuple[EvaluationResult, Optional[str]]:
        """
        Evaluate and generate improvement feedback in one call.
        Common pattern when immediate feedback is needed.
        """
        evaluation_result = await self.evaluate(result, context)

        improvement_prompt = None
        if not evaluation_result.success:
            improvement_prompt = await self.get_improvement_prompt(
                result, evaluation_result, context
            )

        if add_to_history:
            context.add_attempt(
                result=result,
                evaluator_name=self.name,
                evaluation_result=evaluation_result,
                improvement_prompt=improvement_prompt,
            )

        return evaluation_result, improvement_prompt
