# swarm-task

Lightweight task orchestration for iterative AI evaluation loops.

`swarm_task` provides a small runtime for running a callable, evaluating the result through one or more evaluators, and retrying until either evaluation succeeds or retry limits are exhausted.

## Install

```bash
pip install swarm-task
```

## Quick Start

```python
from pydantic import BaseModel

from swarm_task import (
    CustomEvaluator,
    EvaluationContext,
    EvaluationResult,
    EvaluationStatus,
    SchemaValidator,
    SwarmTask,
    SwarmTaskType,
)


class ResultSchema(BaseModel):
    name: str
    values: list[int]


async def custom_check(result: dict[str, object], context: EvaluationContext[dict[str, object]]) -> EvaluationResult:
    if len(result["values"]) < 2:
        return EvaluationResult(
            status=EvaluationStatus.FAILED,
            success=False,
            message="Need at least two values",
        )
    return EvaluationResult(status=EvaluationStatus.SUCCESS, success=True)


async def task_fn() -> dict[str, object]:
    return {"name": "example", "values": [1, 2, 3]}


task = SwarmTask(
    type=SwarmTaskType.EVALUATOR_OPTIMIZER,
    evaluators=[
        SchemaValidator(schema=ResultSchema),
        CustomEvaluator(evaluator_fn=custom_check),
    ],
)

result = await task.run(task_fn)
assert result.success is True
```

## Public API

Top-level exports:
- `SwarmTask`
- `SwarmTaskType`
- `EvaluationStatus`
- `EvaluationContext`
- `EvaluationResult`
- `TaskResult`
- `BaseEvaluator`
- `CustomEvaluator`
- `PassthroughEvaluator`
- `SchemaValidator`

## Notes

- `SwarmTask` is async-first and accepts both sync and async callables.
- Evaluators manage their own retry counts.
- The package intentionally ships only the active runtime; archived experimental code is excluded.
