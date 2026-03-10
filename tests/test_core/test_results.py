from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from swarm_task.core.results import EvaluationResult, HistoryEntry, TaskResult
from swarm_task.core.types import EvaluationStatus


def test_evaluation_result_immutability():
    """Test that EvaluationResult is immutable."""
    result = EvaluationResult(
        status=EvaluationStatus.SUCCESS, success=True, message="test"
    )

    with pytest.raises(ValidationError):
        result.success = False


def test_history_entry_timestamp():
    """Test HistoryEntry timestamp generation."""
    before = datetime.now(timezone.utc).replace(tzinfo=None)
    entry = HistoryEntry(
        evaluator_name="test",
        attempt_number=1,
        result="test",
        evaluation_result=EvaluationResult(
            status=EvaluationStatus.SUCCESS, success=True
        ),
    )
    after = datetime.now(timezone.utc).replace(tzinfo=None)

    assert before <= entry.timestamp <= after


def test_task_result_properties():
    """Test TaskResult helper properties."""
    failed_eval = EvaluationResult(status=EvaluationStatus.FAILED, success=False)
    success_eval = EvaluationResult(status=EvaluationStatus.SUCCESS, success=True)

    result = TaskResult(
        result="test",
        success=False,
        total_attempts=2,
        history=[
            HistoryEntry(
                evaluator_name="test",
                attempt_number=1,
                result="test",
                evaluation_result=failed_eval,
            ),
            HistoryEntry(
                evaluator_name="test",
                attempt_number=2,
                result="test",
                evaluation_result=success_eval,
            ),
        ],
    )

    assert len(result.failed_attempts) == 1
    assert len(result.successful_attempts) == 1
    assert result.last_attempt is not None
    assert result.last_attempt.evaluation_result.success is True
