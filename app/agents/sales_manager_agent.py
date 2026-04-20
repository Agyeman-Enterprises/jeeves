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
class SalesLead:
    name: str
    business: str  # DrAMD, Bookadoc2u, etc.
    source: str  # phonebook, referral, website, etc.
    contact_info: str
    status: str  # new, contacted, qualified, proposal, closed
    notes: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "business": self.business,
            "source": self.source,
            "contact_info": self.contact_info,
            "status": self.status,
            "notes": self.notes,
        }


class SalesManagerAgent(BaseAgent):
    """Creates cold emails, sales scripts, and manages deal strategy, especially for DrAMD and Bookadoc2u."""

    data_path = Path("data") / "sample_sales_leads.json"
    description = "Manages sales leads, creates cold emails, scripts, and deal strategies."
    capabilities = [
        "Create cold email templates",
        "Generate sales scripts",
        "Manage lead pipeline",
        "Develop deal strategies",
        "Track phonebook leads (CA/HI)",
        "Prioritize prospects",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.leads = self._load_leads()

    def supports(self, query: str) -> bool:
        keywords = [
            "sales",
            "lead",
            "cold email",
            "prospect",
            "deal",
            "pipeline",
            "script",
            "dramd",
            "bookadoc2u",
            "phonebook",
            "outreach",
        ]
        return any(keyword in query.lower() for keyword in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()

        if "cold email" in query_lower or "email" in query_lower:
            return self._handle_cold_email_creation(query, context)
        elif "script" in query_lower:
            return self._handle_sales_script(query, context)
        elif "lead" in query_lower or "pipeline" in query_lower:
            return self._handle_lead_pipeline()
        elif "deal" in query_lower or "strategy" in query_lower:
            return self._handle_deal_strategy(query, context)
        elif "phonebook" in query_lower or "scraping" in query_lower:
            return self._handle_phonebook_leads()
        else:
            return self._handle_general_sales(query, context)

    def _handle_cold_email_creation(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()
        business = context.get("business") if context else None
        if not business:
            # Check for DrAMD or Bookadoc2u in query
            if "dramd" in query_lower:
                business = "DrAMD"
            elif "bookadoc" in query_lower:
                business = "Bookadoc2u"

        lines = [
            f"Cold Email Creation{' for ' + business if business else ''}",
            "",
            "I can create:",
            "- Personalized cold email templates",
            "- Subject lines that get opens",
            "- Value propositions for medical practices",
            "- Follow-up sequences",
            "- A/B test variations",
            "",
            "Specify: target audience, business (DrAMD/Bookadoc2u), and key message.",
        ]
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"business": business or "general", "type": "cold_email"},
        )

    def _handle_sales_script(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Sales Script Generation",
            "",
            "I can create scripts for:",
            "- Cold calls",
            "- Discovery calls",
            "- Product demos",
            "- Objection handling",
            "- Closing conversations",
            "",
            "Specify: call type, business, and target persona.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"type": "sales_script"})

    def _handle_lead_pipeline(self) -> AgentResponse:
        by_status: Dict[str, List[SalesLead]] = {}
        by_business: Dict[str, int] = {}

        for lead in self.leads:
            by_status.setdefault(lead.status, []).append(lead)
            by_business[lead.business] = by_business.get(lead.business, 0) + 1

        lines = [f"Sales Pipeline: {len(self.leads)} total leads"]
        lines.append(f"\nBy status:")
        for status, leads in by_status.items():
            lines.append(f"- {status}: {len(leads)}")
        lines.append(f"\nBy business: {', '.join(f'{k}: {v}' for k, v in by_business.items())}")

        # Show top leads
        new_leads = by_status.get("new", [])[:3]
        if new_leads:
            lines.append(f"\nNew leads to contact:")
            for lead in new_leads:
                lines.append(f"- {lead.name} ({lead.business}) from {lead.source}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"leads": [l.to_dict() for l in self.leads]},
        )

    def _handle_deal_strategy(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        business = context.get("business") if context else None
        lines = [
            f"Deal Strategy{' for ' + business if business else ''}",
            "",
            "I can help develop:",
            "- Pricing strategies",
            "- Negotiation tactics",
            "- Proposal structures",
            "- Competitive positioning",
            "- Closing strategies",
            "",
            "Specify: deal size, business, and current stage.",
        ]
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"business": business, "type": "deal_strategy"},
        )

    def _handle_phonebook_leads(self) -> AgentResponse:
        phonebook_leads = [l for l in self.leads if "phonebook" in l.source.lower()]
        lines = [
            f"Phonebook Leads (CA/HI): {len(phonebook_leads)}",
            "",
            "I can help with:",
            "- Scraping CA/HI phonebooks for medical practices",
            "- Qualifying leads from phonebook data",
            "- Prioritizing outreach",
            "- Creating targeted campaigns",
            "",
        ]
        if phonebook_leads:
            lines.append("Recent phonebook leads:")
            for lead in phonebook_leads[:5]:
                lines.append(f"- {lead.name} ({lead.business}) - {lead.status}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"phonebook_leads": [l.to_dict() for l in phonebook_leads]},
        )

    def _handle_general_sales(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Sales Manager Ready",
            "",
            "I can help with:",
            "- Creating cold emails for DrAMD/Bookadoc2u",
            "- Generating sales scripts",
            "- Managing lead pipeline",
            "- Developing deal strategies",
            "- Tracking phonebook leads (CA/HI)",
            "",
            "What do you need help with?",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _load_leads(self) -> List[SalesLead]:
        if not self.data_path.exists():
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            leads: List[SalesLead] = []
            for entry in data:
                try:
                    leads.append(
                        SalesLead(
                            name=entry.get("name", ""),
                            business=entry.get("business", ""),
                            source=entry.get("source", ""),
                            contact_info=entry.get("contact_info", ""),
                            status=entry.get("status", "new"),
                            notes=entry.get("notes", ""),
                        )
                    )
                except Exception as exc:
                    LOGGER.debug("Skipping malformed sales lead: %s", exc)
            return leads
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

