"""
NEXUS Service - Calls NEXUS APIs for business intelligence.
JARVIS does NOT compute KPIs or store business data locally.
All business analytics come from NEXUS.
"""

import logging
from typing import Dict, Any, List, Optional

import httpx

from app.config import NexusConfig

LOGGER = logging.getLogger(__name__)


class NexusServiceError(Exception):
    """Error calling NEXUS API."""
    pass


class NexusService:
    """
    Service for calling NEXUS APIs.
    JARVIS consumes NEXUS intelligence - does not compute analytics.
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or NexusConfig.BASE_URL
        self.api_key = api_key or NexusConfig.API_KEY
        self.headers = NexusConfig.get_headers()
        self.timeout = 30.0

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to NEXUS API."""
        if not self.api_key:
            raise NexusServiceError("NEXUS_API_KEY not configured")

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json_data,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            LOGGER.error("NEXUS API error: %s %s", exc.response.status_code, exc.response.text)
            raise NexusServiceError(f"NEXUS API error: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            LOGGER.error("NEXUS request failed: %s", exc)
            raise NexusServiceError(f"NEXUS request failed: {exc}") from exc

    async def get_portfolio_overview(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get portfolio overview from NEXUS.
        Returns aggregated KPIs across all businesses.
        API: GET /api/v1/portfolio/overview
        """
        params = {}
        if user_id:
            params["user_id"] = user_id

        try:
            return self._request("GET", "/api/v1/portfolio/overview", params=params)
        except NexusServiceError:
            # Return empty structure if NEXUS unavailable
            LOGGER.warning("NEXUS unavailable, returning empty portfolio overview")
            return {
                "businesses": [],
                "total_businesses": 0,
                "summary": "NEXUS service unavailable",
            }

    async def get_business_insight(self, business_id: str) -> Dict[str, Any]:
        """
        Get detailed insight for a specific business from NEXUS.
        API: GET /api/v1/portfolio/business/{business_id}
        """
        try:
            return self._request("GET", f"/api/v1/portfolio/business/{business_id}")
        except NexusServiceError:
            LOGGER.warning("NEXUS unavailable for business insight: %s", business_id)
            return {
                "business_id": business_id,
                "error": "NEXUS service unavailable",
            }

    async def compare_businesses(self, entity_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple businesses from NEXUS.
        API: POST /api/v1/portfolio/comparison
        """
        try:
            return self._request(
                "POST",
                "/api/v1/portfolio/comparison",
                json_data={"entity_ids": entity_ids},
            )
        except NexusServiceError:
            LOGGER.warning("NEXUS unavailable for business comparison")
            return {
                "businesses": [],
                "comparison": {},
                "error": "NEXUS service unavailable",
            }

    async def get_alerts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get portfolio alerts from NEXUS.
        API: GET /api/v1/portfolio/alerts
        """
        params = {}
        if active_only:
            params["active_only"] = "true"

        try:
            response = self._request("GET", "/api/v1/portfolio/alerts", params=params)
            # Handle both list and dict responses
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "alerts" in response:
                return response["alerts"]
            return []
        except NexusServiceError:
            LOGGER.warning("NEXUS unavailable for alerts")
            return []

    async def get_alert_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent alert events from NEXUS.
        """
        try:
            response = self._request(
                "GET",
                "/api/v1/portfolio/alerts/events",
                params={"limit": limit},
            )
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "events" in response:
                return response["events"]
            return []
        except NexusServiceError:
            LOGGER.warning("NEXUS unavailable for alert events")
            return []
    
    async def get_revenue_trends(self, entity_id: Optional[str] = None, months: int = 6) -> Dict[str, Any]:
        """
        Get revenue trends from NEXUS.
        API: GET /api/v1/portfolio/revenue-trends
        """
        try:
            params = {"months": months}
            if entity_id:
                params["entity_id"] = entity_id
            return self._request("GET", "/api/v1/portfolio/revenue-trends", params=params)
        except NexusServiceError:
            LOGGER.warning("NEXUS unavailable for revenue trends")
            return {"trends": [], "period_months": months}
    
    async def get_risk_heatmap(self) -> Dict[str, Any]:
        """
        Get risk heatmap from NEXUS.
        API: GET /api/v1/portfolio/risk-heatmap
        """
        try:
            return self._request("GET", "/api/v1/portfolio/risk-heatmap")
        except NexusServiceError:
            LOGGER.warning("NEXUS unavailable for risk heatmap")
            return {"entities": []}
    
    async def get_cash_flow_analysis(self) -> Dict[str, Any]:
        """
        Get cash flow analysis from NEXUS.
        API: GET /api/v1/portfolio/cash-flow
        """
        try:
            return self._request("GET", "/api/v1/portfolio/cash-flow")
        except NexusServiceError:
            LOGGER.warning("NEXUS unavailable for cash flow analysis")
            return {
                "total_cash": 0.0,
                "average_runway_months": 0.0,
                "critical_count": 0,
                "warning_count": 0,
                "healthy_count": 0,
                "critical_entities": [],
                "recommendations": ["NEXUS service unavailable"]
            }

    async def get_ad_performance(self) -> Dict[str, Any]:
        """
        Get aggregated ad performance metrics from NEXUS (AdAI data).
        This enables Nexus to supervise AdAI and report to Jarvis.
        API: GET /api/v1/portfolio/ad-performance
        """
        try:
            return self._request("GET", "/api/v1/portfolio/ad-performance")
        except NexusServiceError:
            LOGGER.warning("NEXUS unavailable for ad performance")
            return {
                "total_spend_today": 0.0,
                "total_spend_mtd": 0.0,
                "total_conversions": 0,
                "average_cpa": 0.0,
                "average_roas": 0.0,
                "top_campaigns": [],
                "at_risk_campaigns": [],
                "pending_approvals": 0,
                "platform_breakdown": {},
                "error": "NEXUS service unavailable"
            }

