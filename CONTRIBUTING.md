# Contributing

## Local checks

```bash
ruff format --check .
ruff check .
mypy swarm_task
pytest tests -q
python -m build
```

## Release flow

- Conventional commits drive semantic auto-tagging on `main`.
- Pushed `v*` tags create a GitHub Release and publish to PyPI.
