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

| Component     | Purpose                | Direction   | Example                           |
| ------------- | ---------------------- | ----------- | --------------------------------- |
| **Tools**     | Execute actions        | AI → Server | Book a flight, cancel reservation |
| **Resources** | Read data              | AI ← Server | Get airport info, view policies   |
| **Prompts**   | Conversation templates | Server → AI | Travel planning workflow          |

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

## Resource URIs

### URI Structure

MCP resource URIs follow a custom scheme pattern similar to web URLs:

```
scheme://path/with/{parameters}
```

| Part           | Example                              | Purpose                                     |
| -------------- | ------------------------------------ | ------------------------------------------- |
| **Scheme**     | `flight://`, `weather://`, `info://` | Groups related resources (like a namespace) |
| **Path**       | `airports/`, `forecast/`             | Identifies the resource type                |
| **Parameters** | `{code}`, `{email}`                  | Dynamic values passed to the function       |

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

| URI Pattern                          | Parameters      | Example Request                       |
| ------------------------------------ | --------------- | ------------------------------------- |
| `flight://airports/{code}`           | `code`          | `flight://airports/SFO`               |
| `bookings://history/{email}`         | `email`         | `bookings://history/john@example.com` |
| `travel://tips/{destination}`        | `destination`   | `travel://tips/NYC`                   |
| `weather://forecast/{airport_code}`  | `airport_code`  | `weather://forecast/JFK`              |
| `info://seat-maps/{flight_number}`   | `flight_number` | `info://seat-maps/UA123`              |
| `info://baggage-policies`            | _(none)_        | `info://baggage-policies`             |
| `loyalty://programs`                 | _(none)_        | `loyalty://programs`                  |
| `covid://policies`                   | _(none)_        | `covid://policies`                    |
| `airlines://policies/{airline_code}` | `airline_code`  | `airlines://policies/UA`              |

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

| Transport           | Use Case                       | URL Example                 |
| ------------------- | ------------------------------ | --------------------------- |
| **stdio**           | Local development, CLI tools   | N/A (stdin/stdout)          |
| **Streamable HTTP** | Remote servers, AWS deployment | `http://localhost:8000/mcp` |
| ~~SSE~~             | _Deprecated_                   | N/A                         |

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

| Endpoint  | Method | Purpose                                          |
| --------- | ------ | ------------------------------------------------ |
| `/mcp`    | POST   | Main MCP endpoint (initialize, tools/list, etc.) |
| `/health` | GET    | Health check                                     |

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

---

## Appendix: Prompts

> **Note:** Prompts are the least commonly used MCP primitive. Most AI interactions rely on Tools and Resources. Prompts are optional and primarily useful for standardizing common workflows.

### What Are Prompts?

Prompts are **pre-built conversation templates** that provide structured guidance for specific scenarios. Unlike Tools (which execute actions) or Resources (which provide data), Prompts return formatted text that helps guide the AI's interaction with the user.

```python
@mcp.prompt()
async def smart_booking_assistant() -> str:
    """General intelligent booking assistant introduction."""
    return """Welcome to your AI-powered flight booking assistant!
    
I can help you with:
✈️ Flight Search & Booking
🎫 Booking Management
📊 Real-Time Information
...
"""
```

### Characteristics

| Aspect | Description |
|--------|-------------|
| **Purpose** | Provide structured conversation starters or guidance |
| **Direction** | Server → AI (AI receives the template text) |
| **Side Effects** | None - purely text generation |
| **Parameters** | Can accept context to customize the response |
| **Return Value** | Formatted string (often multi-line) |

### How Prompts Differ from Tools and Resources

| Feature | Tools | Resources | Prompts |
|---------|-------|-----------|---------|
| **Action** | Execute operations | Read data | Generate guidance text |
| **Side Effects** | Yes (can modify state) | No | No |
| **Use Case** | Book flight, cancel booking | Get airport info | Guide booking workflow |
| **Invocation** | `tools/call` | `resources/read` | `prompts/get` |

### When to Use Prompts

Prompts are useful for:

