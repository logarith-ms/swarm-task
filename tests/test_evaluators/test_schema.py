from swarm_task.core.types import EvaluationStatus
from swarm_task.evaluators.schema import SchemaValidator


async def test_schema_validator_success(
    test_schema, evaluation_context, valid_test_data
):
    """Test successful schema validation."""
    validator = SchemaValidator(schema=test_schema)

    result = await validator.evaluate(valid_test_data, evaluation_context)

    assert result.success is True
    assert result.status == EvaluationStatus.SUCCESS


async def test_schema_validator_failure(
    test_schema, evaluation_context, invalid_test_data
):
    """Test failed schema validation."""
    validator = SchemaValidator(schema=test_schema)

    result = await validator.evaluate(invalid_test_data, evaluation_context)
    assert result.message is not None, "Message should not be None"

    assert result.success is False
    assert result.status == EvaluationStatus.FAILED
    assert "validation" in result.message.lower()


async def test_schema_validator_retry_count(
    test_schema, evaluation_context, invalid_test_data
):
    """Test retry counting."""
    validator = SchemaValidator(schema=test_schema, max_retries=2)

    # First attempt using __call__
    _ = await validator(invalid_test_data, evaluation_context)
    assert validator.attempts == 1
    assert validator.can_retry is True

    # Second attempt
    _ = await validator(invalid_test_data, evaluation_context)
    assert validator.attempts == 2
    assert validator.can_retry is False
