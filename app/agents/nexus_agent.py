"""
Nexus Agent - Provides human-friendly summaries of NEXUS business intelligence.
Converts NEXUS JSON responses into spoken summaries for JARVIS.
Emits GEM events for all completed operations.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from app.agents.base import AgentResponse, BaseAgent
from app.services.nexus_service import NexusService, NexusServiceError
from app.services.intent_classifier import IntentClassifier
from app.services.jarviscore_client import JarvisCoreWriter

LOGGER = logging.getLogger(__name__)

# Singleton writer for GEM events
_gem_writer: Optional[JarvisCoreWriter] = None


def _get_gem_writer() -> JarvisCoreWriter:
    """Get or create GEM event writer singleton."""
    global _gem_writer
    if _gem_writer is None:
        _gem_writer = JarvisCoreWriter()
    return _gem_writer


def _emit_gem_event(event_type: str, payload: Dict[str, Any], workspace_id: Optional[str] = None):
    """Helper to emit GEM events (non-blocking)."""
    try:
        writer = _get_gem_writer()
        writer.emit_event(
            event_type=event_type,
            source="agent.nexus",
            payload=payload,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        LOGGER.warning("Failed to emit GEM event %s: %s", event_type, exc)


class NexusAgent(BaseAgent):
    """
    Agent that consumes NEXUS APIs and provides human-friendly summaries.
    Does NOT compute KPIs - only fetches and summarizes from NEXUS.
    """

    description = (
        "Provides business intelligence summaries by consuming NEXUS APIs. "
        "Handles portfolio overviews, business insights, and alerts."
    )
    capabilities = [
        "CEO briefing",
        "Portfolio overview",
        "Business insights",
        "Alert summaries",
        "Business comparisons",
        "Top performers",
        "High risk entities",
        "Revenue trends",
        "Ad performance",
    ]

    def __init__(
        self,
        nexus_service: Optional[NexusService] = None,
        intent_classifier: Optional[IntentClassifier] = None,
    ):
        super().__init__()
        self.nexus = nexus_service or NexusService()
        self.intent_classifier = intent_classifier or IntentClassifier()

    def supports(self, query: str) -> bool:
        """Check if query should be handled by NexusAgent using intent classification."""
        classification = self.intent_classifier.classify(query)
        return classification.get("intent") is not None

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        """Handle business intelligence queries via NEXUS using intent classification."""
        import asyncio

        try:
            # Classify intent
            classification = self.intent_classifier.classify(query)
            intent = classification.get("intent")
            entities = classification.get("entities", {})

            if not intent:
                # Not a business intelligence query
                return AgentResponse(
                    agent=self.name,
                    content="I didn't recognize that as a business intelligence query.",
                    status="error",
                )

            # Route to appropriate handler based on intent
            if intent == "ceo_briefing":
                return asyncio.run(self._get_ceo_briefing())
            elif intent == "portfolio_alerts":
                return asyncio.run(self._get_portfolio_alerts_brief())
            elif intent == "business_insight":
                business_name = entities.get("business_name")
                if business_name:
                    return asyncio.run(self._get_business_brief(business_name))
                else:
                    return AgentResponse(
                        agent=self.name,
                        content="I need a business name to provide insights. Which business?",
                        status="error",
                    )
            elif intent == "compare_businesses":
                business_names = entities.get("business_names", [])
                if business_names:
                    return asyncio.run(self._compare_businesses(business_names))
                else:
                    return AgentResponse(
                        agent=self.name,
                        content="I need business names to compare. Which businesses?",
                        status="error",
                    )
            elif intent == "top_performers":
                return asyncio.run(self._get_top_performers())
            elif intent == "high_risk_entities":
                return asyncio.run(self._get_high_risk_entities())
            elif intent == "revenue_trends":
                return asyncio.run(self._get_revenue_trends())
            elif intent == "opportunity_scan":
                return asyncio.run(self._get_opportunity_scan())
            elif intent == "ad_performance":
                return asyncio.run(self._get_ad_performance_summary())
            else:
                # Fallback to CEO briefing
                return asyncio.run(self._get_ceo_briefing())

        except NexusServiceError as exc:
            return AgentResponse(
                agent=self.name,
                content=f"I couldn't reach NEXUS to get business intelligence: {exc}",
                status="error",
                warnings=[f"NEXUS unavailable: {exc}"],
            )
        except Exception as exc:
            LOGGER.exception("Error in NexusAgent: %s", exc)
            return AgentResponse(
                agent=self.name,
                content="I encountered an error while fetching business intelligence.",
                status="error",
                warnings=[str(exc)],
            )

    async def _get_ceo_briefing(self) -> AgentResponse:
        """Get CEO briefing from NEXUS including AdAI performance metrics."""
        overview = await self.nexus.get_portfolio_overview()
        alerts = await self.nexus.get_alerts(active_only=True)
        ad_performance = await self.nexus.get_ad_performance()

        lines = ["CEO Briefing - Business Portfolio Status"]
        lines.append("=" * 50)

        # Portfolio summary
        total = overview.get("total_businesses", 0)
        lines.append(f"\nTotal Businesses: {total}")

        businesses = overview.get("businesses", [])
        if businesses:
            lines.append("\nBusiness Highlights:")
            for biz in businesses[:5]:  # Top 5
                name = biz.get("name", "Unknown")
                status = biz.get("status", "active")
                lines.append(f"  • {name} - {status}")

        # Ad Performance (from AdAI via Nexus)
        if ad_performance and not ad_performance.get("error"):
            lines.append("\n📊 Ad Performance Today:")
            spend_today = ad_performance.get("total_spend_today", 0)
            conversions = ad_performance.get("total_conversions", 0)
            pending = ad_performance.get("pending_approvals", 0)
            roas = ad_performance.get("average_roas", 0)

            lines.append(f"  • Total Spend: ${spend_today:,.2f}")
            lines.append(f"  • Conversions: {conversions}")
            if roas > 0:
                lines.append(f"  • ROAS: {roas:.2f}x")
            if pending > 0:
                lines.append(f"  • Pending Approvals: {pending}")

            # Top campaigns
            top_campaigns = ad_performance.get("top_campaigns", [])
            if top_campaigns:
                lines.append("  • Top Campaigns:")
                for camp in top_campaigns[:3]:
                    camp_name = camp.get("name", "Unknown")
                    lines.append(f"    - {camp_name}")

            # At-risk campaigns
            at_risk = ad_performance.get("at_risk_campaigns", [])
            if at_risk:
                lines.append("  • ⚠️ At-Risk Campaigns:")
                for camp in at_risk[:2]:
                    camp_name = camp.get("name", "Unknown")
                    reason = camp.get("reason", "needs attention")
                    lines.append(f"    - {camp_name}: {reason}")
        else:
            lines.append("\n📊 Ad Performance: Connect AdAI to view advertising metrics")

        # Alerts
        if alerts:
            lines.append(f"\n⚠️ Active Alerts: {len(alerts)}")
            for alert in alerts[:3]:  # Top 3
                name = alert.get("name", "Unknown Alert")
                lines.append(f"  • {name}")
        else:
            lines.append("\n✅ No active alerts")

        # ContentVault — content pipeline
        try:
            from app.services.contentvault_service import ContentVaultService
            cv = ContentVaultService()
            if cv.is_configured():
                lines.append("\n📦 Content Pipeline (ContentVault):")
                lines.append(f"  {cv.get_briefing_summary()}")
        except Exception as exc:
            LOGGER.debug("ContentVault unavailable for CEO briefing: %s", exc)

        # OneDesk — project management
        try:
            from app.services.onedesk_service import OneDeskService
            od = OneDeskService()
            if od.is_configured():
                lines.append("\n📋 Projects & Tasks (OneDesk):")
                lines.append(f"  {od.get_briefing_summary()}")
        except Exception as exc:
            LOGGER.debug("OneDesk unavailable for CEO briefing: %s", exc)

        # BlackRoom strategic decisions
        try:
            from app.services.blackroom_service import BlackroomService
            blackroom = BlackroomService()
            decisions = blackroom.get_decisions(limit=5, status="active")
            lines.append("\n🧠 Strategic Decisions (BlackRoom):")
            if decisions:
                for d in decisions:
                    lines.append(f"  • {d.get('title', 'Untitled')}")
            else:
                lines.append("  No active strategic decisions.")
        except Exception as exc:
            LOGGER.debug("BlackRoom unavailable for CEO briefing: %s", exc)

        content = "\n".join(lines)

        # Emit GEM event for briefing completion
        _emit_gem_event(
            event_type="nexus.briefing.completed",
            payload={
                "briefingType": "ceo",
                "summary": f"CEO briefing delivered. {len(businesses)} businesses, {len(alerts)} alerts.",
                "alertCount": len(alerts),
                "topPerformers": [b.get("name") for b in overview.get("top_performers", [])[:3]],
                "atRisk": [a.get("name") for a in alerts[:3]],
                "adSpendToday": ad_performance.get("total_spend_today", 0),
            },
        )

        return AgentResponse(
            agent=self.name,
            content=content,
            data={"overview": overview, "alerts": alerts, "ad_performance": ad_performance},
        )

    async def _get_portfolio_overview(self) -> AgentResponse:
        """Get portfolio overview summary."""
        overview = await self.nexus.get_portfolio_overview()

        total = overview.get("total_businesses", 0)
        businesses = overview.get("businesses", [])

        lines = [f"Portfolio Overview: {total} businesses tracked"]

        if businesses:
            for biz in businesses[:10]:  # Top 10
                name = biz.get("name", "Unknown")
                category = biz.get("category", "")
                state = biz.get("state", "")
                lines.append(f"  • {name} ({category}, {state})")

        content = "\n".join(lines)
        return AgentResponse(
            agent=self.name,
            content=content,
            data=overview,
        )

    async def _get_business_brief(self, business_id: str) -> AgentResponse:
        """Get brief for a specific business."""
        insight = await self.nexus.get_business_insight(business_id)

        if "error" in insight:
            return AgentResponse(
                agent=self.name,
                content=f"I couldn't get insights for {business_id} from NEXUS.",
                status="error",
            )

        name = insight.get("name", business_id)
        lines = [f"Business Insight: {name}"]

        # Add key metrics if available
        metrics = insight.get("metrics", {})
        if metrics:
            lines.append("\nKey Metrics:")
            for key, value in list(metrics.items())[:5]:
                lines.append(f"  • {key}: {value}")

        content = "\n".join(lines)
        return AgentResponse(
            agent=self.name,
            content=content,
            data=insight,
        )

    async def _get_portfolio_alerts_brief(self) -> AgentResponse:
        """Get portfolio alerts summary."""
        alerts = await self.nexus.get_alerts(active_only=True)
        events = await self.nexus.get_alert_events(limit=10)

        lines = ["Portfolio Alerts Status"]

        if alerts:
            lines.append(f"\nActive Alerts: {len(alerts)}")
            for alert in alerts[:5]:
                name = alert.get("name", "Unknown")
                lines.append(f"  • {name}")
        else:
            lines.append("\n✅ No active alerts")

        if events:
            lines.append(f"\nRecent Events: {len(events)}")
            for event in events[:3]:
                alert_name = event.get("alert_name", "Unknown")
                triggered_at = event.get("triggered_at", "")
                lines.append(f"  • {alert_name} - {triggered_at}")

        content = "\n".join(lines)
        return AgentResponse(
            agent=self.name,
            content=content,
            data={"alerts": alerts, "events": events},
        )

    async def _compare_businesses(self, business_ids: List[str]) -> AgentResponse:
        """Compare multiple businesses."""
        comparison = await self.nexus.compare_businesses(business_ids)

        if "error" in comparison:
            return AgentResponse(
                agent=self.name,
                content="I couldn't compare those businesses from NEXUS.",
                status="error",
            )

        lines = [f"Business Comparison: {', '.join(business_ids)}"]
        # Add comparison details if available
        comp_data = comparison.get("comparison", {})
        if comp_data:
            lines.append("\nComparison:")
            for key, value in list(comp_data.items())[:5]:
                lines.append(f"  • {key}: {value}")

        content = "\n".join(lines)
        return AgentResponse(
            agent=self.name,
            content=content,
            data=comparison,
        )

    async def _get_top_performers(self) -> AgentResponse:
        """Get top performing businesses from NEXUS."""
        overview = await self.nexus.get_portfolio_overview()

        # Extract top_performers from overview if available
        top_performers = overview.get("top_performers", [])
        
        if not top_performers:
            # Fallback: try to infer from businesses list
            businesses = overview.get("businesses", [])
            # Sort by performance metric if available
            businesses_with_perf = [
                b for b in businesses
                if b.get("performance_score") or b.get("revenue_growth")
            ]
            top_performers = sorted(
                businesses_with_perf,
                key=lambda x: x.get("performance_score", 0) or x.get("revenue_growth", 0),
                reverse=True
            )[:5]

        lines = ["Top Performing Businesses"]

        if top_performers:
            for idx, biz in enumerate(top_performers[:5], 1):
                name = biz.get("name", "Unknown")
                score = biz.get("performance_score") or biz.get("revenue_growth")
                lines.append(f"  {idx}. {name}" + (f" (score: {score})" if score else ""))
        else:
            lines.append("\nNo performance data available from NEXUS.")

        content = "\n".join(lines)
        return AgentResponse(
            agent=self.name,
            content=content,
            data={"top_performers": top_performers, "overview": overview},
        )

    async def _get_high_risk_entities(self) -> AgentResponse:
        """Get high-risk businesses that need attention."""
        overview = await self.nexus.get_portfolio_overview()

        # Extract high_risk_businesses from overview if available
        high_risk = overview.get("high_risk_businesses", []) or overview.get("highest_risk_businesses", [])

        if not high_risk:
            # Fallback: look for businesses with alerts or negative metrics
            businesses = overview.get("businesses", [])
            high_risk = [
                b for b in businesses
                if b.get("risk_level") == "high"
                or b.get("has_alerts", False)
                or (b.get("revenue_growth", 0) < 0)
            ][:5]

        lines = ["High-Risk Businesses Requiring Attention"]

        if high_risk:
            for biz in high_risk:
                name = biz.get("name", "Unknown")
                risk_reason = biz.get("risk_reason") or biz.get("alert_summary", "Needs attention")
                lines.append(f"  • {name}: {risk_reason}")
        else:
            lines.append("\n✅ No high-risk businesses identified.")

        content = "\n".join(lines)
        return AgentResponse(
            agent=self.name,
            content=content,
            data={"high_risk_businesses": high_risk, "overview": overview},
        )

    async def _get_revenue_trends(self) -> AgentResponse:
        """Get revenue trends across portfolio."""
        overview = await self.nexus.get_portfolio_overview()

        # Extract revenue trends from overview
        revenue_trends = overview.get("revenue_trends", {})
        businesses = overview.get("businesses", [])

        lines = ["Portfolio Revenue Trends"]

        if revenue_trends:
            total_revenue = revenue_trends.get("total_revenue")
            growth_rate = revenue_trends.get("growth_rate")
            mom_change = revenue_trends.get("month_over_month_change")

            if total_revenue:
                lines.append(f"\nTotal Portfolio Revenue: ${total_revenue:,.2f}")
            if growth_rate is not None:
                lines.append(f"Growth Rate: {growth_rate:.1f}%")
            if mom_change is not None:
                trend = "↑" if mom_change > 0 else "↓"
                lines.append(f"Month-over-Month: {trend} {abs(mom_change):.1f}%")

            # Biggest movers
            biggest_drop = revenue_trends.get("biggest_revenue_drop")
            biggest_gain = revenue_trends.get("biggest_revenue_gain")

            if biggest_drop:
                lines.append(f"\nBiggest Drop: {biggest_drop.get('name')} - {biggest_drop.get('change', 0):.1f}%")
            if biggest_gain:
                lines.append(f"Biggest Gain: {biggest_gain.get('name')} - {biggest_gain.get('change', 0):.1f}%")
        else:
            # Fallback: analyze businesses for revenue data
            businesses_with_revenue = [
                b for b in businesses
                if b.get("revenue") or b.get("revenue_growth") is not None
            ]
            if businesses_with_revenue:
                lines.append("\nRevenue by Business:")
                for biz in businesses_with_revenue[:10]:
                    name = biz.get("name", "Unknown")
                    revenue = biz.get("revenue")
                    growth = biz.get("revenue_growth")
                    if revenue:
                        lines.append(f"  • {name}: ${revenue:,.2f}" + (f" ({growth:+.1f}%)" if growth is not None else ""))
            else:
                lines.append("\nNo revenue trend data available from NEXUS.")

        content = "\n".join(lines)
        return AgentResponse(
            agent=self.name,
            content=content,
            data={"revenue_trends": revenue_trends, "overview": overview},
        )

    async def _get_opportunity_scan(self) -> AgentResponse:
        """Get growth opportunities from NEXUS."""
        overview = await self.nexus.get_portfolio_overview()

        # Extract opportunities from overview if available
        opportunities = overview.get("opportunities", []) or overview.get("growth_opportunities", [])

        if not opportunities:
            # Fallback: look for businesses with high growth potential
            businesses = overview.get("businesses", [])
            opportunities = [
                b for b in businesses
                if b.get("growth_potential") == "high"
                or b.get("opportunity_score", 0) > 0.7
            ][:5]

        lines = ["Growth Opportunities"]

        if opportunities:
            for opp in opportunities:
                name = opp.get("name", "Unknown")
                reason = opp.get("opportunity_reason") or opp.get("description", "High growth potential")
                lines.append(f"  • {name}: {reason}")
        else:
            lines.append("\nNo specific opportunities identified. Review portfolio overview for insights.")

        content = "\n".join(lines)
        return AgentResponse(
            agent=self.name,
            content=content,
            data={"opportunities": opportunities, "overview": overview},
        )

    async def _get_ad_performance_summary(self) -> AgentResponse:
        """Get detailed ad performance summary (AdAI metrics via Nexus)."""
        ad_performance = await self.nexus.get_ad_performance()

        lines = ["Ad Performance Summary"]
        lines.append("=" * 50)

        if ad_performance.get("error"):
            lines.append("\n⚠️ AdAI data unavailable. Connect your ad accounts to enable tracking.")
            return AgentResponse(
                agent=self.name,
                content="\n".join(lines),
                data={"ad_performance": ad_performance},
                status="warning",
            )

        # Today's metrics
        lines.append("\n📊 Today's Performance:")
        spend_today = ad_performance.get("total_spend_today", 0)
        spend_mtd = ad_performance.get("total_spend_mtd", 0)
        conversions = ad_performance.get("total_conversions", 0)
        avg_cpa = ad_performance.get("average_cpa", 0)
        roas = ad_performance.get("average_roas", 0)

        lines.append(f"  • Spend Today: ${spend_today:,.2f}")
        lines.append(f"  • Spend MTD: ${spend_mtd:,.2f}")
        lines.append(f"  • Conversions: {conversions}")
        if avg_cpa > 0:
            lines.append(f"  • Average CPA: ${avg_cpa:,.2f}")
        if roas > 0:
            lines.append(f"  • ROAS: {roas:.2f}x")

        # Platform breakdown
        platform_breakdown = ad_performance.get("platform_breakdown", {})
        if platform_breakdown:
            lines.append("\n📱 Platform Breakdown:")
            for platform, metrics in platform_breakdown.items():
                p_spend = metrics.get("spend", 0)
                p_conv = metrics.get("conversions", 0)
                if p_spend > 0 or p_conv > 0:
                    lines.append(f"  • {platform.capitalize()}: ${p_spend:,.2f} | {p_conv} conv")

        # Top campaigns
        top_campaigns = ad_performance.get("top_campaigns", [])
        if top_campaigns:
            lines.append("\n🏆 Top Performing Campaigns:")
            for camp in top_campaigns[:5]:
                camp_name = camp.get("name", "Unknown")
                camp_roas = camp.get("roas", 0)
                camp_spend = camp.get("spend", 0)
                lines.append(f"  • {camp_name}" + (f" (ROAS: {camp_roas:.2f}x)" if camp_roas > 0 else ""))

        # At-risk campaigns
        at_risk = ad_performance.get("at_risk_campaigns", [])
        if at_risk:
            lines.append("\n⚠️ Campaigns Needing Attention:")
            for camp in at_risk:
                camp_name = camp.get("name", "Unknown")
                reason = camp.get("reason", "Performance decline")
                lines.append(f"  • {camp_name}: {reason}")

        # Pending approvals
        pending = ad_performance.get("pending_approvals", 0)
        if pending > 0:
            lines.append(f"\n🔔 Pending Approvals: {pending}")

        content = "\n".join(lines)

        # Emit GEM event for ad performance query
        _emit_gem_event(
            event_type="nexus.briefing.completed",
            payload={
                "briefingType": "ad_performance",
                "summary": f"Ad performance summary delivered. Spend: ${spend_today:,.2f}, Conversions: {conversions}",
                "alertCount": len(at_risk),
                "metrics": {
                    "spendToday": spend_today,
                    "spendMTD": spend_mtd,
                    "conversions": conversions,
                    "avgCPA": avg_cpa,
                    "roas": roas,
                },
            },
        )

        return AgentResponse(
            agent=self.name,
            content=content,
            data={"ad_performance": ad_performance},
        )

    def _extract_business_name(self, query: str) -> Optional[str]:
        """Extract business name from query (simple heuristic)."""
        # This is now handled by intent classifier, but kept for backward compatibility
        return None

    def _extract_business_names(self, query: str) -> List[str]:
        """Extract multiple business names from query."""
        # This is now handled by intent classifier, but kept for backward compatibility
        return []

