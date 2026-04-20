"""
Meta Marketing API Client
Handles communication with Meta (Facebook/Instagram) Ads API.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

LOGGER = logging.getLogger(__name__)


class MetaCampaignObjective(str, Enum):
    """Meta campaign objectives."""
    AWARENESS = "OUTCOME_AWARENESS"
    TRAFFIC = "OUTCOME_TRAFFIC"
    ENGAGEMENT = "OUTCOME_ENGAGEMENT"
    LEADS = "OUTCOME_LEADS"
    APP_PROMOTION = "OUTCOME_APP_PROMOTION"
    SALES = "OUTCOME_SALES"


class MetaCampaignStatus(str, Enum):
    """Meta campaign status values."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"


@dataclass
class MetaCampaign:
    """Meta campaign representation."""
    id: str
    name: str
    status: MetaCampaignStatus
    objective: MetaCampaignObjective
    daily_budget: Optional[float] = None
    lifetime_budget: Optional[float] = None
    spend: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    created_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "objective": self.objective.value,
            "daily_budget": self.daily_budget,
            "lifetime_budget": self.lifetime_budget,
            "metrics": {
                "spend": round(self.spend, 2),
                "impressions": self.impressions,
                "clicks": self.clicks,
                "conversions": self.conversions,
                "ctr": round((self.clicks / self.impressions * 100) if self.impressions > 0 else 0, 2),
                "cpc": round((self.spend / self.clicks) if self.clicks > 0 else 0, 2),
                "cpa": round((self.spend / self.conversions) if self.conversions > 0 else 0, 2),
            },
            "created_time": self.created_time.isoformat() if self.created_time else None,
        }


