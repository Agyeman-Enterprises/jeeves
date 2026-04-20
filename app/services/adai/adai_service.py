"""
AdAI Service
Central service for advertising automation across all companies.
Handles data aggregation, campaign management, and analytics.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

LOGGER = logging.getLogger(__name__)


class Platform(str, Enum):
    """Supported advertising platforms."""
    META = "meta"
    GOOGLE = "google"
    TIKTOK = "tiktok"


class CampaignStatus(str, Enum):
    """Campaign status values."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DRAFT = "DRAFT"
    ARCHIVED = "ARCHIVED"
    ERROR = "ERROR"


@dataclass
class CampaignMetrics:
    """Campaign performance metrics."""
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    conversions: int = 0
    revenue: float = 0.0

    @property
    def ctr(self) -> float:
        """Click-through rate percentage."""
        return (self.clicks / self.impressions * 100) if self.impressions > 0 else 0.0

    @property
    def cpc(self) -> float:
        """Cost per click."""
        return (self.spend / self.clicks) if self.clicks > 0 else 0.0

    @property
    def cpa(self) -> float:
        """Cost per acquisition."""
        return (self.spend / self.conversions) if self.conversions > 0 else 0.0

    @property
    def roas(self) -> float:
        """Return on ad spend."""
        return (self.revenue / self.spend) if self.spend > 0 else 0.0

    @property
    def cvr(self) -> float:
        """Conversion rate percentage."""
        return (self.conversions / self.clicks * 100) if self.clicks > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with calculated KPIs."""
        return {
            "impressions": self.impressions,
            "clicks": self.clicks,
            "spend": round(self.spend, 2),
            "conversions": self.conversions,
            "revenue": round(self.revenue, 2),
            "kpis": {
                "ctr": round(self.ctr, 2),
                "cpc": round(self.cpc, 2),
                "cpa": round(self.cpa, 2),
                "roas": round(self.roas, 2),
                "cvr": round(self.cvr, 2),
            }
        }


@dataclass
class Campaign:
    """Campaign representation."""
    id: str
    name: str
    workspace_id: str
    platform: Platform
    status: CampaignStatus
    daily_budget: float
    lifetime_budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: Optional[CampaignMetrics] = None
    meta_campaign_id: Optional[str] = None
    google_campaign_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "workspace_id": self.workspace_id,
            "platform": self.platform.value,
            "status": self.status.value,
            "daily_budget": self.daily_budget,
            "lifetime_budget": self.lifetime_budget,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "metrics": self.metrics.to_dict() if self.metrics else None,
        }


class AdAIService:
    """
    Central AdAI service for advertising automation.

    Handles:
    - Campaign CRUD operations
    - Performance data aggregation
    - Budget management
    - Cross-workspace analytics
    - Platform API coordination
    """

    # Priority companies for budget allocation
    PRIORITY_COMPANIES = [
        'medrx',
        'bookadoc2u',
        'myhealthally',
        'inkwellpublishing',
        'accessmd',
    ]

    # Monthly spend alert threshold (USD)
    MONTHLY_SPEND_ALERT_THRESHOLD = 150

    # Default daily budget cap per workspace
    DEFAULT_DAILY_CAP = 50.0

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize AdAI service.

        Args:
            supabase_url: Supabase project URL (falls back to env var)
            supabase_key: Supabase service key (falls back to env var)
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        self._client = None

    @property
    def is_configured(self) -> bool:
        """Check if Supabase is configured."""
        return bool(self.supabase_url and self.supabase_key)

    def _get_client(self):
        """Get or create Supabase client."""
        if not self.is_configured:
            LOGGER.warning("Supabase not configured for AdAI service")
            return None

        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.supabase_url, self.supabase_key)
            except ImportError:
                LOGGER.warning("Supabase client not installed")
                return None
            except Exception as e:
                LOGGER.error(f"Failed to create Supabase client: {e}")
                return None

        return self._client

    # ==================== Campaign Management ====================

    async def get_campaigns(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[CampaignStatus] = None,
        platform: Optional[Platform] = None,
    ) -> List[Campaign]:
        """
        Get campaigns with optional filters.

        Args:
            workspace_id: Filter by workspace
            status: Filter by status
            platform: Filter by platform

        Returns:
            List of Campaign objects
        """
        client = self._get_client()
        if not client:
            return self._get_mock_campaigns(workspace_id, status, platform)

        try:
            query = client.table("ad_campaigns").select("*")

            if workspace_id:
                query = query.eq("workspace_id", workspace_id)
            if status:
                query = query.eq("status", status.value)
            if platform:
                query = query.eq("platform", platform.value)

            result = query.execute()

            return [self._parse_campaign(row) for row in result.data]

        except Exception as e:
            LOGGER.error(f"Error fetching campaigns: {e}")
            return []

    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a single campaign by ID."""
        client = self._get_client()
        if not client:
            return None

        try:
            result = client.table("ad_campaigns").select("*").eq("id", campaign_id).single().execute()
            return self._parse_campaign(result.data) if result.data else None
        except Exception as e:
            LOGGER.error(f"Error fetching campaign {campaign_id}: {e}")
            return None

    async def create_campaign(
        self,
        name: str,
        workspace_id: str,
        platform: Platform,
        daily_budget: float,
        **kwargs
    ) -> Optional[Campaign]:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            workspace_id: Workspace/company ID
            platform: Target platform
            daily_budget: Daily budget in USD
            **kwargs: Additional campaign settings

        Returns:
            Created Campaign or None on failure
        """
        client = self._get_client()
        if not client:
            LOGGER.warning("Cannot create campaign: Supabase not configured")
            return None

        try:
            data = {
                "name": name,
                "workspace_id": workspace_id,
                "platform": platform.value,
                "status": CampaignStatus.DRAFT.value,
                "daily_budget": daily_budget,
                "created_at": datetime.utcnow().isoformat(),
                **kwargs
            }

            result = client.table("ad_campaigns").insert(data).execute()
            return self._parse_campaign(result.data[0]) if result.data else None

        except Exception as e:
            LOGGER.error(f"Error creating campaign: {e}")
            return None

    async def update_campaign_status(
        self,
        campaign_id: str,
        status: CampaignStatus
    ) -> bool:
        """Update campaign status."""
        client = self._get_client()
        if not client:
            return False

        try:
            client.table("ad_campaigns").update({
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", campaign_id).execute()
            return True
        except Exception as e:
            LOGGER.error(f"Error updating campaign status: {e}")
            return False

    async def update_campaign_budget(
        self,
        campaign_id: str,
        daily_budget: float
    ) -> bool:
        """Update campaign daily budget."""
        client = self._get_client()
        if not client:
            return False

        try:
            client.table("ad_campaigns").update({
                "daily_budget": daily_budget,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", campaign_id).execute()
            return True
        except Exception as e:
            LOGGER.error(f"Error updating campaign budget: {e}")
            return False

    # ==================== Analytics ====================

    async def get_workspace_summary(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get performance summary for a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            Summary dict with aggregate metrics
        """
        campaigns = await self.get_campaigns(workspace_id=workspace_id)

        if not campaigns:
            return {
                "workspace_id": workspace_id,
                "total_campaigns": 0,
                "active_campaigns": 0,
                "total_spend": 0.0,
                "total_conversions": 0,
                "total_revenue": 0.0,
                "avg_cpa": 0.0,
                "avg_roas": 0.0,
            }

        active = [c for c in campaigns if c.status == CampaignStatus.ACTIVE]

        total_spend = sum(c.metrics.spend if c.metrics else 0 for c in campaigns)
        total_conversions = sum(c.metrics.conversions if c.metrics else 0 for c in campaigns)
        total_revenue = sum(c.metrics.revenue if c.metrics else 0 for c in campaigns)

        avg_cpa = (total_spend / total_conversions) if total_conversions > 0 else 0.0
        avg_roas = (total_revenue / total_spend) if total_spend > 0 else 0.0

        return {
            "workspace_id": workspace_id,
            "total_campaigns": len(campaigns),
            "active_campaigns": len(active),
            "total_spend": round(total_spend, 2),
            "total_conversions": total_conversions,
            "total_revenue": round(total_revenue, 2),
            "avg_cpa": round(avg_cpa, 2),
            "avg_roas": round(avg_roas, 2),
        }

    async def get_cross_workspace_summary(self) -> Dict[str, Any]:
        """
        Get performance summary across all workspaces.

        Returns:
            Summary dict with cross-workspace metrics
        """
        all_campaigns = await self.get_campaigns()

        workspaces: Dict[str, List[Campaign]] = {}
        for campaign in all_campaigns:
            ws_id = campaign.workspace_id
            if ws_id not in workspaces:
                workspaces[ws_id] = []
            workspaces[ws_id].append(campaign)

        total_spend = sum(c.metrics.spend if c.metrics else 0 for c in all_campaigns)
        total_conversions = sum(c.metrics.conversions if c.metrics else 0 for c in all_campaigns)
        total_revenue = sum(c.metrics.revenue if c.metrics else 0 for c in all_campaigns)

        # Check priority company spend
        priority_spend = 0.0
        for ws_id, campaigns in workspaces.items():
            if self.is_priority_company(ws_id):
                priority_spend += sum(c.metrics.spend if c.metrics else 0 for c in campaigns)

        return {
            "total_workspaces": len(workspaces),
            "total_campaigns": len(all_campaigns),
            "active_campaigns": len([c for c in all_campaigns if c.status == CampaignStatus.ACTIVE]),
            "total_spend": round(total_spend, 2),
            "total_conversions": total_conversions,
            "total_revenue": round(total_revenue, 2),
            "priority_company_spend": round(priority_spend, 2),
            "spend_alert": total_spend > self.MONTHLY_SPEND_ALERT_THRESHOLD,
            "avg_cpa": round((total_spend / total_conversions) if total_conversions > 0 else 0, 2),
            "avg_roas": round((total_revenue / total_spend) if total_spend > 0 else 0, 2),
        }

    async def get_daily_metrics(
        self,
        workspace_id: Optional[str] = None,
        date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get daily metrics snapshot.

        Args:
            workspace_id: Optional workspace filter
            date: Date for metrics (defaults to today)

        Returns:
            Daily metrics dict
        """
        target_date = date or datetime.utcnow()
        client = self._get_client()

        if not client:
            # Return mock data when not configured
            return self._get_mock_daily_metrics(workspace_id, target_date)

        try:
            query = client.table("ad_metrics_daily").select("*")
            query = query.eq("date", target_date.date().isoformat())

            if workspace_id:
                query = query.eq("workspace_id", workspace_id)

            result = query.execute()

            # Aggregate metrics
            metrics = CampaignMetrics()
            for row in result.data:
                metrics.impressions += row.get("impressions", 0)
                metrics.clicks += row.get("clicks", 0)
                metrics.spend += row.get("spend", 0)
                metrics.conversions += row.get("conversions", 0)
                metrics.revenue += row.get("revenue", 0)

            return {
                "date": target_date.date().isoformat(),
                "workspace_id": workspace_id,
                **metrics.to_dict()
            }

        except Exception as e:
            LOGGER.error(f"Error fetching daily metrics: {e}")
            return {"error": str(e)}

    # ==================== Budget Management ====================

    def is_priority_company(self, company_slug: str) -> bool:
        """Check if a company is in the priority list."""
        normalized = company_slug.lower().replace(' ', '').replace('-', '').replace('_', '')
        return normalized in [c.lower() for c in self.PRIORITY_COMPANIES]

    def calculate_budget_allocation(
        self,
        total_budget: float,
        workspaces: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate budget allocation across workspaces.
        Priority companies get 60% of budget, others split 40%.

        Args:
            total_budget: Total available budget
            workspaces: List of workspace dicts with 'id' key

        Returns:
            Dict mapping workspace_id to allocated budget
        """
        priority = []
        non_priority = []

        for ws in workspaces:
            ws_id = ws.get('id', ws.get('slug', ''))
            if self.is_priority_company(ws_id):
                priority.append(ws_id)
            else:
                non_priority.append(ws_id)

        allocation: Dict[str, float] = {}

        # Priority companies get 60%
        if priority:
            priority_budget = total_budget * 0.6
            per_priority = priority_budget / len(priority)
            for ws_id in priority:
                allocation[ws_id] = round(per_priority, 2)

        # Non-priority split 40%
        if non_priority:
            non_priority_budget = total_budget * 0.4
            per_non_priority = non_priority_budget / len(non_priority)
            for ws_id in non_priority:
                allocation[ws_id] = round(per_non_priority, 2)

        return allocation

    async def check_spend_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for spend alerts across workspaces.

        Returns:
            List of alert dicts for workspaces exceeding thresholds
        """
        alerts = []
        summary = await self.get_cross_workspace_summary()

        if summary.get("spend_alert"):
            alerts.append({
                "type": "monthly_spend_exceeded",
                "level": "warning",
                "message": f"Total monthly spend (${summary['total_spend']}) exceeds threshold (${self.MONTHLY_SPEND_ALERT_THRESHOLD})",
                "total_spend": summary["total_spend"],
                "threshold": self.MONTHLY_SPEND_ALERT_THRESHOLD,
            })

        return alerts

    # ==================== Helper Methods ====================

    def _parse_campaign(self, row: Dict[str, Any]) -> Campaign:
        """Parse database row into Campaign object."""
        metrics = None
        if any(k in row for k in ['impressions', 'clicks', 'spend']):
            metrics = CampaignMetrics(
                impressions=row.get('impressions', 0),
                clicks=row.get('clicks', 0),
                spend=row.get('spend', 0),
                conversions=row.get('conversions', 0),
                revenue=row.get('revenue', 0),
            )

        return Campaign(
            id=row['id'],
            name=row['name'],
            workspace_id=row['workspace_id'],
            platform=Platform(row['platform']),
            status=CampaignStatus(row['status']),
            daily_budget=row.get('daily_budget', 0),
            lifetime_budget=row.get('lifetime_budget'),
            start_date=datetime.fromisoformat(row['start_date']) if row.get('start_date') else None,
            end_date=datetime.fromisoformat(row['end_date']) if row.get('end_date') else None,
            metrics=metrics,
            meta_campaign_id=row.get('meta_campaign_id'),
            google_campaign_id=row.get('google_campaign_id'),
        )

    def _get_mock_campaigns(
        self,
        workspace_id: Optional[str],
        status: Optional[CampaignStatus],
        platform: Optional[Platform],
    ) -> List[Campaign]:
        """Return mock campaign data for demo/development."""
        mock_campaigns = [
            Campaign(
                id="camp_001",
                name="MedRx Awareness Q1",
                workspace_id="medrx",
                platform=Platform.META,
                status=CampaignStatus.ACTIVE,
                daily_budget=25.0,
                metrics=CampaignMetrics(
                    impressions=15000,
                    clicks=450,
                    spend=75.50,
                    conversions=12,
                    revenue=480.0,
                ),
            ),
            Campaign(
                id="camp_002",
                name="Bookadoc2u Launch",
                workspace_id="bookadoc2u",
                platform=Platform.META,
                status=CampaignStatus.ACTIVE,
                daily_budget=30.0,
                metrics=CampaignMetrics(
                    impressions=22000,
                    clicks=680,
                    spend=102.30,
                    conversions=18,
                    revenue=720.0,
                ),
            ),
            Campaign(
                id="camp_003",
                name="InkwellPublishing Retargeting",
                workspace_id="inkwellpublishing",
                platform=Platform.META,
                status=CampaignStatus.PAUSED,
                daily_budget=20.0,
                metrics=CampaignMetrics(
                    impressions=8000,
                    clicks=240,
                    spend=48.00,
                    conversions=6,
                    revenue=180.0,
                ),
            ),
        ]

        # Apply filters
        filtered = mock_campaigns
        if workspace_id:
            filtered = [c for c in filtered if c.workspace_id == workspace_id]
        if status:
            filtered = [c for c in filtered if c.status == status]
        if platform:
            filtered = [c for c in filtered if c.platform == platform]

        return filtered

    def _get_mock_daily_metrics(
        self,
        workspace_id: Optional[str],
        date: datetime
    ) -> Dict[str, Any]:
        """Return mock daily metrics for demo/development."""
        return {
            "date": date.date().isoformat(),
            "workspace_id": workspace_id,
            "impressions": 45000,
            "clicks": 1370,
            "spend": 225.80,
            "conversions": 36,
            "revenue": 1380.0,
            "kpis": {
                "ctr": 3.04,
                "cpc": 0.16,
                "cpa": 6.27,
                "roas": 6.11,
                "cvr": 2.63,
            },
            "_mock": True,
        }
