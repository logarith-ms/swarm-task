import pytest

from swarm_task.core.types import EvaluationStatus, EvaluatorConfig, SwarmTaskType


def test_swarm_task_type_values():
    """Test SwarmTaskType enum values."""
    assert SwarmTaskType.EVALUATOR_OPTIMIZER == "evaluator_optimizer"


def test_evaluation_status_values():
    """Test EvaluationStatus enum values."""
    assert EvaluationStatus.SUCCESS == "success"
    assert EvaluationStatus.FAILED == "failed"
    assert EvaluationStatus.RETRYING == "retrying"
    assert EvaluationStatus.MAX_RETRIES_EXCEEDED == "max_retries_exceeded"


def test_evaluator_config_validation():
    """Test EvaluatorConfig validation."""
    # Valid config
    config = EvaluatorConfig(max_retries=3, name="test")
    assert config.max_retries == 3
    assert config.name == "test"

    # Invalid max_retries
    with pytest.raises(ValueError):
        EvaluatorConfig(max_retries=0)
