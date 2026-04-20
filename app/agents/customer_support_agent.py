from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)


@dataclass
class SupportTicket:
    ticket_id: str
    business: str
    customer_email: str
    subject: str
    status: str  # open, in_progress, resolved, closed
    priority: str  # low, medium, high, urgent
    created_at: datetime
    last_updated: datetime
    category: str = "general"

    def to_dict(self) -> Dict[str, str]:
        return {
            "ticket_id": self.ticket_id,
            "business": self.business,
            "customer_email": self.customer_email,
            "subject": self.subject,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "category": self.category,
        }


class CustomerSupportSpecialistAgent(BaseAgent):
    """Handles customer queries, support tickets, and customer service operations."""

    data_path = Path("data") / "sample_support_tickets.json"
    description = "Manages customer support tickets and answers customer queries."
    capabilities = [
        "View open tickets",
        "Respond to customer inquiries",
        "Prioritize support requests",
        "Track resolution times",
        "Generate support responses",
        "Escalate urgent issues",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.tickets = self._load_tickets()

    def supports(self, query: str) -> bool:
        keywords = [
            "support",
            "ticket",
            "customer",
            "inquiry",
            "complaint",
            "help",
            "issue",
            "problem",
            "question",
        ]
        return any(keyword in query.lower() for keyword in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()

        if "open" in query_lower or "pending" in query_lower:
            return self._handle_open_tickets()
        elif "urgent" in query_lower or "priority" in query_lower:
            return self._handle_urgent_tickets()
        elif "respond" in query_lower or "reply" in query_lower or "answer" in query_lower:
            return self._handle_response_generation(query, context)
        elif "ticket" in query_lower:
            return self._handle_ticket_overview()
        else:
            return self._handle_general_support(query, context)

    def _handle_open_tickets(self) -> AgentResponse:
        open_tickets = [t for t in self.tickets if t.status in ["open", "in_progress"]]
        if not open_tickets:
            return AgentResponse(
                agent=self.name,
                content="No open support tickets.",
                data={"open_tickets": []},
            )

        open_tickets.sort(key=lambda t: (t.priority == "urgent", t.created_at), reverse=True)
        lines = [f"Open Support Tickets: {len(open_tickets)}"]
        for ticket in open_tickets[:5]:
            lines.append(
                f"- [{ticket.priority.upper()}] {ticket.subject} ({ticket.business}) - {ticket.status}"
            )

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"open_tickets": [t.to_dict() for t in open_tickets]},
        )

    def _handle_urgent_tickets(self) -> AgentResponse:
        urgent = [t for t in self.tickets if t.priority == "urgent" and t.status != "resolved"]
        if not urgent:
            return AgentResponse(
                agent=self.name,
                content="No urgent tickets at this time.",
                data={"urgent_tickets": []},
            )

        urgent.sort(key=lambda t: t.created_at)
        lines = [f"Urgent Tickets: {len(urgent)}"]
        for ticket in urgent:
            lines.append(f"- {ticket.subject} ({ticket.business}) - {ticket.customer_email}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"urgent_tickets": [t.to_dict() for t in urgent]},
        )

    def _handle_response_generation(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        ticket_id = context.get("ticket_id") if context else None
        customer_message = context.get("message") if context else None

        lines = [
            "Customer Support Response Generator",
            "",
            "I can help you:",
            "- Draft professional responses to customer inquiries",
            "- Handle complaints with empathy",
            "- Provide technical troubleshooting steps",
            "- Escalate issues appropriately",
            "- Follow up on resolved tickets",
            "",
        ]
        if ticket_id:
            lines.append(f"Working on ticket: {ticket_id}")
        if customer_message:
            lines.append(f"\nCustomer message: {customer_message[:200]}...")
            lines.append("\nI'll draft a response based on the context.")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"ticket_id": ticket_id, "message": customer_message},
        )

    def _handle_ticket_overview(self) -> AgentResponse:
        by_status: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        by_business: Dict[str, int] = {}

        for ticket in self.tickets:
            by_status[ticket.status] = by_status.get(ticket.status, 0) + 1
            by_priority[ticket.priority] = by_priority.get(ticket.priority, 0) + 1
            by_business[ticket.business] = by_business.get(ticket.business, 0) + 1

        lines = [f"Support Tickets Overview: {len(self.tickets)} total"]
        lines.append(f"\nBy status: {', '.join(f'{k}: {v}' for k, v in by_status.items())}")
        lines.append(f"By priority: {', '.join(f'{k}: {v}' for k, v in by_priority.items())}")
        lines.append(f"By business: {', '.join(f'{k}: {v}' for k, v in by_business.items())}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"tickets": [t.to_dict() for t in self.tickets]},
        )

    def _handle_general_support(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Customer Support Specialist Ready",
            "",
            "I can help with:",
            "- Viewing open tickets",
            "- Prioritizing urgent issues",
            "- Drafting customer responses",
            "- Tracking ticket status",
            "- Managing support workflows",
            "",
            "What do you need help with?",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _load_tickets(self) -> List[SupportTicket]:
        if not self.data_path.exists():
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            tickets: List[SupportTicket] = []
            for entry in data:
                try:
                    created_at = datetime.fromisoformat(entry["created_at"])
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    last_updated = datetime.fromisoformat(entry.get("last_updated", entry["created_at"]))
                    if last_updated.tzinfo is None:
                        last_updated = last_updated.replace(tzinfo=timezone.utc)

                    tickets.append(
                        SupportTicket(
                            ticket_id=entry.get("ticket_id", ""),
                            business=entry.get("business", ""),
                            customer_email=entry.get("customer_email", ""),
                            subject=entry.get("subject", ""),
                            status=entry.get("status", "open"),
                            priority=entry.get("priority", "medium"),
                            created_at=created_at,
                            last_updated=last_updated,
                            category=entry.get("category", "general"),
                        )
                    )
                except Exception as exc:
                    LOGGER.debug("Skipping malformed support ticket: %s", exc)
            return tickets
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

