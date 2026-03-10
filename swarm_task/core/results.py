from datetime import UTC, datetime
from typing import Any, Dict, Generic, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .types import EvaluationStatus, T


def _utc_now_naive() -> datetime:
    """Return a naive UTC timestamp for Pydantic defaults."""
    return datetime.now(UTC).replace(tzinfo=None)


class EvaluationResult(BaseModel):
    """Result of a single evaluation attempt."""

    model_config = ConfigDict(frozen=True)

    status: EvaluationStatus
    success: bool
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HistoryEntry(BaseModel, Generic[T]):
    """Represents a single entry in the evaluation history."""

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(default_factory=_utc_now_naive)
    evaluator_name: str
    attempt_number: int = Field(ge=1)
    result: T
    evaluation_result: EvaluationResult
    improvement_prompt: Optional[str] = None


class TaskResult(BaseModel, Generic[T]):
    """Final result of a SwarmTask execution."""

    result: T
    success: bool
    total_attempts: int = Field(ge=1)
    history: List[HistoryEntry[T]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def last_attempt(self) -> Optional[HistoryEntry[T]]:
        """Get the most recent evaluation attempt."""
        return self.history[-1] if self.history else None

    @property
    def failed_attempts(self) -> List[HistoryEntry[T]]:
        """Get all failed evaluation attempts."""
        return [entry for entry in self.history if not entry.evaluation_result.success]

    @property
    def successful_attempts(self) -> List[HistoryEntry[T]]:
        """Get all successful evaluation attempts."""
        return [entry for entry in self.history if entry.evaluation_result.success]
