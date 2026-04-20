"""
Ad Analytics Specialist
Handles performance analytics, reporting, and insights for ad campaigns.
"""

from app.agents.base_specialist import SpecialistAgent
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class AdAnalyticsSpecialist(SpecialistAgent):
    """
    Specialist for ad performance analytics.

    Responsibilities:
    - Generate performance reports
    - Calculate KPIs (CPA, ROAS, CTR)
    - Identify top/bottom performers
    - Trend analysis
    - Cross-workspace reporting
    """

    id = "spec.ads.analytics"
    display_name = "Ad Analytics Specialist"
    master_id = "master.advertising"
    role = "analytics"

    def get_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "role": self.role,
            "capabilities": [
                "daily_report",
                "kpi_calculation",
                "top_performers",
                "trend_analysis",
                "cross_workspace_summary",
            ],
        }

    def run_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an analytics task.

        Task types:
        - daily_report: Generate daily performance report
        - kpi: Calculate KPIs for an entity
        - top_performers: Identify best performing entities
        - bottom_performers: Identify worst performing entities
        - trends: Analyze performance trends

        Args:
            task_type: Type of task to execute
            payload: Task-specific parameters

        Returns:
            Task result with analytics data
        """
        handlers = {
            "daily_report": self._generate_daily_report,
            "kpi": self._calculate_kpis,
            "top_performers": self._get_top_performers,
            "bottom_performers": self._get_bottom_performers,
            "trends": self._analyze_trends,
        }

        handler = handlers.get(task_type)
        if not handler:
            return {
                "specialist": self.id,
                "task_type": task_type,
                "status": "error",
                "error": f"Unknown task type: {task_type}",
            }

        return handler(payload)

    def _generate_daily_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a daily performance report."""
        workspace_id = payload.get("workspace_id")
        date = payload.get("date", datetime.utcnow().date().isoformat())

        return {
            "specialist": self.id,
            "task_type": "daily_report",
            "status": "pending_implementation",
            "workspace_id": workspace_id,
            "date": date,
        }

    def _calculate_kpis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate KPIs for an entity."""
        metrics = payload.get("metrics", {})

        impressions = metrics.get("impressions", 0)
        clicks = metrics.get("clicks", 0)
        spend = metrics.get("spend", 0)
        conversions = metrics.get("conversions", 0)
        revenue = metrics.get("revenue", 0)

        # Calculate KPIs
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cpc = (spend / clicks) if clicks > 0 else 0
        cpa = (spend / conversions) if conversions > 0 else 0
        roas = (revenue / spend) if spend > 0 else 0
        cvr = (conversions / clicks * 100) if clicks > 0 else 0

        return {
            "specialist": self.id,
            "task_type": "kpi",
            "status": "success",
            "metrics": {
                "impressions": impressions,
                "clicks": clicks,
                "spend": round(spend, 2),
                "conversions": conversions,
                "revenue": round(revenue, 2),
            },
            "kpis": {
                "ctr": round(ctr, 2),
                "cpc": round(cpc, 2),
                "cpa": round(cpa, 2),
                "roas": round(roas, 2),
                "cvr": round(cvr, 2),
            },
        }

    def _get_top_performers(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Identify top performing entities."""
        entities = payload.get("entities", [])
        metric = payload.get("metric", "roas")
        limit = payload.get("limit", 5)

        # Sort by metric (descending for ROAS, ascending for CPA)
        reverse = metric.lower() not in ["cpa", "cpc"]
        sorted_entities = sorted(
            entities,
            key=lambda x: x.get(metric, 0),
            reverse=reverse
        )

        return {
            "specialist": self.id,
            "task_type": "top_performers",
            "status": "success",
            "metric": metric,
            "top_performers": sorted_entities[:limit],
        }

    def _get_bottom_performers(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Identify worst performing entities."""
        entities = payload.get("entities", [])
        metric = payload.get("metric", "cpa")
        limit = payload.get("limit", 5)

        # Sort by metric (ascending for ROAS, descending for CPA)
        reverse = metric.lower() in ["cpa", "cpc"]
        sorted_entities = sorted(
            entities,
            key=lambda x: x.get(metric, float('inf')),
            reverse=reverse
        )

        return {
            "specialist": self.id,
            "task_type": "bottom_performers",
            "status": "success",
            "metric": metric,
            "bottom_performers": sorted_entities[:limit],
        }

    def _analyze_trends(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        entity_id = payload.get("entity_id")
        metric = payload.get("metric", "spend")
        period = payload.get("period", "7d")

        return {
            "specialist": self.id,
            "task_type": "trends",
            "status": "pending_implementation",
            "entity_id": entity_id,
            "metric": metric,
            "period": period,
        }

    def generate_workspace_summary(
        self,
        campaigns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a summary across all campaigns in a workspace.

        Args:
            campaigns: List of campaign dicts with metrics

        Returns:
            Aggregated summary statistics
        """
        if not campaigns:
            return {
                "total_campaigns": 0,
                "active_campaigns": 0,
                "total_spend": 0,
                "total_conversions": 0,
                "avg_cpa": 0,
                "avg_roas": 0,
            }

        total_spend = sum(c.get("spend", 0) for c in campaigns)
        total_conversions = sum(c.get("conversions", 0) for c in campaigns)
        total_revenue = sum(c.get("revenue", 0) for c in campaigns)

        active = [c for c in campaigns if c.get("status") == "ACTIVE"]

        avg_cpa = (total_spend / total_conversions) if total_conversions > 0 else 0
        avg_roas = (total_revenue / total_spend) if total_spend > 0 else 0

        return {
            "total_campaigns": len(campaigns),
            "active_campaigns": len(active),
            "total_spend": round(total_spend, 2),
            "total_conversions": total_conversions,
            "total_revenue": round(total_revenue, 2),
            "avg_cpa": round(avg_cpa, 2),
            "avg_roas": round(avg_roas, 2),
        }
