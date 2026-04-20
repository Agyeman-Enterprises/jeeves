from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)


@dataclass
class AnalyticsReport:
    business: str
    report_type: str  # revenue, traffic, conversion, engagement, forecast
    period: str
    metrics: Dict[str, float]
    insights: List[str]
    generated_at: datetime

    def to_dict(self) -> Dict[str, str]:
        return {
            "business": self.business,
            "report_type": self.report_type,
            "period": self.period,
            "metrics": str(self.metrics),
            "insights": str(self.insights),
            "generated_at": self.generated_at.isoformat(),
        }


class DataAnalystAgent(BaseAgent):
    """Performs analytics, generates forecasts, and creates business reports."""

    data_path = Path("data") / "sample_analytics.json"
    description = "Analyzes data, generates forecasts, and creates business intelligence reports."
    capabilities = [
        "Generate revenue reports",
        "Analyze traffic and conversion metrics",
        "Create forecasts and projections",
        "Identify trends and patterns",
        "Build dashboards",
        "Provide data-driven insights",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.reports = self._load_reports()

    def supports(self, query: str) -> bool:
        keywords = [
            "analytics",
            "report",
            "forecast",
            "metrics",
            "data",
            "analysis",
            "insights",
            "revenue",
            "conversion",
            "traffic",
            "dashboard",
        ]
        return any(keyword in query.lower() for keyword in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()

        if "revenue" in query_lower or "sales" in query_lower:
            return self._handle_revenue_analysis(query, context)
        elif "forecast" in query_lower or "projection" in query_lower:
            return self._handle_forecast(query, context)
        elif "traffic" in query_lower or "visitors" in query_lower:
            return self._handle_traffic_analysis(query, context)
        elif "conversion" in query_lower:
            return self._handle_conversion_analysis(query, context)
        elif "report" in query_lower:
            return self._handle_report_generation(query, context)
        else:
            return self._handle_general_analytics(query, context)

    def _handle_revenue_analysis(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        business = context.get("business") if context else None
        lines = [
            f"Revenue Analysis{' for ' + business if business else ''}",
            "",
            "I can analyze:",
            "- Monthly/quarterly revenue trends",
            "- Revenue by product/service",
            "- Revenue by business unit",
            "- Growth rates and YoY comparisons",
            "- Revenue forecasting",
            "",
            "Provide: business name, time period, and I'll generate the analysis.",
        ]
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"report_type": "revenue", "business": business},
        )

    def _handle_forecast(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Forecast Generation",
            "",
            "I can create forecasts for:",
            "- Revenue projections",
            "- Traffic growth",
            "- Conversion rate trends",
            "- Customer acquisition",
            "- Market trends",
            "",
            "Specify: metric, time horizon, and historical data period.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"report_type": "forecast"})

    def _handle_traffic_analysis(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Traffic Analysis",
            "",
            "I can analyze:",
            "- Website traffic trends",
            "- Traffic sources (organic, paid, social)",
            "- Page performance",
            "- Bounce rates",
            "- User engagement metrics",
            "",
            "Provide: website/business and time period.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"report_type": "traffic"})

    def _handle_conversion_analysis(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Conversion Analysis",
            "",
            "I can analyze:",
            "- Conversion rates by channel",
            "- Funnel performance",
            "- A/B test results",
            "- Drop-off points",
            "- Optimization opportunities",
            "",
            "Specify: conversion goal and time period.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"report_type": "conversion"})

    def _handle_report_generation(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Report Generation",
            "",
            "I can generate:",
            "- Executive summaries",
            "- Weekly/monthly business reports",
            "- Performance dashboards",
            "- Trend analysis reports",
            "- Comparative analyses",
            "",
            "Specify: report type, business, and metrics to include.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _handle_general_analytics(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Data Analyst Ready",
            "",
            "I can help with:",
            "- Revenue analysis and forecasting",
            "- Traffic and conversion metrics",
            "- Business intelligence reports",
            "- Trend identification",
            "- Data visualization recommendations",
            "",
            "What would you like me to analyze?",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _load_reports(self) -> List[AnalyticsReport]:
        if not self.data_path.exists():
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            reports: List[AnalyticsReport] = []
            for entry in data:
                try:
                    generated_at = datetime.fromisoformat(entry.get("generated_at", datetime.now().isoformat()))
                    reports.append(
                        AnalyticsReport(
                            business=entry.get("business", ""),
                            report_type=entry.get("report_type", ""),
                            period=entry.get("period", ""),
                            metrics=entry.get("metrics", {}),
                            insights=entry.get("insights", []),
                            generated_at=generated_at,
                        )
                    )
                except Exception as exc:
                    LOGGER.debug("Skipping malformed analytics report: %s", exc)
            return reports
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

