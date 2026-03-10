from enum import StrEnum
from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")  # Generic type for task results


class SwarmTaskType(StrEnum):
    """Types of tasks that can be executed by SwarmTask."""

    EVALUATOR_OPTIMIZER = "evaluator_optimizer"
    # Extensible for future task types
    # CHAIN = "chain"
    # PARALLEL = "parallel"


class EvaluationStatus(StrEnum):
    """Status of an evaluation attempt."""

    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"


class EvaluatorConfig(BaseModel):
    """Configuration options for evaluators."""

    model_config = ConfigDict(frozen=True)

    max_retries: int = Field(default=3, ge=1)
    name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
