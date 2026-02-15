#!/usr/bin/env python3
"""
HTTP/SSE MCP Server for AWS deployment
Wraps the FastMCP server to expose it via Server-Sent Events (SSE)
"""

import os
import sys
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from server import (
    search_flights, get_flight_details, create_booking, get_booking,
    cancel_booking, check_in, get_airport_info, get_flight_status,
    find_best_flight, handle_disruption
)

# Load environment
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Flight MCP Server (HTTP/SSE)",
    version="1.0.0",
    description="MCP server exposed via HTTP Server-Sent Events for AWS deployment"
)

# Store active SSE connections and message queues
class SSEConnection:
    def __init__(self):
        self.messages = asyncio.Queue()
        self.initialized = False

active_connections: Dict[int, SSEConnection] = {}
connection_counter = 0


class CallToolRequest(BaseModel):
    arguments: Dict[str, Any]


async def sse_event(event_type: str, data: Any) -> str:
    """Format a Server-Sent Event"""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def mcp_sse_stream(connection_id: int) -> AsyncGenerator[str, None]:
    """
    MCP Server-Sent Events stream
    Handles the bidirectional communication protocol
    """
    try:
        conn = active_connections[connection_id]
        
        # Send initialization event
        yield await sse_event("initialized", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "flight-simulator",
                "version": "1.0.0"
            }
        })
        
        conn.initialized = True
        
        # Keep connection alive and process messages
        while connection_id in active_connections:
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(
                    conn.messages.get(), 
                    timeout=30.0
                )
                
                if message["type"] == "list_resources":
                    # List all available tools
                    tools = [
                        {
                            "name": "search_flights",
                            "description": "Search for available flights",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "origin": {"type": "string"},
                                    "destination": {"type": "string"},
                                    "departure_date": {"type": "string"},
                                    "passengers": {"type": "integer", "default": 1},
                                    "seat_class": {"type": "string", "default": "economy"}
                                },
                                "required": ["origin", "destination", "departure_date"]
                            }
                        },
                        {
                            "name": "get_flight_details",
                            "description": "Get details for a specific flight",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "flight_id": {"type": "string"}
                                },
                                "required": ["flight_id"]
                            }
                        },
                        {
                            "name": "create_booking",
                            "description": "Create a new flight booking",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "flight_id": {"type": "string"},
                                    "passengers": {"type": "array"},
                                    "seat_class": {"type": "string"}
                                },
                                "required": ["flight_id", "passengers"]
                            }
                        },
                        {
                            "name": "get_booking",
                            "description": "Retrieve booking details",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "booking_id": {"type": "string"},
                                    "email": {"type": "string"}
                                },
                                "required": ["booking_id"]
                            }
                        },
                        {
                            "name": "cancel_booking",
                            "description": "Cancel a booking",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "booking_id": {"type": "string"},
                                    "reason": {"type": "string"}
                                },
                                "required": ["booking_id"]
                            }
                        },
                        {
                            "name": "check_in",
                            "description": "Check in for a flight",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "booking_id": {"type": "string"}
                                },
                                "required": ["booking_id"]
                            }
                        },
                        {
                            "name": "get_airport_info",
                            "description": "Get airport information",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "code": {"type": "string"}
                                },
                                "required": ["code"]
                            }
                        },
                        {
                            "name": "get_flight_status",
                            "description": "Get current flight status",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "flight_id": {"type": "string"}
                                },
                                "required": ["flight_id"]
                            }
                        }
                    ]
                    
                    yield await sse_event("resources/list_result", {
                        "resources": tools
                    })
                
                elif message["type"] == "call_tool":
                    try:
                        tool_name = message.get("name")
                        args = message.get("arguments", {})
                        
                        # Call the appropriate tool
                        if tool_name == "search_flights":
                            result = await search_flights(**args)
                        elif tool_name == "get_flight_details":
                            result = await get_flight_details(**args)
                        elif tool_name == "create_booking":
                            result = await create_booking(**args)
                        elif tool_name == "get_booking":
                            result = await get_booking(**args)
                        elif tool_name == "cancel_booking":
                            result = await cancel_booking(**args)
                        elif tool_name == "check_in":
                            result = await check_in(**args)
                        elif tool_name == "get_airport_info":
                            result = await get_airport_info(**args)
                        elif tool_name == "get_flight_status":
                            result = await get_flight_status(**args)
                        else:
                            raise ValueError(f"Unknown tool: {tool_name}")
                        
                        yield await sse_event("tool_result", {
                            "content": [{"type": "text", "text": json.dumps(result)}]
                        })
                    except Exception as e:
                        yield await sse_event("error", {
                            "code": -32603,
                            "message": f"Tool execution error: {str(e)}"
                        })
                
            except asyncio.TimeoutError:
                # Keep connection alive with heartbeat
                yield await sse_event("ping", {"timestamp": datetime.now().isoformat()})
            except Exception as e:
                yield await sse_event("error", {
                    "code": -32603,
                    "message": f"Stream error: {str(e)}"
                })
                break
    
    except Exception as e:
        yield await sse_event("error", {
            "code": -32603,
            "message": f"SSE connection error: {str(e)}"
        })
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]


@app.get("/")
async def root():
    return {
        "name": "Flight MCP Server (HTTP/SSE)",
        "version": "1.0.0",
        "transport": "sse",
        "endpoints": {
            "sse": "/sse",
            "tools": "/tools",
            "docs": "/docs"
        },
        "description": "MCP server for flight booking operations"
    }


@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint for MCP protocol communication"""
    global connection_counter
    connection_counter += 1
    connection_id = connection_counter
    
    active_connections[connection_id] = SSEConnection()
    
    return StreamingResponse(
        mcp_sse_stream(connection_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )


@app.post("/sse/message")
async def sse_message(connection_id: int, message: dict):
    """Send a message to an SSE connection"""
    if connection_id not in active_connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    await active_connections[connection_id].messages.put(message)
    return {"status": "queued"}


@app.get("/tools")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {"name": "search_flights", "description": "Search for flights"},
            {"name": "get_flight_details", "description": "Get flight details"},
            {"name": "create_booking", "description": "Create a booking"},
            {"name": "get_booking", "description": "Get booking details"},
            {"name": "cancel_booking", "description": "Cancel a booking"},
            {"name": "check_in", "description": "Check in to a flight"},
            {"name": "get_airport_info", "description": "Get airport information"},
            {"name": "get_flight_status", "description": "Get flight status"}
        ]
    }


@app.post("/tools/{tool_name}/call")
async def call_tool(tool_name: str, body: CallToolRequest):
    """Call a specific MCP tool via HTTP POST"""
    try:
        if tool_name == "search_flights":
            result = await search_flights(**body.arguments)
        elif tool_name == "get_flight_details":
            result = await get_flight_details(**body.arguments)
        elif tool_name == "create_booking":
            result = await create_booking(**body.arguments)
        elif tool_name == "get_booking":
            result = await get_booking(**body.arguments)
        elif tool_name == "cancel_booking":
            result = await cancel_booking(**body.arguments)
        elif tool_name == "check_in":
            result = await check_in(**body.arguments)
        elif tool_name == "get_airport_info":
            result = await get_airport_info(**body.arguments)
        elif tool_name == "get_flight_status":
            result = await get_flight_status(**body.arguments)
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        return {"status": "success", "result": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=os.getenv("ENV", "development") == "development"
    )
