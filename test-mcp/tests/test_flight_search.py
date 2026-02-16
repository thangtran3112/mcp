"""
Tests for flight search functionality
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import search_flights, get_flight_details
from models import SeatClass


@pytest.mark.asyncio
async def test_search_flights_basic():
    """Test basic flight search functionality."""
    result = await search_flights(
        origin="SFO",
        destination="JFK",
        departure_date=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        passengers=1,
        seat_class="economy"
    )
    
    assert result["success"] is True
    assert "outbound_flights" in result
    assert len(result["outbound_flights"]) > 0
    assert result["search_criteria"]["origin"] == "SFO"
    assert result["search_criteria"]["destination"] == "JFK"


@pytest.mark.asyncio
async def test_search_flights_round_trip():
    """Test round trip flight search."""
    departure = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
    result = await search_flights(
        origin="SFO",
        destination="JFK",
        departure_date=departure,
        return_date=return_date,
        passengers=2,
        seat_class="business"
    )
    
    assert result["success"] is True
    assert "return_flights" in result
    assert result["return_flights"] is not None
    assert len(result["return_flights"]) > 0


@pytest.mark.asyncio
async def test_search_flights_invalid_date():
    """Test flight search with invalid date format."""
    result = await search_flights(
        origin="SFO",
        destination="JFK",
        departure_date="invalid-date",
        passengers=1
    )
    
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio 
async def test_get_flight_details():
    """Test getting flight details."""
    # First search for a flight
    search_result = await search_flights(
        origin="SFO",
        destination="JFK",
        departure_date=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        passengers=1
    )
    
    assert search_result["success"] is True
    assert len(search_result["outbound_flights"]) > 0
    
    # Get details for the first flight
    flight_id = search_result["outbound_flights"][0]["flight_id"]
    details_result = await get_flight_details(flight_id)
    
    assert details_result["success"] is True
    assert "flight" in details_result
    assert details_result["flight"]["flight_id"] == flight_id
    assert "airport_info" in details_result["flight"]


@pytest.mark.asyncio
async def test_get_flight_details_invalid():
    """Test getting details for non-existent flight."""
    result = await get_flight_details("INVALID-FLIGHT-ID")
    
    assert result["success"] is False
    assert "error" in result
    assert "not found" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])