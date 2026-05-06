#!/usr/bin/env bash
# One-command dev API from backend/ with this repo's .venv (Unix).
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  echo "Create venv first: python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi
export PYTHONPATH=.
export ENABLE_OLLAMA="${ENABLE_OLLAMA:-0}"
echo "Starting SafeNest API at http://127.0.0.1:8000 (PYTHONPATH=. ENABLE_OLLAMA=$ENABLE_OLLAMA)"
exec .venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
