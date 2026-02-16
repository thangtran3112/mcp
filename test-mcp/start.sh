#!/usr/bin/env zsh
set -e
set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure script runs from its repository directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "${BLUE}========================================${NC}"
echo "${BLUE}   Flight Simulator MCP Server${NC}"
echo "${BLUE}========================================${NC}"
echo ""

# Setup virtual environment
setup_venv() {
    # Prefer an existing .venv, otherwise fall back to ./venv
    if [ -d ".venv" ]; then
        VENV_DIR=".venv"
    else
        VENV_DIR="venv"
    fi

    # Create venv only if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv "$VENV_DIR"
    fi

    # Activate the venv
    source "$VENV_DIR/bin/activate"

    # Ensure pip is available and install dependencies
    if ! python -m pip --version >/dev/null 2>&1; then
        python -m ensurepip --upgrade || true
    fi
    
    echo "${YELLOW}Installing dependencies...${NC}"
    python -m pip install --upgrade pip -q
    pip install -r ./requirements.txt -q
    echo "${GREEN}Dependencies installed.${NC}"
    echo ""
}

# Show menu
show_menu() {
    echo "How would you like to start the MCP server?"
    echo ""
    echo "  ${GREEN}1)${NC} stdio (local/Claude Desktop)"
    echo "  ${GREEN}2)${NC} Streamable HTTP (remote/AWS deployment)"
    echo "  ${GREEN}3)${NC} MCP Inspector (debug/testing)"
    echo "  ${GREEN}4)${NC} Exit"
    echo ""
}

# Start stdio server
start_stdio() {
    echo ""
    echo "${GREEN}Starting MCP server with stdio transport...${NC}"
    echo "${YELLOW}Use Ctrl+C to stop the server${NC}"
    echo ""
    exec python ./src/server.py
}

# Start streamable HTTP server
start_http() {
    echo ""
    
    # Ask for host
    echo -n "Enter host [${BLUE}0.0.0.0${NC}]: "
    read input_host
    HOST="${input_host:-0.0.0.0}"
    
    # Ask for port
    echo -n "Enter port [${BLUE}8000${NC}]: "
    read input_port
    PORT="${input_port:-8000}"
    
    echo ""
    echo "${GREEN}Starting MCP server with Streamable HTTP on ${HOST}:${PORT}...${NC}"
    echo "${YELLOW}Use Ctrl+C to stop the server${NC}"
    echo ""
    echo "Connect using: ${BLUE}http://${HOST}:${PORT}/mcp${NC}"
    echo ""
    
    exec python ./src/server.py --transport streamable-http --host "$HOST" --port "$PORT"
}

# Start MCP Inspector
start_inspector() {
    echo ""
    echo "${GREEN}Starting MCP Inspector...${NC}"
    echo "${YELLOW}This will open a web UI for testing the MCP server${NC}"
    echo "${YELLOW}Access the UI at: http://localhost:6274${NC}"
    echo ""
    
    export npm_config_registry="https://registry.npmjs.org/"
    npx @modelcontextprotocol/inspector python src/server.py
}

# Main
setup_venv

# Check if argument was provided (for non-interactive use)
if [ $# -gt 0 ]; then
    case "$1" in
        stdio|1)
            start_stdio
            ;;
        http|streamable-http|2)
            HOST="${2:-0.0.0.0}"
            PORT="${3:-8000}"
            echo ""
            echo "${GREEN}Starting MCP server with Streamable HTTP on ${HOST}:${PORT}...${NC}"
            exec python ./src/server.py --transport streamable-http --host "$HOST" --port "$PORT"
            ;;
        inspector|3)
            start_inspector
            ;;
        *)
            echo "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [stdio|http|inspector]"
            exit 1
            ;;
    esac
    exit 0
fi

# Interactive mode
while true; do
    show_menu
    echo -n "Enter choice [1-4]: "
    read choice
    
    case "$choice" in
        1)
            start_stdio
            ;;
        2)
            start_http
            ;;
        3)
            start_inspector
            ;;
        4)
            echo ""
            echo "${BLUE}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo ""
            echo "${RED}Invalid option. Please enter 1-4.${NC}"
            echo ""
            ;;
    esac
done
