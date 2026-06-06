#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip uv
uv sync --extra dev

cat <<'MSG'
Environment ready.

For local development and tests, run:
  uv run python -m unittest discover -s tests

For real SDXL/HunyuanDiT training and inference dependencies, run:
  uv sync --extra full
MSG
