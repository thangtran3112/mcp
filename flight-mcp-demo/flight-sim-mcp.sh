#!/usr/bin/env zsh
set -e
set -u
set -o pipefail
# Ensure script runs from its repository directory so relative paths work
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer an existing .venv, otherwise fall back to ./venv
if [ -d ".venv" ]; then
	VENV_DIR=".venv"
else
	VENV_DIR="venv"
fi

# Create venv only if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
	python3 -m venv "$VENV_DIR"
fi

# Activate the venv
source "$VENV_DIR/bin/activate"

# Ensure pip is available inside the venv (bootstrap if needed), then upgrade and install
if ! python -m pip --version >/dev/null 2>&1; then
	python -m ensurepip --upgrade || true
fi
python -m pip install --upgrade pip
pip install -r ./requirements.txt

# Allow a safe dry-run for testing: set SKIP_SERVER=1 to stop before launching
if [ "${SKIP_SERVER:-0}" = "1" ]; then
	echo "SKIP_SERVER=1 set — skipping server start"
	exit 0
fi

# Start the server
python ./src/server.py
