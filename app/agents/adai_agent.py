"""
AdAI Agent
BaseAgent wrapper for the AdMaster, enabling integration with the Jarvis orchestrator.
Handles ad-related queries and routes to appropriate specialists.
"""

from app.agents.base import BaseAgent, AgentResponse
from app.agents.masters.ad_master import AdMaster, PRIORITY_COMPANIES, MONTHLY_SPEND_ALERT_THRESHOLD
from typing import Dict, Any, Optional, List
import asyncio


class AdAIAgent(BaseAgent):
    """
    AdAI Agent - Advertising automation and optimization.

    This agent handles all ad-related queries and provides:
    - Campaign status and performance reports
    - Budget optimization recommendations
    - Creative rotation suggestions
    - A/B testing insights
    - Cross-company ad spend summaries

    Priority companies: MedRx, Bookadoc2u, MyHealthAlly, InkwellPublishing, AccessMD
    """

    name = "AdAIAgent"
    description = "Advertising AI - manages ad campaigns, creative rotation, spend optimization across 31 companies"
    capabilities = [
        "Campaign performance reporting",
        "Budget optimization and scaling",
        "Creative rotation recommendations",
        "A/B testing management",
        "Cross-company ad spend summaries",
        "Anomaly detection and alerts",
        "Platform-specific insights (Meta, Google, TikTok)",
    ]

    def __init__(
        self,
        personality: Optional[Dict] = None,
        behavior: Optional[Dict] = None
    ) -> None:
        super().__init__(personality=personality, behavior=behavior)
        self.ad_master = AdMaster()

    def supports(self, query: str) -> bool:
        """Check if this agent should handle the query."""
        keywords = [
            # Core ad terms
            "ad", "ads", "advertising", "adai",
            "campaign", "campaigns",
            "creative", "creatives",
            # Metrics
            "cpa", "roas", "ctr", "cpc",
            "spend", "budget",
            "impressions", "clicks", "conversions",
            # Actions
            "scale", "pause", "rotate",
            # Platforms
            "meta", "facebook", "instagram", "google ads", "tiktok",
            # Testing
            "a/b test", "ab test", "experiment",
        ]
        query_lower = query.lower()
        return any(kw in query_lower for kw in keywords)

    def handle(self, query: str, context: Optional[Dict[str, str]] = None) -> AgentResponse:
        """
        Handle an ad-related query.

        Routes to appropriate handlers based on query intent.
        """
        query_lower = query.lower()
        ctx = context or {}

        try:
            # Performance/Status queries
            if any(kw in query_lower for kw in ["how are", "performance", "status", "report"]):
                return self._handle_performance_query(query, ctx)

            # Budget queries
            if any(kw in query_lower for kw in ["budget", "spend", "cost", "scale"]):
                return self._handle_budget_query(query, ctx)

            # Creative queries
            if any(kw in query_lower for kw in ["creative", "rotate", "fatigue"]):
                return self._handle_creative_query(query, ctx)

            # Experiment queries
            if any(kw in query_lower for kw in ["test", "experiment", "a/b", "ab"]):
                return self._handle_experiment_query(query, ctx)

            # Strategy/planning queries
            if any(kw in query_lower for kw in ["plan", "strategy", "recommend"]):
                return self._handle_strategy_query(query, ctx)

            # Default: general info
            return self._handle_general_query(query, ctx)

        except Exception as e:
            return AgentResponse(
                agent=self.name,
                content=f"Error processing ad query: {str(e)}",
                data={"error": str(e)},
                status="error",
            )

    def _handle_performance_query(self, query: str, context: Dict) -> AgentResponse:
        """Handle performance and status queries."""
        business = context.get("business", context.get("business_name"))

        # TODO: Integrate with Supabase to fetch actual metrics
        # For now, return a structured placeholder

        content = self._format_performance_summary(business)

        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "query_type": "performance",
                "business": business,
                "priority_companies": PRIORITY_COMPANIES,
                "status": "pending_data_integration",
            },
            status="success",
        )

    def _handle_budget_query(self, query: str, context: Dict) -> AgentResponse:
        """Handle budget and spend queries."""
        business = context.get("business", context.get("business_name"))

        content = (
            f"**Ad Budget Summary**\n\n"
            f"Monthly spend alert threshold: ${MONTHLY_SPEND_ALERT_THRESHOLD}\n"
            f"Default daily cap per workspace: $50\n\n"
            f"Priority companies for budget allocation:\n"
        )
        for company in PRIORITY_COMPANIES:
            content += f"- {company.title()}\n"

        content += (
            f"\n*Note: Full budget data integration with Supabase pending. "
            f"Cloudflare Worker will sync actual spend data.*"
        )

        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "query_type": "budget",
                "business": business,
                "monthly_threshold": MONTHLY_SPEND_ALERT_THRESHOLD,
                "default_daily_cap": 50,
            },
            status="success",
        )

    def _handle_creative_query(self, query: str, context: Dict) -> AgentResponse:
        """Handle creative and rotation queries."""
        content = (
            "**Creative Management**\n\n"
            "AdAI monitors creative performance and recommends rotation when:\n"
            "- CTR drops below 0.5%\n"
            "- Frequency exceeds 3.0\n"
            "- Performance declines for 2+ consecutive days\n\n"
            "*Creative library and rotation data will be available once "
            "Meta API integration is complete.*"
        )

        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "query_type": "creative",
                "rotation_thresholds": {
                    "ctr_floor": 0.005,
                    "frequency_ceiling": 3.0,
                },
            },
            status="success",
        )

    def _handle_experiment_query(self, query: str, context: Dict) -> AgentResponse:
        """Handle A/B testing queries."""
        content = (
            "**A/B Testing with AdAI**\n\n"
            "Experiment types supported:\n"
            "- Creative tests (image vs video vs carousel)\n"
            "- Copy tests (headlines, body, CTAs)\n"
            "- Audience tests (targeting variations)\n"
            "- Bid strategy tests\n\n"
            "Winner criteria:\n"
            "- Minimum 10 conversions per arm\n"
            "- 95% confidence level\n"
            "- 10%+ lift over control\n\n"
            "*Experiment management UI coming in Phase 4.*"
        )

        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "query_type": "experiment",
                "winner_criteria": {
                    "min_conversions": 10,
                    "confidence": 0.95,
                    "min_lift_percent": 10,
                },
            },
            status="success",
        )

    def _handle_strategy_query(self, query: str, context: Dict) -> AgentResponse:
        """Handle strategy and planning queries."""
        business = context.get("business", context.get("business_name", "your business"))

        # Use AdMaster's plan method for strategy generation
        plan_result = self.ad_master.plan(
            objective=query,
            context=context
        )

        content = (
            f"**Advertising Strategy for {business}**\n\n"
            f"{plan_result.get('strategy', 'Strategy generation pending LLM integration.')}"
        )

        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "query_type": "strategy",
                "plan": plan_result,
            },
            status="success",
        )

    def _handle_general_query(self, query: str, context: Dict) -> AgentResponse:
        """Handle general ad queries."""
        summary = self.ad_master.get_summary()

        content = (
            "**AdAI - Advertising Automation**\n\n"
            f"Managing ads for {summary['specialist_count']} specialist areas:\n"
            "- Meta campaign management\n"
            "- Creative asset optimization\n"
            "- Budget governance\n"
            "- Performance analytics\n"
            "- A/B testing\n\n"
            f"Priority companies: {', '.join(c.title() for c in PRIORITY_COMPANIES)}\n"
            f"Monthly spend alert: ${MONTHLY_SPEND_ALERT_THRESHOLD}\n\n"
            "Ask me about:\n"
            "- \"How are my ads performing?\"\n"
            "- \"What's my ad spend this month?\"\n"
            "- \"Suggest a creative rotation\"\n"
            "- \"Plan an A/B test for MedRx\"\n"
        )

        return AgentResponse(
            agent=self.name,
            content=content,
            data={
                "query_type": "general",
                "summary": summary,
            },
            status="success",
        )

    def _format_performance_summary(self, business: Optional[str] = None) -> str:
        """Format a performance summary message."""
        if business:
            is_priority = self.ad_master.is_priority_company(business)
            priority_note = " (Priority company)" if is_priority else ""
            return (
                f"**Ad Performance for {business}{priority_note}**\n\n"
                f"*Performance data will be available once Meta API sync is complete.*\n\n"
                f"The Cloudflare Worker will pull daily metrics including:\n"
                f"- Impressions, clicks, CTR\n"
                f"- Spend, CPA, ROAS\n"
                f"- Conversion data\n"
                f"- Creative performance scores"
            )
        else:
            return (
                "**Ad Performance Summary (All Companies)**\n\n"
                f"Priority companies: {', '.join(c.title() for c in PRIORITY_COMPANIES)}\n"
                f"Monthly spend threshold: ${MONTHLY_SPEND_ALERT_THRESHOLD}\n\n"
                f"*Cross-company performance data will be available once Meta API sync is complete.*\n\n"
                "Specify a company name for detailed insights:\n"
                "- \"How are MedRx ads performing?\"\n"
                "- \"Bookadoc2u ad spend this week\""
            )
