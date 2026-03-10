from swarm_task.core.context import EvaluationContext


async def test_context_initialization():
    """Test that context initializes with empty history and metadata."""
    context = EvaluationContext()
    assert len(context.history) == 0
    assert len(context.metadata) == 0


async def test_add_attempt(evaluation_context, successful_evaluation):
    """Test adding an attempt to the context."""
    context = evaluation_context

    context.add_attempt(
        result={"test": "data"},
        evaluator_name="test_evaluator",
        evaluation_result=successful_evaluation,
    )

    assert len(context.history) == 1
    entry = context.history[0]
    assert entry.evaluator_name == "test_evaluator"
    assert entry.evaluation_result == successful_evaluation


async def test_context_metadata_update(evaluation_context):
    """Test updating context metadata."""
    context = evaluation_context

    context.update_metadata(test_key="test_value")
    assert context.metadata["test_key"] == "test_value"


async def test_get_attempts_by_evaluator(evaluation_context, successful_evaluation):
    """Test filtering attempts by evaluator."""
    context = evaluation_context

    # Add attempts from different evaluators
    context.add_attempt(
        result={"test": "data1"},
        evaluator_name="evaluator1",
        evaluation_result=successful_evaluation,
    )
    context.add_attempt(
        result={"test": "data2"},
        evaluator_name="evaluator2",
        evaluation_result=successful_evaluation,
    )

    evaluator1_attempts = context.get_attempts_by_evaluator("evaluator1")
    assert len(evaluator1_attempts) == 1
    assert evaluator1_attempts[0].evaluator_name == "evaluator1"
