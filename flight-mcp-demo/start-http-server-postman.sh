#!/usr/bin/env zsh
set -e

# Postman-friendly HTTP server
# Run with: ./start-http-server.sh
# Then open http://127.0.0.1:8000/docs in Postman or browser

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

# Ensure pip is available
if ! python -m pip --version >/dev/null 2>&1; then
	python -m ensurepip --upgrade || true
fi

python -m pip install --upgrade pip
pip install -r ./requirements.txt

echo "Starting MCP server with HTTP transport on 127.0.0.1:8000"
echo "Open in Postman:"
echo "  - http://127.0.0.1:8000/docs (interactive API docs)"
echo "  - http://127.0.0.1:8000/openapi.json (OpenAPI schema)"
echo ""

# Use HTTP transport
exec "$VENV_DIR/bin/python" -m uvicorn src.http_adapter:app --host 127.0.0.1 --port 8000
