# Contributing

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

## Checks

```bash
python examples/run_demo.py
idpcg generate --config examples/generation_request.json
python -m unittest discover -s tests
```

## Design Rules

- Keep the offline mock backend working without heavy dependencies.
- Preserve the `GenerationRequest` and manifest schema when adding real backends.
- Put production model code behind optional extras.
- Add tests for CLI contracts and manifest structure.
