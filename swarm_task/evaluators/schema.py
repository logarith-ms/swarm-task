import logging
from typing import Any, List, Type

from pydantic import BaseModel, ValidationError

from ..core.context import EvaluationContext
from ..core.results import EvaluationResult
from ..core.types import EvaluationStatus
from .base import BaseEvaluator

logger = logging.getLogger("swarm_task")


class SchemaValidator(BaseEvaluator[Any]):
    """
    Evaluator that validates results against a Pydantic schema.
    """

    def __init__(
        self,
        schema: Type[BaseModel],
        max_retries: int = 3,
        name: str = "SchemaValidator",
    ):
        """
        Initialize the schema validator.

        Args:
            schema: Pydantic model class to validate against
            max_retries: Maximum number of retry attempts
            name: Name of the validator
        """
        super().__init__(max_retries=max_retries, name=name)
        self.schema = schema
        logger.info("SchemaValidator initialized successfully")

    async def evaluate(
        self, result: Any, _context: EvaluationContext[Any]
    ) -> EvaluationResult:
        """
        Validate the result against the schema.
        """
        logger.info("Evaluating result against schema")
        try:
            # Validate the result against the schema
            self.schema.model_validate(result)

            logger.info("Schema validation successful")
            return EvaluationResult(
                status=EvaluationStatus.SUCCESS,
                success=True,
                message="Schema validation successful",
                metadata={"schema": self.schema.__name__},
            )

        except ValidationError as e:
            logger.error("Schema validation failed", extra={"error": str(e)})
            return EvaluationResult(
                status=EvaluationStatus.FAILED,
                success=False,
                message="Schema validation failed",
                metadata={
                    "schema": self.schema.__name__,
                    "validation_errors": e.errors(),
                },
            )

    async def get_improvement_prompt(
        self,
        _result: Any,
        evaluation_result: EvaluationResult,
        _context: EvaluationContext[Any],
    ) -> str:
        """
        Generate a prompt to fix schema validation errors.
        """
        logger.info("Generating improvement prompt for schema validation")
        errors = evaluation_result.metadata.get("validation_errors", [])
        error_summary = self.get_validation_errors_summary(errors)

        prompt = (
            f"The previous result failed schema validation for {self.schema.__name__}. "
            f"Please fix the following issues:\n"
            f"{error_summary}\n"
            f"Ensure the response matches the required schema exactly."
        )

        logger.info("Improvement prompt generated: %s", prompt)

        return prompt

    def get_validation_errors_summary(self, errors: List[Any]) -> str:
        """
        Create a human-readable summary of validation errors.
        Useful for both logging and prompt generation.
        """
        return "\n".join(
            f"- Field '{'.'.join(str(loc) for loc in error['loc'])}': {error['msg']}"
            for error in errors
        )
