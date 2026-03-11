import pytest

from swarm_task.core.context import EvaluationContext
from swarm_task.core.exceptions import SwarmTaskError
from swarm_task.core.results import EvaluationResult
from swarm_task.core.types import EvaluationStatus
from swarm_task.evaluators import PassthroughEvaluator
from swarm_task.evaluators.custom import CustomEvaluator
from swarm_task.evaluators.schema import SchemaValidator
from swarm_task.task import SwarmTask, SwarmTaskType


async def test_swarm_task_successful_run(test_schema, valid_test_data):
    """Test successful task execution."""

    async def task_fn():
        return valid_test_data

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[SchemaValidator(schema=test_schema)],
    )

    result = await task.run(task_fn)
    assert result.success is True
    assert len(result.history) == 1


async def test_swarm_task_with_multiple_evaluators(test_schema):
    """TaskResult.total_attempts should count task invocations, not history entries."""

    async def task_fn():
        return {"name": "test", "values": [1, 2, 3]}

    async def custom_eval(result, context):
        return EvaluationResult(
            status=EvaluationStatus.SUCCESS, success=True, message="Custom check passed"
        )

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[
            SchemaValidator(schema=test_schema),
            CustomEvaluator(evaluator_fn=custom_eval),
        ],
    )

    result = await task.run(task_fn)
    assert result.success is True
    assert result.total_attempts == 1
    assert len(result.history) == 2


async def test_swarm_task_failure_handling(test_schema, invalid_test_data):
    """Test task failure handling."""
    attempts = 0
    max_attempts = 2

    async def task_fn():
        nonlocal attempts
        attempts += 1
        return invalid_test_data

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[SchemaValidator(schema=test_schema, max_retries=1)],
    )

    result = await task.run(task_fn)
    assert result.success is False
    assert len(result.history) == 1
    assert attempts <= max_attempts


async def test_swarm_task_max_retries(test_schema):
    """Retry exhaustion should preserve the last produced result."""
    attempts = 0
    invalid_result = {"name": "test", "values": "invalid"}

    async def task_fn():
        nonlocal attempts
        attempts += 1
        return invalid_result

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[SchemaValidator(schema=test_schema, max_retries=2)],
    )

    result = await task.run(task_fn)
    assert result.success is False
    assert result.result == invalid_result
    assert result.total_attempts == 3
    assert result.metadata["reason"] == "Max retries exceeded"
    assert attempts == 3


async def test_swarm_task_raises_when_no_result_exists_before_first_attempt():
    """Exceptions should propagate when the task produced no result at all."""

    async def task_fn():
        raise SwarmTaskError("boom")

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[PassthroughEvaluator()],
    )

    with pytest.raises(SwarmTaskError, match="boom"):
        await task.run(task_fn)


async def test_swarm_task_raises_generic_exception_when_no_result_exists():
    """Generic exceptions should also propagate when nothing was produced."""

    async def task_fn():
        raise RuntimeError("boom")

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[PassthroughEvaluator()],
    )

    with pytest.raises(RuntimeError, match="boom"):
        await task.run(task_fn)


async def test_swarm_task_preserves_result_when_improvement_prompt_fails():
    """Post-result failures should return the produced result instead of dropping it."""

    async def task_fn():
        return {"name": "test", "values": [1]}

    async def failed_eval(result, context):
        return EvaluationResult(
            status=EvaluationStatus.FAILED,
            success=False,
            message="Need retry",
        )

    async def broken_prompt(result, evaluation_result, context):
        raise RuntimeError("prompt boom")

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[
            CustomEvaluator(
                evaluator_fn=failed_eval,
                improvement_prompt_fn=broken_prompt,
            )
        ],
    )

    result = await task.run(task_fn)

    assert result.success is False
    assert result.result == {"name": "test", "values": [1]}
    assert result.total_attempts == 1
    assert result.metadata["reason"] == "Evaluation pipeline failed"
    assert result.metadata["error_type"] == "RuntimeError"


async def test_swarm_task_preserves_last_result_when_later_attempt_raises(test_schema):
    """A later pre-result failure should preserve the last produced result."""
    attempts = 0
    first_result = {"name": "test", "values": "invalid"}

    async def task_fn():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return first_result
        raise RuntimeError("task boom")

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[SchemaValidator(schema=test_schema, max_retries=2)],
    )

    result = await task.run(task_fn)

    assert result.success is False
    assert result.result == first_result
    assert result.total_attempts == 2
    assert result.metadata["reason"] == "Task function failed"
    assert result.metadata["error_type"] == "RuntimeError"


@pytest.mark.asyncio
async def test_swarm_task_context_reuse(test_schema):
    """Test that context is properly maintained between attempts."""
    context = EvaluationContext()

    async def task_fn():
        return {"name": "test", "values": [1, 2, 3]}

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[SchemaValidator(schema=test_schema)],
    )

    _ = await task.run(task_fn, context=context)
    assert context.total_attempts == 1
