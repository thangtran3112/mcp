"""
MCP Application instance - shared across all modules
"""

import os
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP server - this is the single shared instance
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "flight-simulator"),
    version=os.getenv("MCP_SERVER_VERSION", "0.1.0")
)

# Configure server settings
mcp.description = "Enhanced flight booking and management system with real-time tracking"
mcp.author = "Flight Sim MCP Team"
