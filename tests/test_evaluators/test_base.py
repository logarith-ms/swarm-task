import pytest

from swarm_task.core.context import EvaluationContext
from swarm_task.core.results import EvaluationResult
from swarm_task.core.types import EvaluationStatus
from swarm_task.evaluators.base import BaseEvaluator, MaxRetriesExceededError


class TestEvaluator(BaseEvaluator[str]):
    """Test implementation of BaseEvaluator."""

    __test__ = False

    async def evaluate(self, result, context):
        return EvaluationResult(
            status=EvaluationStatus.SUCCESS, success=True, message="Test evaluation"
        )

    async def get_improvement_prompt(self, result, evaluation_result, context):
        return "Test improvement prompt"


async def test_base_evaluator_retry_counting():
    """Test retry counting mechanism."""
    evaluator = TestEvaluator(max_retries=2)
    context = EvaluationContext()

    assert evaluator.attempts == 0
    assert evaluator.can_retry is True

    # First attempt
    _ = await evaluator(result="test", context=context)
    assert evaluator.attempts == 1
    assert evaluator.can_retry is True

    # Using __call__ should increment counter
    _ = await evaluator(result="test", context=context)
    assert evaluator.attempts == 2
    assert evaluator.can_retry is False


async def test_base_evaluator_reset():
    """Test reset functionality."""
    evaluator = TestEvaluator(max_retries=1)
    context = EvaluationContext()

    await evaluator(result="test", context=context)
    assert evaluator.attempts == 1

    # Second attempt should raise error
    with pytest.raises(MaxRetriesExceededError) as exc_info:
        await evaluator(result="test", context=context)

    assert evaluator.name in str(exc_info.value)

    # Reset should reset counter
    evaluator.reset()
    assert evaluator.attempts == 0
    assert evaluator.can_retry is True


async def test_base_evaluator_max_retries_error():
    """Test MaxRetriesExceededError handling."""
    evaluator = TestEvaluator(max_retries=1)
    context = EvaluationContext()

    # First attempt
    await evaluator(result="test", context=context)
    assert evaluator.attempts == 1

    # Second attempt should raise error
    with pytest.raises(MaxRetriesExceededError) as exc_info:
        await evaluator(
            result="test", context=context
        )  # Use __call__ instead of evaluate_safely

    assert evaluator.name in str(exc_info.value)
    assert str(evaluator.max_retries) in str(exc_info.value)
