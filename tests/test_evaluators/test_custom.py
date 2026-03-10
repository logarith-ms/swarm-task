from swarm_task.core.context import EvaluationContext
from swarm_task.core.results import EvaluationResult
from swarm_task.core.types import EvaluationStatus
from swarm_task.evaluators.custom import CustomEvaluator


async def test_custom_evaluator_with_custom_functions():
    """Test CustomEvaluator with both evaluation and improvement functions."""

    async def custom_eval(result, context):
        return EvaluationResult(
            status=EvaluationStatus.SUCCESS if result > 0 else EvaluationStatus.FAILED,
            success=result > 0,
            message="Value must be positive",
        )

    async def custom_improve(result, eval_result, context):
        return (
            f"Current value {result} is not positive. Please provide a positive number."
        )

    evaluator = CustomEvaluator(
        evaluator_fn=custom_eval, improvement_prompt_fn=custom_improve
    )

    # Test successful evaluation
    result = await evaluator.evaluate(5, EvaluationContext())
    assert result.success is True

    # Test failed evaluation
    result = await evaluator.evaluate(-1, EvaluationContext())
    assert result.success is False

    # Test improvement prompt
    prompt = await evaluator.get_improvement_prompt(-1, result, EvaluationContext())
    assert "not positive" in prompt


async def test_custom_evaluator_evaluate_with_feedback():
    """Test the evaluate_with_feedback utility method."""

    async def custom_eval(result, context):
        return EvaluationResult(
            status=EvaluationStatus.FAILED, success=False, message="Test failure"
        )

    evaluator = CustomEvaluator(evaluator_fn=custom_eval)
    context = EvaluationContext()

    result, prompt = await evaluator.evaluate_with_feedback("test", context)

    assert result.success is False
    assert prompt is not None
    assert len(context.history) == 1


async def test_custom_evaluator_default_improvement_prompt():
    """Test default improvement prompt when no custom function provided."""

    async def custom_eval(result, context):
        return EvaluationResult(
            status=EvaluationStatus.FAILED, success=False, message="Test failure"
        )

    evaluator = CustomEvaluator(evaluator_fn=custom_eval)
    result = await evaluator.evaluate("test", EvaluationContext())

    prompt = await evaluator.get_improvement_prompt("test", result, EvaluationContext())
    assert "Test failure" in prompt
    assert evaluator.name in prompt
