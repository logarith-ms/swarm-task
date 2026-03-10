import logging
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .results import EvaluationResult, HistoryEntry
from .types import T

logger = logging.getLogger("swarm_task")


class EvaluationContext(BaseModel, Generic[T]):
    """
    Maintains state and history during the evaluation process.

    This context object is passed between evaluators and maintains
    the complete history of evaluation attempts and metadata.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",  # Allows storing additional metadata
    )

    history: List[HistoryEntry[T]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_attempt(
        self,
        result: T,
        evaluator_name: str,
        evaluation_result: EvaluationResult,
        improvement_prompt: Optional[str] = None,
    ) -> None:
        """
        Record a new evaluation attempt in the history.

        Args:
            result: The result that was evaluated
            evaluator_name: Name of the evaluator
            evaluation_result: Result of the evaluation
            improvement_prompt: Optional prompt for improvement
        """
        entry: HistoryEntry[T] = HistoryEntry(
            timestamp=datetime.now(),
            evaluator_name=evaluator_name,
            attempt_number=len(self.history) + 1,
            result=result,
            evaluation_result=evaluation_result,
            improvement_prompt=improvement_prompt,
        )
        logger.info("Adding evaluation attempt for %s", evaluator_name)
        logger.debug("Evaluation attempt added", extra={"entry": entry})
        self.history.append(entry)

    @property
    def last_attempt(self) -> Optional[HistoryEntry[T]]:
        """Get the most recent evaluation attempt."""
        return self.history[-1] if self.history else None

    @property
    def total_attempts(self) -> int:
        """Get total number of evaluation attempts."""
        return len(self.history)

    @property
    def successful_attempts(self) -> List[HistoryEntry[T]]:
        """Get all successful evaluation attempts."""
        return [entry for entry in self.history if entry.evaluation_result.success]

    @property
    def failed_attempts(self) -> List[HistoryEntry[T]]:
        """Get all failed evaluation attempts."""
        return [entry for entry in self.history if not entry.evaluation_result.success]

    def get_attempts_by_evaluator(self, evaluator_name: str) -> List[HistoryEntry[T]]:
        """
        Get all attempts for a specific evaluator.

        Args:
            evaluator_name: Name of the evaluator to filter by

        Returns:
            List of attempts by the specified evaluator
        """
        return [
            entry for entry in self.history if entry.evaluator_name == evaluator_name
        ]

    def update_metadata(self, **kwargs: Any) -> None:
        """
        Update context metadata with new key-value pairs.

        Args:
            **kwargs: Key-value pairs to add to metadata
        """
        self.metadata.update(kwargs)
