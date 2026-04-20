"""
FlightAware service for flight tracking and status.
"""

import logging
import os
from typing import Dict, List, Optional

import requests

LOGGER = logging.getLogger(__name__)

FLIGHTAWARE_API_KEY = os.getenv("FLIGHTAWARE_API_KEY")
FLIGHTAWARE_API_URL = "https://aeroapi.flightaware.com/aeroapi"


class FlightAwareService:
    """Service for tracking flights via FlightAware."""
    
    def __init__(self):
        self.api_key = FLIGHTAWARE_API_KEY
        self.is_configured = bool(self.api_key)
        
        if not self.is_configured:
            LOGGER.warning("FlightAware API key not configured. Set FLIGHTAWARE_API_KEY")
        else:
            LOGGER.info("FlightAware service configured")
    
    def get_flight_status(self, flight_number: str, date: Optional[str] = None) -> Dict[str, any]:
        """
        Get flight status.
        
        Args:
            flight_number: Flight number (e.g., "UA123")
            date: Optional date (YYYY-MM-DD), defaults to today
        
        Returns:
            Dict with flight status
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "FlightAware not configured"
            }
        
        try:
            headers = {
                "x-apikey": self.api_key
            }
            
            url = f"{FLIGHTAWARE_API_URL}/flights/{flight_number}"
            if date:
                url += f"?start={date}"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            flight_data = response.json()
            LOGGER.info(f"Flight status retrieved: {flight_number}")
            return {
                "success": True,
                "flight": flight_data
            }
        except Exception as e:
            LOGGER.error(f"Failed to get flight status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def track_flight(self, flight_number: str) -> Dict[str, any]:
        """
        Track a flight and get real-time updates.
        
        Args:
            flight_number: Flight number
        
        Returns:
            Dict with tracking information
        """
        return self.get_flight_status(flight_number)


# Global instance
flightaware_service = FlightAwareService()

