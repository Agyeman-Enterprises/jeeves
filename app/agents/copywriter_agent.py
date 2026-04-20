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
class CopywritingProject:
    business: str
    project_type: str  # blog_post, ad_copy, email_campaign, landing_page
    title: str
    status: str
    due_date: Optional[date] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "business": self.business,
            "project_type": self.project_type,
            "title": self.title,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else "",
            "notes": self.notes,
        }


class CopywriterAgent(BaseAgent):
    """Creates blog posts, ad copy, email marketing, and landing pages for businesses."""

    data_path = Path("data") / "sample_copywriting.json"
    description = "Generates and manages copywriting projects across all businesses."
    capabilities = [
        "Write blog posts",
        "Create ad copy",
        "Draft email campaigns",
        "Design landing pages",
        "Track copywriting projects",
        "Generate content briefs",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.projects = self._load_projects()

    def supports(self, query: str) -> bool:
        keywords = [
            "blog",
            "ad copy",
            "email campaign",
            "landing page",
            "copywriting",
            "copywriter",
            "marketing copy",
            "content brief",
        ]
        return any(keyword in query.lower() for keyword in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()

        if "blog" in query_lower or "post" in query_lower:
            return self._handle_blog_request(query, context)
        elif "ad" in query_lower or "advertisement" in query_lower:
            return self._handle_ad_copy_request(query, context)
        elif "email" in query_lower and ("campaign" in query_lower or "marketing" in query_lower):
            return self._handle_email_campaign_request(query, context)
        elif "landing page" in query_lower or "landing" in query_lower:
            return self._handle_landing_page_request(query, context)
        elif "project" in query_lower or "queue" in query_lower:
            return self._handle_project_queue()
        else:
            return self._handle_general_copywriting(query, context)

    def _handle_blog_request(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        business = context.get("business") if context else None
        if not business:
            # Try to extract business from query
            businesses = ["ScribeMD", "Bookadoc2u", "DrAMD", "A3Design", "TaxRX"]
            for b in businesses:
                if b.lower() in query.lower():
                    business = b
                    break

        lines = [
            f"Blog post request for {business or 'your business'}",
            "",
            "I can help you create:",
            "- SEO-optimized blog posts",
            "- Thought leadership articles",
            "- Product launch announcements",
            "- Educational content",
            "",
            "Provide: topic, target audience, key points, and I'll draft the post.",
        ]
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"project_type": "blog_post", "business": business or "general"},
        )

    def _handle_ad_copy_request(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Ad Copy Creation",
            "",
            "I can generate:",
            "- Social media ads (Facebook, Instagram, LinkedIn)",
            "- Google Ads copy",
            "- Display banner copy",
            "- Video ad scripts",
            "",
            "Specify: platform, target audience, CTA, and campaign goal.",
        ]
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"project_type": "ad_copy"},
        )

    def _handle_email_campaign_request(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Email Marketing Campaign",
            "",
            "I can create:",
            "- Welcome email sequences",
            "- Newsletter templates",
            "- Promotional campaigns",
            "- Abandoned cart emails",
            "- Re-engagement campaigns",
            "",
            "Provide: campaign type, audience segment, and key messaging.",
        ]
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"project_type": "email_campaign"},
        )

    def _handle_landing_page_request(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Landing Page Copy",
            "",
            "I can write:",
            "- Hero headlines",
            "- Value propositions",
            "- Feature descriptions",
            "- CTA buttons",
            "- Social proof sections",
            "- FAQ content",
            "",
            "Specify: product/service, target conversion, and key benefits.",
        ]
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"project_type": "landing_page"},
        )

    def _handle_project_queue(self) -> AgentResponse:
        if not self.projects:
            return AgentResponse(
                agent=self.name,
                content="No copywriting projects in queue.",
                data={"projects": []},
            )

        today = date.today()
        due_soon = [p for p in self.projects if p.due_date and p.due_date <= today]
        upcoming = [p for p in self.projects if not p.due_date or p.due_date > today]

        lines = [f"Copywriting Projects: {len(self.projects)} total"]
        if due_soon:
            lines.append(f"\nDue soon/overdue: {len(due_soon)}")
            for project in due_soon[:3]:
                lines.append(f"- {project.title} ({project.project_type}) for {project.business}")

        if upcoming:
            lines.append(f"\nUpcoming: {len(upcoming)}")
            for project in upcoming[:3]:
                lines.append(f"- {project.title} ({project.project_type}) for {project.business}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"projects": [p.to_dict() for p in self.projects]},
        )

    def _handle_general_copywriting(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Copywriter Agent Ready",
            "",
            "I can help with:",
            "- Blog posts and articles",
            "- Ad copy (social, search, display)",
            "- Email marketing campaigns",
            "- Landing page copy",
            "- Content briefs and outlines",
            "",
            "What would you like me to create?",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _load_projects(self) -> List[CopywritingProject]:
        if not self.data_path.exists():
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            projects: List[CopywritingProject] = []
            for entry in data:
                try:
                    due_date = None
                    if entry.get("due_date"):
                        due_date = datetime.fromisoformat(entry["due_date"]).date()
                    projects.append(
                        CopywritingProject(
                            business=entry.get("business", ""),
                            project_type=entry.get("project_type", ""),
                            title=entry.get("title", ""),
                            status=entry.get("status", "draft"),
                            due_date=due_date,
                            notes=entry.get("notes", ""),
                        )
                    )
                except Exception as exc:
                    LOGGER.debug("Skipping malformed copywriting project: %s", exc)
            return projects
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

