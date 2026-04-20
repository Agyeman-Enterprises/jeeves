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
class PartnershipOpportunity:
    business: str
    partner_name: str
    opportunity_type: str  # partnership, joint_venture, acquisition, strategic_alliance
    status: str  # research, outreach, negotiation, active, closed
    potential_value: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "business": self.business,
            "partner_name": self.partner_name,
            "opportunity_type": self.opportunity_type,
            "status": self.status,
            "potential_value": self.potential_value or "",
            "notes": self.notes,
        }


class BusinessDevelopmentSpecialistAgent(BaseAgent):
    """Identifies and develops business opportunities, partnerships, and strategic initiatives."""

    data_path = Path("data") / "sample_business_development.json"
    description = "Identifies partnerships, strategic opportunities, and business growth initiatives."
    capabilities = [
        "Identify partnership opportunities",
        "Research potential partners",
        "Develop strategic alliances",
        "Evaluate acquisition targets",
        "Create business development plans",
        "Track opportunity pipeline",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.opportunities = self._load_opportunities()

    def supports(self, query: str) -> bool:
        keywords = [
            "partnership",
            "business development",
            "strategic",
            "alliance",
            "acquisition",
            "joint venture",
            "opportunity",
            "bizdev",
            "growth",
        ]
        return any(keyword in query.lower() for keyword in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()

        if "partnership" in query_lower:
            return self._handle_partnership_opportunities()
        elif "acquisition" in query_lower:
            return self._handle_acquisition_opportunities()
        elif "opportunity" in query_lower or "pipeline" in query_lower:
            return self._handle_opportunity_pipeline()
        elif "research" in query_lower:
            return self._handle_research_request(query, context)
        else:
            return self._handle_general_bizdev(query, context)

    def _handle_partnership_opportunities(self) -> AgentResponse:
        partnerships = [o for o in self.opportunities if o.opportunity_type == "partnership"]
        lines = [f"Partnership Opportunities: {len(partnerships)}"]
        active = [p for p in partnerships if p.status in ["outreach", "negotiation", "active"]]
        if active:
            lines.append(f"\nActive: {len(active)}")
            for opp in active[:3]:
                lines.append(f"- {opp.partner_name} ({opp.business}) - {opp.status}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"partnerships": [p.to_dict() for p in partnerships]},
        )

    def _handle_acquisition_opportunities(self) -> AgentResponse:
        acquisitions = [o for o in self.opportunities if o.opportunity_type == "acquisition"]
        lines = [f"Acquisition Opportunities: {len(acquisitions)}"]
        if acquisitions:
            for opp in acquisitions[:3]:
                value_str = f" (Value: {opp.potential_value})" if opp.potential_value else ""
                lines.append(f"- {opp.partner_name} ({opp.business}) - {opp.status}{value_str}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"acquisitions": [a.to_dict() for a in acquisitions]},
        )

    def _handle_opportunity_pipeline(self) -> AgentResponse:
        by_status: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        for opp in self.opportunities:
            by_status[opp.status] = by_status.get(opp.status, 0) + 1
            by_type[opp.opportunity_type] = by_type.get(opp.opportunity_type, 0) + 1

        lines = [f"Business Development Pipeline: {len(self.opportunities)} total"]
        lines.append(f"\nBy status: {', '.join(f'{k}: {v}' for k, v in by_status.items())}")
        lines.append(f"By type: {', '.join(f'{k}: {v}' for k, v in by_type.items())}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"opportunities": [o.to_dict() for o in self.opportunities]},
        )

    def _handle_research_request(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Business Development Research",
            "",
            "I can research:",
            "- Potential partnership targets",
            "- Market opportunities",
            "- Competitive landscape",
            "- Acquisition candidates",
            "- Strategic alliance possibilities",
            "",
            "Specify: business, industry, and research focus.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _handle_general_bizdev(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Business Development Specialist Ready",
            "",
            "I can help with:",
            "- Identifying partnership opportunities",
            "- Researching potential partners",
            "- Developing strategic alliances",
            "- Evaluating acquisitions",
            "- Creating growth strategies",
            "",
            "What opportunity would you like to explore?",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _load_opportunities(self) -> List[PartnershipOpportunity]:
        if not self.data_path.exists():
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            opportunities: List[PartnershipOpportunity] = []
            for entry in data:
                try:
                    opportunities.append(
                        PartnershipOpportunity(
                            business=entry.get("business", ""),
                            partner_name=entry.get("partner_name", ""),
                            opportunity_type=entry.get("opportunity_type", "partnership"),
                            status=entry.get("status", "research"),
                            potential_value=entry.get("potential_value"),
                            notes=entry.get("notes", ""),
                        )
                    )
                except Exception as exc:
                    LOGGER.debug("Skipping malformed opportunity: %s", exc)
            return opportunities
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

