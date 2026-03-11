import logging
from inspect import iscoroutinefunction
from typing import Awaitable, Callable, Generic, List, Optional, Union, cast

from .core.context import EvaluationContext
from .core.results import EvaluationResult, TaskResult
from .core.types import SwarmTaskType, T
from .evaluators.base import BaseEvaluator, MaxRetriesExceededError
from .utils.validation import validate_evaluator_chain, validate_retry_limits

logger = logging.getLogger("swarm_task")


class SwarmTask(Generic[T]):
    """
    Main task orchestrator that manages the evaluation-optimization pipeline.
    """

    def __init__(
        self,
        type: SwarmTaskType,
        evaluators: List[BaseEvaluator[T]],
        name: Optional[str] = None,
    ):
        """
        Initialize a SwarmTask.

        Args:
            type: Type of task (currently only EVALUATOR_OPTIMIZER)
            evaluators: List of evaluators to run in sequence
            name: Optional name for the task
        """
        # Validate configuration
        validate_evaluator_chain(evaluators)
        validate_retry_limits(evaluators)

        self.type = type
        self.evaluators = evaluators
        self.name = name or self.__class__.__name__

        logger.debug(
            "SwarmTask initialized successfully",
            extra={
                "type": self.type,
                "evaluators": self.evaluator_names,
                "name": self.name,
            },
        )

    async def run(
        self,
        task_fn: Union[Callable[[], T], Callable[[], Awaitable[T]]],
        context: Optional[EvaluationContext[T]] = None,
    ) -> TaskResult[T]:
        """Execute the task with evaluation and optimization."""
        logger.info("Running SwarmTask")
        return await self._run(task_fn, context)

    async def _run(
        self,
        task_fn: Union[Callable[[], T], Callable[[], Awaitable[T]]],
        context: Optional[EvaluationContext[T]] = None,
    ) -> TaskResult[T]:
        """
        Execute the task with evaluation and optimization.

        Args:
            task_fn: Callable that produces the result to evaluate
            context: Optional existing context (creates new if None)

        Returns:
            TaskResult containing final result and execution history
        """
        context = context or EvaluationContext[T]()
        task_attempts = 0
        max_total_attempts = max(e.max_retries for e in self.evaluators) + 1
        last_result: Optional[T] = None

        def build_failure_result(
            result: T,
            reason: str,
            **metadata: object,
        ) -> TaskResult[T]:
            failure_metadata = {"reason": reason, **metadata}
            logger.error("SwarmTask failed", extra=failure_metadata)
            return TaskResult(
                result=result,
                success=False,
                total_attempts=max(1, task_attempts),
                history=context.history,
                metadata=failure_metadata,
            )

        while task_attempts < max_total_attempts:
            task_attempts += 1
            logger.info("Attempt %s of %s", task_attempts, max_total_attempts)

            logger.debug("Task fn %s", task_fn)

            try:
                result = cast(
                    T, await task_fn() if iscoroutinefunction(task_fn) else task_fn()
                )
            except Exception as error:
                if last_result is None:
                    raise
                return build_failure_result(
                    last_result,
                    "Task function failed",
                    error_type=type(error).__name__,
                    error_message=str(error),
                )

            last_result = result
            logger.debug("Result %s", result)

            success = True
            for evaluator in self.evaluators:
                try:
                    evaluation_result = await evaluator(result, context)
                    logger.debug("Evaluation result %s", evaluation_result)

                    if not evaluation_result.success:
                        success = False
                        improvement_prompt = await evaluator.get_improvement_prompt(
                            result, evaluation_result, context
                        )
                        context.add_attempt(
                            result=result,
                            evaluator_name=evaluator.name,
                            evaluation_result=evaluation_result,
                            improvement_prompt=improvement_prompt,
                        )
                        break

                    context.add_attempt(
                        result=result,
                        evaluator_name=evaluator.name,
                        evaluation_result=evaluation_result,
                    )

                except MaxRetriesExceededError:
                    return build_failure_result(
                        result=result,
                        reason="Max retries exceeded",
                        failed_evaluator=evaluator.name,
                    )
                except Exception as error:
                    return build_failure_result(
                        result=result,
                        reason="Evaluation pipeline failed",
                        failed_evaluator=evaluator.name,
                        error_type=type(error).__name__,
                        error_message=str(error),
                    )

            if success:
                return TaskResult(
                    result=result,
                    success=True,
                    total_attempts=max(1, task_attempts),
                    history=context.history,
                    metadata={"final_evaluator": self.evaluators[-1].name},
                )

        assert last_result is not None
        return build_failure_result(
            last_result,
            "Maximum total attempts exceeded",
            max_attempts=max_total_attempts,
        )

    @property
    def evaluator_names(self) -> List[str]:
        """Get names of all evaluators in the pipeline."""
        return [evaluator.name for evaluator in self.evaluators]

    def reset_evaluators(self) -> None:
        """Reset attempt counters for all evaluators."""
        for evaluator in self.evaluators:
            evaluator.reset()

    async def run_single_evaluation(
        self, result: T, context: Optional[EvaluationContext[T]] = None
    ) -> List[EvaluationResult]:
        """
        Run a single evaluation pass through all evaluators without optimization.
        Useful for testing or one-off evaluations.

        Args:
            result: Result to evaluate
            context: Optional context (creates new if None)

        Returns:
            List of evaluation results from each evaluator
        """
        context = context or EvaluationContext[T]()
        results = []

        for evaluator in self.evaluators:
            evaluation_result = await evaluator.evaluate_safely(result, context)
            results.append(evaluation_result)

            context.add_attempt(
                result=result,
                evaluator_name=evaluator.name,
                evaluation_result=evaluation_result,
            )

            if not evaluation_result.success:
                break

        return results
