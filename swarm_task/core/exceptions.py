from typing import Any, Optional


class SwarmTaskError(Exception):
    """Base exception for all SwarmTask errors."""

    pass


class EvaluationError(SwarmTaskError):
    """Raised when an evaluation fails unexpectedly."""

    def __init__(
        self,
        message: str,
        evaluator_name: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.evaluator_name = evaluator_name
        self.details = details or {}
        super().__init__(f"[{evaluator_name}] {message}")


class MaxRetriesError(SwarmTaskError):
    """Raised when max retries are exceeded."""

    def __init__(self, evaluator_name: str, max_retries: int):
        self.evaluator_name = evaluator_name
        self.max_retries = max_retries
        super().__init__(
            f"Evaluator '{evaluator_name}' exceeded maximum retries ({max_retries})"
        )


class TaskConfigurationError(SwarmTaskError):
    """Raised when task configuration is invalid."""

    pass
