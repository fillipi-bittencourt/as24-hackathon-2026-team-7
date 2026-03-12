#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${PORT:-8501}"
PYTHON_BIN=""
APP_PYTHON=".venv/bin/python"

if [ -x "$APP_PYTHON" ]; then
  PYTHON_BIN="$APP_PYTHON"
fi

if [ -z "$PYTHON_BIN" ]; then
  if command -v python3.9 >/dev/null 2>&1; then
    PYTHON_BIN="python3.9"
  elif command -v python3.10 >/dev/null 2>&1; then
    PYTHON_BIN="python3.10"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "Python 3 is required but was not found."
    exit 1
  fi
fi

"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 9):
    raise SystemExit("Python 3.9 or higher is required.")
PY

if [ ! -x "$APP_PYTHON" ]; then
  echo "Creating virtual environment..."
  "$PYTHON_BIN" -m venv .venv
  APP_PYTHON=".venv/bin/python"
fi

if ! "$APP_PYTHON" - <<'PY' >/dev/null 2>&1; then
import streamlit
import pandas
import numpy
import scipy
import statsmodels
import sklearn
import pymc
import arviz
import openai
import anthropic
PY
  echo "Installing dependencies from requirements.txt..."
  ./.venv/bin/pip install --upgrade pip
  ./.venv/bin/pip install -r requirements.txt
fi

if command -v lsof >/dev/null 2>&1 && lsof -i TCP:"$PORT" >/dev/null 2>&1; then
  echo "Port $PORT is already in use. Stop the existing server or run with another port, for example:"
  echo "PORT=8507 ./run_app.sh"
  exit 1
fi

export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo "Starting the MMM app..."
echo "Open this link in your browser: http://localhost:$PORT"
echo ""

printf '\n' | ./.venv/bin/streamlit run app.py --server.port "$PORT"
