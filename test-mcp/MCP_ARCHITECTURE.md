# MCP Architecture Guide

This document explains the Model Context Protocol (MCP) architecture used in this project, covering Tools, Resources, Prompts, and URI patterns.

---

## Table of Contents

1. [Overview](#overview)
2. [MCP Components](#mcp-components)
   - [Tools](#tools)
   - [Resources](#resources)
   - [Prompts](#prompts)
3. [Resource URIs](#resource-uris)
   - [URI Structure](#uri-structure)
   - [How URIs Are Created](#how-uris-are-created)
   - [URI Patterns in This Project](#uri-patterns-in-this-project)
   - [How URIs Are Used](#how-uris-are-used)
   - [Static vs Dynamic Resources](#static-vs-dynamic-resources)
4. [Transport Methods](#transport-methods)
5. [Architecture Diagram](#architecture-diagram)

---

## Overview

MCP (Model Context Protocol) is a protocol that allows AI assistants to interact with external systems through a standardized interface. It provides three main primitives:

| Component | Purpose | Direction | Example |
|-----------|---------|-----------|---------|
| **Tools** | Execute actions | AI → Server | Book a flight, cancel reservation |
| **Resources** | Read data | AI ← Server | Get airport info, view policies |
| **Prompts** | Conversation templates | Server → AI | Travel planning workflow |

---

## MCP Components

### Tools

Tools are **actions** the AI can execute. They may have side effects (modify data, call APIs, etc.).

```python
@mcp.tool()
async def book_flight(flight_number: str, passenger_name: str) -> Dict:
    """Book a flight for a passenger."""
    # Creates a booking - has side effects
    return {"confirmation": "ABC123", "status": "confirmed"}
```

**Characteristics:**
- Can modify state
- May have side effects
- Return operation results
- Located in `src/tools/`

### Resources

Resources are **read-only data endpoints**. They provide information without side effects.

```python
@mcp.resource("flight://airports/{code}")
async def get_airport_info(code: str) -> Dict:
    """Get information about an airport."""
    # Read-only - no side effects
    return airports[code.upper()]
```

**Characteristics:**
- Read-only (no side effects)
- Accessed via URI patterns
- Return data/information
- Located in `src/resources/`

### Prompts

Prompts are **pre-built conversation templates** that guide AI interactions.

```python
@mcp.prompt()
def travel_planning_prompt(destination: str, dates: str) -> str:
    """Generate a travel planning conversation starter."""
    return f"Help me plan a trip to {destination} on {dates}..."
```

**Characteristics:**
- Template-based
- Guide conversation flow
- No execution logic
- Located in `src/prompts/`

---

## Resource URIs

### URI Structure

MCP resource URIs follow a custom scheme pattern similar to web URLs:

```
scheme://path/with/{parameters}
```

| Part | Example | Purpose |
|------|---------|---------|
| **Scheme** | `flight://`, `weather://`, `info://` | Groups related resources (like a namespace) |
| **Path** | `airports/`, `forecast/` | Identifies the resource type |
| **Parameters** | `{code}`, `{email}` | Dynamic values passed to the function |

### How URIs Are Created

You define the URI pattern in the `@mcp.resource()` decorator:

```python
@mcp.resource("flight://airports/{code}")
async def get_airport_info(code: str) -> Dict[str, Any]:
    # The {code} in the URI becomes the function parameter
    return airports[code.upper()]
```

The parameter name in the URI (`{code}`) must match the function parameter name (`code: str`).

### URI Patterns in This Project

| URI Pattern | Parameters | Example Request |
|-------------|------------|-----------------|
| `flight://airports/{code}` | `code` | `flight://airports/SFO` |
| `bookings://history/{email}` | `email` | `bookings://history/john@example.com` |
| `travel://tips/{destination}` | `destination` | `travel://tips/NYC` |
| `weather://forecast/{airport_code}` | `airport_code` | `weather://forecast/JFK` |
| `info://seat-maps/{flight_number}` | `flight_number` | `info://seat-maps/UA123` |
| `info://baggage-policies` | *(none)* | `info://baggage-policies` |
| `loyalty://programs` | *(none)* | `loyalty://programs` |
| `covid://policies` | *(none)* | `covid://policies` |
| `airlines://policies/{airline_code}` | `airline_code` | `airlines://policies/UA` |

### How URIs Are Used

**1. AI Client Discovers Resources**

When an AI connects, it can list available resources:

```json
// Request
{"method": "resources/list"}

// Response
{
  "resources": [
    {"uri": "flight://airports/{code}", "name": "Airport Info"},
    {"uri": "info://baggage-policies", "name": "Baggage Policies"},
    ...
  ]
}
```

**2. AI Client Reads a Resource**

The AI fills in parameters and requests the data:

```json
// Request
{"method": "resources/read", "params": {"uri": "flight://airports/SFO"}}

// Response  
{
  "code": "SFO",
  "name": "San Francisco International Airport",
  "city": "San Francisco",
  ...
}
```

**Visual Flow:**

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI Assistant                            │
├─────────────────────────────────────────────────────────────────┤
│ User: "What terminals does SFO have?"                           │
│                                                                 │
│ AI thinks: I need airport info. Let me read the resource.       │
│            URI template: flight://airports/{code}                │
│            Fill in: flight://airports/SFO                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Server                                 │
├─────────────────────────────────────────────────────────────────┤
│ Receives: resources/read, uri="flight://airports/SFO"           │
│                                                                 │
│ Matches pattern: flight://airports/{code}                        │
│ Extracts: code = "SFO"                                          │
│ Calls: get_airport_info(code="SFO")                             │
│                                                                 │
│ Returns: { "terminals": ["1", "2", "3", "International"], ... }  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ AI: "SFO has 4 terminals: 1, 2, 3, and International."           │
└─────────────────────────────────────────────────────────────────┘
```

### Static vs Dynamic Resources

**Static** (no parameters) - Returns the same data every time:

```python
@mcp.resource("info://baggage-policies")
async def baggage_policies() -> Dict:
    return { ... }  # Always same policies
```

**Dynamic** (with parameters) - Returns data based on input:

```python
@mcp.resource("flight://airports/{code}")
async def get_airport_info(code: str) -> Dict:
    return airports[code]  # Different data per airport
```

### Scheme Naming Conventions

The scheme names are arbitrary - you choose them for clarity:

```python
# Good - descriptive schemes
@mcp.resource("flight://airports/{code}")      # Flight-related
@mcp.resource("weather://forecast/{code}")     # Weather-related
@mcp.resource("bookings://history/{email}")    # Booking-related
@mcp.resource("info://baggage-policies")       # General info

# Also valid - single scheme for everything
@mcp.resource("api://airports/{code}")
@mcp.resource("api://weather/{code}")
@mcp.resource("api://baggage-policies")
```

---

## Transport Methods

MCP supports multiple transport methods:

| Transport | Use Case | URL Example |
|-----------|----------|-------------|
| **stdio** | Local development, CLI tools | N/A (stdin/stdout) |
| **Streamable HTTP** | Remote servers, AWS deployment | `http://localhost:8000/mcp` |
| ~~SSE~~ | *Deprecated* | N/A |

### Starting the Server

```bash
# Interactive mode
./start.sh

# Direct commands
./start.sh stdio              # STDIO transport
./start.sh http               # Streamable HTTP on port 8000
./start.sh inspector          # MCP Inspector (debug UI)
```

### Streamable HTTP Endpoints

When running with `streamable-http` transport:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/mcp` | POST | Main MCP endpoint (initialize, tools/list, etc.) |
| `/health` | GET | Health check |

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                           MCP Server                                 │
│                        (test-mcp package)                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │   Tools     │    │  Resources  │    │   Prompts   │              │
│  │ (actions)   │    │ (read-only) │    │ (templates) │              │
│  ├─────────────┤    ├─────────────┤    ├─────────────┤              │
│  │ book_flight │    │ airports/   │    │ travel_plan │              │
│  │ cancel_book │    │ weather/    │    │ booking_    │              │
│  │ track_flight│    │ bookings/   │    │   assistant │              │
│  │ price_alert │    │ baggage/    │    │ flight_     │              │
│  │ ...         │    │ ...         │    │   search    │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│         │                  │                  │                      │
│         └──────────────────┼──────────────────┘                      │
│                            │                                         │
│                    ┌───────▼───────┐                                 │
│                    │   mcp_app.py  │                                 │
│                    │  (FastMCP)    │                                 │
│                    └───────┬───────┘                                 │
│                            │                                         │
│              ┌─────────────┴─────────────┐                           │
│              │                           │                           │
│       ┌──────▼──────┐            ┌───────▼──────┐                    │
│       │    STDIO    │            │  Streamable  │                    │
│       │  Transport  │            │    HTTP      │                    │
│       └─────────────┘            └──────────────┘                    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         AI Clients                                   │
├──────────────────────────────────────────────────────────────────────┤
│  • Cursor IDE (stdio)                                                │
│  • Claude Desktop (stdio)                                            │
│  • MCP Inspector (HTTP)                                              │
│  • Postman (HTTP)                                                    │
│  • Custom applications (HTTP)                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
test-mcp/
├── src/
│   ├── mcp_app.py           # Shared MCP instance
│   ├── server.py            # Main entry point
│   ├── tools/               # Tool definitions
│   │   ├── tracking.py      # Flight tracking tools
│   │   ├── services.py      # Service-related tools
│   │   └── group.py         # Group booking tools
│   ├── resources/           # Resource definitions
│   │   └── flight_resources.py
│   ├── prompts/             # Prompt templates
│   │   └── templates.py
│   ├── models/              # Data models
│   └── data/                # Mock data
├── start.sh                 # Interactive startup script
├── requirements.txt         # Python dependencies
└── README.md                # Usage documentation
```

---

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Inspector](https://www.npmjs.com/package/@modelcontextprotocol/inspector)
