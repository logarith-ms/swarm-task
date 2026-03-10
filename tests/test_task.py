import pytest

from swarm_task.core.context import EvaluationContext
from swarm_task.core.results import EvaluationResult
from swarm_task.core.types import EvaluationStatus
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
    """Test task with multiple evaluators."""

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
    """Test that task respects max retries."""
    attempts = 0

    async def task_fn():
        nonlocal attempts
        attempts += 1
        return {"name": "test", "values": "invalid"}

    task = SwarmTask(
        type=SwarmTaskType.EVALUATOR_OPTIMIZER,
        evaluators=[SchemaValidator(schema=test_schema, max_retries=2)],
    )

    result = await task.run(task_fn)
    assert result.success is False
    assert attempts <= 3  # Initial attempt + 2 retries


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
