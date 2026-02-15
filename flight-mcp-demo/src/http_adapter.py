from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys
from typing import Optional, Any, Dict

# Ensure src is on path
sys.path.insert(0, os.path.dirname(__file__))

import server

app = FastAPI(
    title="Flight MCP HTTP Adapter",
    version="1.0.0"
)


class SearchBody(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    seat_class: str = "economy"
    nonstop_only: Optional[bool] = False
    max_price: Optional[float] = None
    preferred_airlines: Optional[list[str]] = None


async def _call_tool(maybe_tool, /, **kwargs) -> Any:
    """
    Call either a FunctionTool-like object (has `.fn`) or a coroutine function.
    """
    tool_fn = None
    # If it's a FunctionTool (fastmcp.tools.tool.FunctionTool), it exposes `.fn`
    if hasattr(maybe_tool, "fn"):
        tool_fn = getattr(maybe_tool, "fn")
    else:
        tool_fn = maybe_tool

    if not callable(tool_fn):
        raise TypeError("Tool is not callable")

    # Call and await the coroutine
    result = tool_fn(**kwargs)
    if hasattr(result, "__await__"):
        return await result
    return result


@app.post("/search")
async def http_search(body: SearchBody):
    try:
        return await _call_tool(server.search_flights, **body.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/flight/{flight_id}")
async def http_flight(flight_id: str):
    try:
        return await _call_tool(server.get_flight_details, flight_id=flight_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Booking endpoints
class CreateBookingBody(BaseModel):
    flight_id: str
    passengers: list
    seat_class: str = "economy"
    payment_token: str = "mock-payment-token"
    add_insurance: bool = False
    special_requests: Optional[str] = None


@app.post("/booking")
async def http_create_booking(body: CreateBookingBody):
    try:
        return await _call_tool(server.create_booking, **body.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/booking/{booking_id}")
async def http_get_booking(booking_id: str, email: Optional[str] = None):
    try:
        return await _call_tool(server.get_booking, booking_id=booking_id, email=email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/booking/{booking_id}/cancel")
async def http_cancel_booking(booking_id: str, reason: Optional[str] = None):
    try:
        return await _call_tool(server.cancel_booking, booking_id=booking_id, reason=reason)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CheckInBody(BaseModel):
    booking_id: str
    passenger_ids: Optional[list[str]] = None
    seat_preferences: Optional[list[Dict[str, str]]] = None


@app.post("/checkin")
async def http_check_in(body: CheckInBody):
    try:
        return await _call_tool(server.check_in, **body.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/airport/{code}")
async def http_airport_info(code: str):
    try:
        return await _call_tool(server.get_airport_info, code=code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{flight_id}")
async def http_flight_status(flight_id: str):
    try:
        return await _call_tool(server.get_flight_status, flight_id=flight_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Prompt endpoints (simple wrappers)
class PromptBody(BaseModel):
    travel_details: str
    preferences: Optional[str] = None


@app.post("/prompt/find_best_flight")
async def http_find_best(prompt: PromptBody):
    try:
        return await _call_tool(server.find_best_flight, travel_details=prompt.travel_details, preferences=prompt.preferences or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompt/handle_disruption")
async def http_handle_disruption(body: dict):
    try:
        return await _call_tool(server.handle_disruption, booking_info=body.get("booking_info",""), disruption_type=body.get("disruption_type",""))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
