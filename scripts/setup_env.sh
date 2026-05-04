#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f ".venv/bin/python" ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi

VENV_PY="$SCRIPT_DIR/.venv/bin/python"
echo "Upgrading pip and installing requirements using: $VENV_PY"
$VENV_PY -m pip install --upgrade pip
$VENV_PY -m pip install -r "$SCRIPT_DIR/../requirements.txt"

echo "Environment setup complete. Run: $VENV_PY -m streamlit run ../app.py"
