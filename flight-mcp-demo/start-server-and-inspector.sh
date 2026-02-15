#!/usr/bin/env zsh
set -e

export npm_config_registry="https://registry.npmjs.org/"

# Start the HTTP/SSE MCP server
python src/http_mcp_server.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Run the inspector with SSE transport
npx @modelcontextprotocol/inspector sse http://127.0.0.1:8000/sse

# Kill the background server when done
kill $SERVER_PID 2>/dev/null || true
