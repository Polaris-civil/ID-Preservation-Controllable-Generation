#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .

cat <<'MSG'
Environment ready.

For local development and tests, run:
  pip install -e ".[dev]"

For real SDXL/HunyuanDiT training and inference dependencies, run:
  pip install -e ".[full]"
MSG
