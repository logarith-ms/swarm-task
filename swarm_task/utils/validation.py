import logging
from typing import Any, List

from ..core.exceptions import TaskConfigurationError
from ..evaluators.base import BaseEvaluator

logger = logging.getLogger("swarm_task")


def validate_evaluator_chain(evaluators: List[BaseEvaluator[Any]]) -> None:
    """
    Validate evaluator chain configuration.

    Args:
        evaluators: List of evaluators to validate

    Raises:
        TaskConfigurationError: If configuration is invalid
    """
    logger.info("Validating evaluator chain")
    if not evaluators:
        raise TaskConfigurationError("At least one evaluator must be provided")

    # Check for duplicate evaluator names
    names = [e.name for e in evaluators]
    if len(names) != len(set(names)):
        raise TaskConfigurationError("Evaluator names must be unique")

    logger.info("Evaluator chain validated successfully")


def validate_retry_limits(evaluators: List[BaseEvaluator[Any]]) -> None:
    """
    Validate retry limits for all evaluators.

    Args:
        evaluators: List of evaluators to validate

    Raises:
        TaskConfigurationError: If retry limits are invalid
    """
    logger.info("Validating retry limits")
    for evaluator in evaluators:
        if evaluator.max_retries < 1:
            raise TaskConfigurationError(
                f"Invalid max_retries for evaluator '{evaluator.name}': "
                f"must be >= 1"
            )
    logger.info("Retry limits validated successfully")