class MetaAdsClient:
    """
    Client for Meta Marketing API.

    Handles:
    - Campaign CRUD operations
    - Ad set management
    - Creative management
    - Insights and reporting
    """

    API_VERSION = "v18.0"
    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        access_token: Optional[str] = None,
        ad_account_id: Optional[str] = None,
    ):
        """
        Initialize Meta Ads client.

        Args:
            access_token: Meta access token (falls back to env var)
            ad_account_id: Ad account ID (falls back to env var)
        """
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = ad_account_id or os.getenv("META_AD_ACCOUNT_ID")

        # Normalize ad account ID format
        if self.ad_account_id and not self.ad_account_id.startswith("act_"):
            self.ad_account_id = f"act_{self.ad_account_id}"

    @property
    def is_configured(self) -> bool:
        """Check if Meta API is configured."""
        return bool(self.access_token and self.ad_account_id)

    def _get_url(self, endpoint: str) -> str:
        """Build full API URL."""
        return f"{self.BASE_URL}/{self.API_VERSION}/{endpoint}"

    def _get_params(self, **kwargs) -> Dict[str, Any]:
        """Build request params with access token."""
        params = {"access_token": self.access_token}
        params.update(kwargs)
        return params

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make API request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body

        Returns:
            API response data
        """
        if not self.is_configured:
            LOGGER.warning("Meta API not configured")
            return {"error": "Meta API not configured"}

        try:
            import httpx

            url = self._get_url(endpoint)
            all_params = self._get_params(**(params or {}))

            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=all_params)
                elif method.upper() == "POST":
                    response = await client.post(url, params=all_params, json=data)
                else:
                    response = await client.request(method, url, params=all_params, json=data)

                response.raise_for_status()
                return response.json()

        except ImportError:
            LOGGER.warning("httpx not installed for Meta API calls")
            return {"error": "httpx not installed"}
        except Exception as e:
            LOGGER.error(f"Meta API request failed: {e}")
            return {"error": str(e)}

    # ==================== Campaign Operations ====================

    async def get_campaigns(
        self,
        status: Optional[MetaCampaignStatus] = None,
        limit: int = 100,
    ) -> List[MetaCampaign]:
        """
        Get campaigns for the ad account.

        Args:
            status: Filter by status
            limit: Maximum campaigns to return

        Returns:
            List of MetaCampaign objects
        """
        if not self.is_configured:
            return self._get_mock_campaigns(status)

        endpoint = f"{self.ad_account_id}/campaigns"
        params = {
            "fields": "id,name,status,objective,daily_budget,lifetime_budget,created_time",
            "limit": limit,
        }

        if status:
            params["effective_status"] = [status.value]

        result = await self._request("GET", endpoint, params=params)

        if "error" in result:
            LOGGER.error(f"Failed to get campaigns: {result['error']}")
            return []

        campaigns = []
        for item in result.get("data", []):
            try:
                campaigns.append(self._parse_campaign(item))
            except Exception as e:
                LOGGER.warning(f"Failed to parse campaign: {e}")

        return campaigns

    async def get_campaign(self, campaign_id: str) -> Optional[MetaCampaign]:
        """Get a single campaign by ID."""
        if not self.is_configured:
            return None

        params = {
            "fields": "id,name,status,objective,daily_budget,lifetime_budget,created_time"
        }

        result = await self._request("GET", campaign_id, params=params)

        if "error" in result:
            return None

        return self._parse_campaign(result)

    async def create_campaign(
        self,
        name: str,
        objective: MetaCampaignObjective,
        status: MetaCampaignStatus = MetaCampaignStatus.PAUSED,
        daily_budget: Optional[float] = None,
        special_ad_categories: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            objective: Campaign objective
            status: Initial status (default PAUSED)
            daily_budget: Daily budget in cents
            special_ad_categories: Special categories (HOUSING, CREDIT, etc.)

        Returns:
            Campaign ID or None on failure
        """
        if not self.is_configured:
            LOGGER.warning("Cannot create campaign: Meta API not configured")
            return None

        endpoint = f"{self.ad_account_id}/campaigns"
        data = {
            "name": name,
            "objective": objective.value,
            "status": status.value,
            "special_ad_categories": special_ad_categories or [],
        }

        if daily_budget:
            # Meta expects budget in cents
            data["daily_budget"] = int(daily_budget * 100)

        result = await self._request("POST", endpoint, data=data)

        if "error" in result:
            LOGGER.error(f"Failed to create campaign: {result['error']}")
            return None

        return result.get("id")

    async def update_campaign_status(
        self,
        campaign_id: str,
        status: MetaCampaignStatus
    ) -> bool:
        """Update campaign status."""
        if not self.is_configured:
            return False

        result = await self._request(
            "POST",
            campaign_id,
            data={"status": status.value}
        )

        return "error" not in result

    async def update_campaign_budget(
        self,
        campaign_id: str,
        daily_budget: float
    ) -> bool:
        """Update campaign daily budget."""
        if not self.is_configured:
            return False

        result = await self._request(
            "POST",
            campaign_id,
            data={"daily_budget": int(daily_budget * 100)}
        )

        return "error" not in result

    # ==================== Insights ====================

    async def get_campaign_insights(
        self,
        campaign_id: str,
        date_preset: str = "last_7d",
    ) -> Dict[str, Any]:
        """
        Get campaign insights/metrics.

        Args:
            campaign_id: Campaign ID
            date_preset: Date range preset (today, yesterday, last_7d, etc.)

        Returns:
            Insights data dict
        """
        if not self.is_configured:
            return self._get_mock_insights(campaign_id)

        endpoint = f"{campaign_id}/insights"
        params = {
            "fields": "impressions,clicks,spend,actions,action_values,ctr,cpc",
            "date_preset": date_preset,
        }

        result = await self._request("GET", endpoint, params=params)

        if "error" in result or not result.get("data"):
            return {}

        return result["data"][0] if result["data"] else {}

    async def get_account_insights(
        self,
        date_preset: str = "last_7d",
    ) -> Dict[str, Any]:
        """
        Get account-level insights.

        Args:
            date_preset: Date range preset

        Returns:
            Account insights data
        """
        if not self.is_configured:
            return self._get_mock_account_insights()

        endpoint = f"{self.ad_account_id}/insights"
        params = {
            "fields": "impressions,clicks,spend,actions,action_values,ctr,cpc",
            "date_preset": date_preset,
        }

        result = await self._request("GET", endpoint, params=params)

        if "error" in result or not result.get("data"):
            return {}

        return result["data"][0] if result["data"] else {}

    # ==================== Helper Methods ====================

    def _parse_campaign(self, data: Dict[str, Any]) -> MetaCampaign:
        """Parse API response into MetaCampaign."""
        daily_budget = data.get("daily_budget")
        if daily_budget:
            daily_budget = float(daily_budget) / 100  # Convert from cents

        lifetime_budget = data.get("lifetime_budget")
        if lifetime_budget:
            lifetime_budget = float(lifetime_budget) / 100

        created_time = None
        if data.get("created_time"):
            try:
                created_time = datetime.fromisoformat(data["created_time"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        return MetaCampaign(
            id=data["id"],
            name=data["name"],
            status=MetaCampaignStatus(data.get("status", "PAUSED")),
            objective=MetaCampaignObjective(data.get("objective", "OUTCOME_TRAFFIC")),
            daily_budget=daily_budget,
            lifetime_budget=lifetime_budget,
            created_time=created_time,
        )

    def _get_mock_campaigns(
        self,
        status: Optional[MetaCampaignStatus]
    ) -> List[MetaCampaign]:
        """Return mock campaigns for demo/development."""
        mock = [
            MetaCampaign(
                id="23851234567890",
                name="MedRx - Awareness Q1",
                status=MetaCampaignStatus.ACTIVE,
                objective=MetaCampaignObjective.AWARENESS,
                daily_budget=25.0,
                spend=75.50,
                impressions=15000,
                clicks=450,
                conversions=12,
            ),
            MetaCampaign(
                id="23851234567891",
                name="Bookadoc2u - Lead Gen",
                status=MetaCampaignStatus.ACTIVE,
                objective=MetaCampaignObjective.LEADS,
                daily_budget=30.0,
                spend=102.30,
                impressions=22000,
                clicks=680,
                conversions=18,
            ),
            MetaCampaign(
                id="23851234567892",
                name="InkwellPublishing - Retargeting",
                status=MetaCampaignStatus.PAUSED,
                objective=MetaCampaignObjective.SALES,
                daily_budget=20.0,
                spend=48.00,
                impressions=8000,
                clicks=240,
                conversions=6,
            ),
        ]

        if status:
            return [c for c in mock if c.status == status]
        return mock

    def _get_mock_insights(self, campaign_id: str) -> Dict[str, Any]:
        """Return mock insights for demo/development."""
        return {
            "impressions": "15000",
            "clicks": "450",
            "spend": "75.50",
            "ctr": "3.00",
            "cpc": "0.17",
            "actions": [
                {"action_type": "link_click", "value": "450"},
                {"action_type": "lead", "value": "12"},
            ],
            "_mock": True,
        }

    def _get_mock_account_insights(self) -> Dict[str, Any]:
        """Return mock account insights for demo/development."""
        return {
            "impressions": "45000",
            "clicks": "1370",
            "spend": "225.80",
            "ctr": "3.04",
            "cpc": "0.16",
            "actions": [
                {"action_type": "link_click", "value": "1370"},
                {"action_type": "lead", "value": "36"},
            ],
            "_mock": True,
        }
