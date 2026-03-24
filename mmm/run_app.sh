#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${PORT:-8501}"
INSTALL_ONLY="${INSTALL_ONLY:-0}"
FORCE_REINSTALL="${FORCE_REINSTALL:-0}"
VENV_DIR=".venv"
APP_PYTHON="$VENV_DIR/bin/python"
APP_PIP="$VENV_DIR/bin/pip"
FINGERPRINT_FILE="$VENV_DIR/.requirements.sha256"

fail() {
  echo "Error: $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [ -f "$path" ] || fail "Required file not found: $path"
}

select_system_python() {
  local candidates=(
    "python3.9"
    "python3"
    "python"
    "python3.10"
    "python3.11"
    "python3.12"
    "python3.13"
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    if ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi
    if "$candidate" - <<'PY' >/dev/null 2>&1; then
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

python_version_string() {
  local python_bin="$1"
  "$python_bin" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
PY
}

requirements_fingerprint() {
  local python_bin="$1"
  "$python_bin" - <<'PY'
from __future__ import annotations

import hashlib
from pathlib import Path

base = Path(".")
payload = []
for name in ["requirements.txt", ".python-version"]:
    path = base / name
    payload.append(f"{name}:{path.read_text(encoding='utf-8')}")
print(hashlib.sha256("\n".join(payload).encode("utf-8")).hexdigest())
PY
}

environment_ready() {
  local python_bin="$1"
  "$python_bin" - <<'PY' >/dev/null 2>&1
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
}

require_file "app.py"
require_file "requirements.txt"
require_file ".python-version"

SYSTEM_PYTHON="$(select_system_python)" || fail "Python 3.9 or higher is required but was not found."

if [ ! -x "$APP_PYTHON" ]; then
  echo "Creating virtual environment with $(python_version_string "$SYSTEM_PYTHON")..."
  "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
fi

if ! "$APP_PYTHON" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
then
  fail "The existing virtual environment uses Python older than 3.9. Delete .venv and run the script again."
fi

CURRENT_FINGERPRINT="$(requirements_fingerprint "$APP_PYTHON")"
STORED_FINGERPRINT=""
if [ -f "$FINGERPRINT_FILE" ]; then
  STORED_FINGERPRINT="$(<"$FINGERPRINT_FILE")"
fi

NEEDS_INSTALL=0
if [ "$FORCE_REINSTALL" = "1" ]; then
  NEEDS_INSTALL=1
elif [ ! -f "$APP_PIP" ]; then
  NEEDS_INSTALL=1
elif [ "$CURRENT_FINGERPRINT" != "$STORED_FINGERPRINT" ]; then
  NEEDS_INSTALL=1
elif ! environment_ready "$APP_PYTHON"; then
  NEEDS_INSTALL=1
fi

if [ "$NEEDS_INSTALL" = "1" ]; then
  echo "Installing dependencies from requirements.txt..."
  "$APP_PIP" install --upgrade pip
  "$APP_PIP" install -r requirements.txt
  printf '%s' "$CURRENT_FINGERPRINT" > "$FINGERPRINT_FILE"
fi

if ! environment_ready "$APP_PYTHON"; then
  fail "Dependency verification failed after installation. Inspect the pip output above and try again."
fi

if [ "$INSTALL_ONLY" = "1" ]; then
  echo "Environment is ready. Skipping app launch because INSTALL_ONLY=1."
  exit 0
fi

if command -v lsof >/dev/null 2>&1 && lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  fail "Port $PORT is already in use. Stop the existing server or run with another port, for example: PORT=8507 ./run_app.sh"
fi

export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_HEADLESS=true

echo "Starting the MMM app..."
echo "Using Python $(python_version_string "$APP_PYTHON") from $APP_PYTHON"
echo "Open this link in your browser: http://localhost:$PORT"
echo ""

printf '\n' | "$APP_PYTHON" -m streamlit run app.py --server.port "$PORT"
