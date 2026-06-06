# Contributing

## Development Setup

```bash
uv sync --extra dev
```

On Windows PowerShell:

```powershell
uv sync --extra dev
```

## Checks

```bash
uv run python examples/run_demo.py
uv run idpcg generate --config examples/generation_request.json
uv run python -m unittest discover -s tests
```

## Design Rules

- Keep the offline mock backend working without heavy dependencies.
- Preserve the `GenerationRequest` and manifest schema when adding real backends.
- Put production model code behind optional extras.
- Add tests for CLI contracts and manifest structure.
