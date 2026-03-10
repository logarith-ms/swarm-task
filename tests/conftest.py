from typing import List

import pytest
from pydantic import BaseModel

from swarm_task.core.context import EvaluationContext
from swarm_task.core.results import EvaluationResult
from swarm_task.core.types import EvaluationStatus


class TestSchema(BaseModel):
    """Test schema for validation."""

    name: str
    values: List[int]


@pytest.fixture
def test_schema():
    return TestSchema


@pytest.fixture
def evaluation_context():
    return EvaluationContext()


@pytest.fixture
def successful_evaluation():
    return EvaluationResult(
        status=EvaluationStatus.SUCCESS,
        success=True,
        message="Test passed",
        metadata={"test": True},
    )


@pytest.fixture
def failed_evaluation():
    return EvaluationResult(
        status=EvaluationStatus.FAILED,
        success=False,
        message="Test failed",
        metadata={"test": True},
    )


@pytest.fixture
def valid_test_data():
    return {"name": "test", "values": [1, 2, 3]}


@pytest.fixture
def invalid_test_data():
    return {"name": "test", "values": "not a list"}
