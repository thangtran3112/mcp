"""
Flight tracking and price alert tools
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from data.mock_data import db
from mcp_app import mcp


@mcp.tool()
async def track_flight(
    flight_id: str,
    notify_changes: bool = True
) -> Dict[str, Any]:
    """
    Track a flight in real-time and get status updates.
    
    Args:
        flight_id: The flight ID to track
        notify_changes: Whether to enable notifications for changes
    
    Returns:
        Real-time flight status and tracking information
    """
    try:
        flight = db.get_flight(flight_id)
        if not flight:
            return {
                "success": False,
                "error": f"Flight {flight_id} not found"
            }
        
        # Calculate flight progress (mock)
        now = datetime.now()
        total_duration = (flight.arrival - flight.departure).total_seconds()
        elapsed = (now - flight.departure).total_seconds()
        
        if elapsed < 0:
            progress = 0
            phase = "Not Departed"
        elif elapsed > total_duration:
            progress = 100
            phase = "Arrived"
        else:
            progress = min(100, (elapsed / total_duration) * 100)
            if progress < 10:
                phase = "Taxiing/Takeoff"
            elif progress < 90:
                phase = "In Flight"
            else:
                phase = "Descending/Landing"
        
        # Mock position data
        tracking_data = {
            "success": True,
            "flight_id": flight_id,
            "flight_number": flight.flight_number,
            "airline": flight.airline,
            "route": {
                "origin": flight.origin,
                "destination": flight.destination
            },
            "schedule": {
                "scheduled_departure": flight.departure.isoformat(),
                "scheduled_arrival": flight.arrival.isoformat(),
                "actual_departure": flight.departure.isoformat() if progress > 0 else None,
                "estimated_arrival": flight.arrival.isoformat()
            },
            "status": {
                "current_status": flight.status.value,
                "phase": phase,
                "progress_percentage": round(progress, 1),
                "on_time": True
            },
            "position": {
                "altitude_feet": 35000 if 10 < progress < 90 else 0,
                "speed_mph": 550 if 10 < progress < 90 else 0,
                "heading": "East" if flight.origin < flight.destination else "West"
            },
            "gate_info": {
                "departure_gate": flight.gate,
                "departure_terminal": flight.terminal,
                "arrival_gate": "TBD"
            },
            "notifications_enabled": notify_changes,
            "last_updated": datetime.now().isoformat()
        }
        
        return tracking_data
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@mcp.tool()
async def price_alert(
    origin: str,
    destination: str,
    departure_date: str,
    target_price: float,
    seat_class: str = "economy",
    alert_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Set up a price alert for a specific route and date.
    
    Args:
        origin: Origin airport code
        destination: Destination airport code  
        departure_date: Target departure date (YYYY-MM-DD)
        target_price: Alert when price drops below this amount
        seat_class: Class of service to monitor
        alert_email: Email address for notifications
    
    Returns:
        Price alert confirmation and current prices
    """
    try:
        # Parse date
        dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
        
        # Search for current prices
        from models import SeatClass
        seat_class_enum = SeatClass(seat_class.lower())
        
        flights = db.search_flights(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=dep_date,
            passengers=1,
            seat_class=seat_class_enum
        )
        
        if not flights:
            current_lowest = None
        else:
            prices = [getattr(f.price, seat_class.lower()) for f in flights]
            current_lowest = min(prices)
        
        # Create alert (mock - would store in database)
        alert_id = f"PA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        alert_data = {
            "success": True,
            "alert_id": alert_id,
            "route": f"{origin.upper()} → {destination.upper()}",
            "departure_date": departure_date,
            "seat_class": seat_class,
            "target_price": target_price,
            "current_lowest_price": current_lowest,
            "price_difference": current_lowest - target_price if current_lowest else None,
            "alert_status": "Active",
            "notification_email": alert_email or "Not set",
            "created_at": datetime.now().isoformat(),
            "expires_at": (dep_date - timedelta(days=1)).isoformat(),
            "tips": [
                "Prices typically drop 6-8 weeks before departure",
                "Tuesday and Wednesday often have lower prices",
                "Consider flexible dates for better deals",
                "Book early morning or late night flights for savings"
            ]
        }
        
        if current_lowest and current_lowest <= target_price:
            alert_data["immediate_action"] = {
                "message": "Current price is already at or below your target!",
                "current_price": current_lowest,
                "recommendation": "Book now to secure this price"
            }
        
        return alert_data
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