1. **Standardizing workflows** - Ensure consistent step-by-step guidance
2. **Onboarding interactions** - Welcome messages with capabilities overview
3. **Complex multi-step processes** - Booking flows, trip planning
4. **Specialized scenarios** - Accessibility needs, group bookings

### Prompts in This Project

Located in `src/prompts/templates.py`:

| Prompt Name | Parameters | Purpose |
|-------------|------------|---------|
| `complete_booking` | `flight_search_criteria`, `passenger_count` | Guide through booking process step-by-step |
| `trip_planning` | `cities`, `date_range` | Plan multi-city trips with optimal routing |
| `loyalty_optimization` | `member_status`, `upcoming_trips` | Maximize loyalty program benefits |
| `accessibility_booking` | `assistance_needed`, `special_requirements` | Handle accessibility requirements |
| `handle_group_travel` | `group_size`, `travel_purpose` | Coordinate group bookings |
| `smart_booking_assistant` | *(none)* | General welcome and capabilities overview |

### Example: Complete Booking Prompt

```python
@mcp.prompt()
async def complete_booking(
    flight_search_criteria: dict,
    passenger_count: int
) -> str:
    """Guide through the entire booking process step by step."""
    return f"""I'll help you complete your flight booking for {passenger_count} passenger(s).

Based on your search criteria:
- Route: {flight_search_criteria.get('origin')} → {flight_search_criteria.get('destination')}
- Departure: {flight_search_criteria.get('departure_date')}
- Return: {flight_search_criteria.get('return_date', 'One-way trip')}

Here's what we'll do:
1. Search for the best flights matching your criteria
2. Compare options based on price, schedule, and amenities
3. Select your preferred flights
4. Enter passenger information
5. Choose seats (optional)
6. Add any extras (baggage, meals, insurance)
7. Complete payment
8. Receive confirmation and boarding passes

Let me start by searching for available flights..."""
```

### Example: Accessibility Booking Prompt

This prompt shows how prompts can handle specialized scenarios:

```python
@mcp.prompt()
async def accessibility_booking(
    assistance_needed: List[str],
    special_requirements: Optional[str] = None
) -> str:
    """Handle bookings with accessibility requirements."""
    assistance_str = ", ".join(assistance_needed)
    return f"""I'll ensure your travel needs are fully accommodated.

Assistance requested: {assistance_str}
{f'Special requirements: {special_requirements}' if special_requirements else ''}

Services available:
- Wheelchair assistance (curb to gate)
- Priority boarding
- Assistance animals accommodation
- Medical equipment handling
- Accessible seating assignments
- Personal safety briefings

Important notes:
- Arrive 3 hours early for smooth processing
- Bring documentation for service animals
- Medical equipment flies free
- Accessibility services are complimentary

Let me search for flights and arrange your assistance..."""
```

### How Prompts Are Invoked

**1. AI Client Lists Available Prompts**

```json
// Request
{"method": "prompts/list"}

// Response
{
  "prompts": [
    {"name": "complete_booking", "description": "Guide through booking process"},
    {"name": "smart_booking_assistant", "description": "General assistant intro"},
    ...
  ]
}
```

**2. AI Client Gets a Prompt**

```json
// Request
{
  "method": "prompts/get",
  "params": {
    "name": "complete_booking",
    "arguments": {
      "flight_search_criteria": {"origin": "SFO", "destination": "JFK", "departure_date": "2026-03-15"},
      "passenger_count": 2
    }
  }
}

// Response
{
  "messages": [
    {
      "role": "assistant",
      "content": {
        "type": "text",
        "text": "I'll help you complete your flight booking for 2 passenger(s).\n\nBased on your search criteria:\n- Route: SFO → JFK\n..."
      }
    }
  ]
}
```

### Testing Prompts

In MCP Inspector, navigate to the **Prompts** tab to see and test available prompts. You can provide argument values and see the generated text.

### Why Prompts Are Less Common

Most AI interactions can be handled with:
- **Tools** for actions (book, cancel, modify)
- **Resources** for data (airport info, policies, status)

Prompts add value when you need:
- Consistent multi-step workflows
- Standardized onboarding experiences
- Context-specific guidance templates

For simple interactions, the AI can generate appropriate responses without needing pre-built templates.
