from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)


@dataclass
class SEOProject:
    website: str
    business: str
    project_type: str  # keyword_research, on_page, backlinks, content_optimization, technical_seo
    status: str
    priority: str
    notes: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "website": self.website,
            "business": self.business,
            "project_type": self.project_type,
            "status": self.status,
            "priority": self.priority,
            "notes": self.notes,
        }


class SEOEcommerceSpecialistAgent(BaseAgent):
    """Handles SEO optimization and eCommerce strategy across all business websites."""

    data_path = Path("data") / "sample_seo_ecommerce.json"
    description = "Manages SEO optimization and eCommerce strategy across all business websites."
    capabilities = [
        "Keyword research and optimization",
        "On-page SEO audits",
        "Technical SEO improvements",
        "eCommerce conversion optimization",
        "Site performance analysis",
        "Competitor SEO analysis",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.projects = self._load_projects()

    def supports(self, query: str) -> bool:
        keywords = [
            "seo",
            "keyword",
            "ecommerce",
            "optimization",
            "ranking",
            "search engine",
            "backlink",
            "conversion",
            "website",
            "traffic",
        ]
        return any(keyword in query.lower() for keyword in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()

        if "keyword" in query_lower:
            return self._handle_keyword_research(query, context)
        elif "on-page" in query_lower or "onpage" in query_lower:
            return self._handle_on_page_seo(query, context)
        elif "technical" in query_lower:
            return self._handle_technical_seo(query, context)
        elif "ecommerce" in query_lower or "conversion" in query_lower:
            return self._handle_ecommerce_optimization(query, context)
        elif "audit" in query_lower:
            return self._handle_seo_audit(query, context)
        else:
            return self._handle_general_seo(query, context)

    def _handle_keyword_research(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        business = context.get("business") if context else None
        lines = [
            f"Keyword Research{' for ' + business if business else ''}",
            "",
            "I can help with:",
            "- Finding high-value keywords",
            "- Competitor keyword analysis",
            "- Long-tail keyword opportunities",
            "- Keyword difficulty assessment",
            "- Content gap analysis",
            "",
            "Specify: business/website and target topics.",
        ]
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"project_type": "keyword_research", "business": business},
        )

    def _handle_on_page_seo(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "On-Page SEO Optimization",
            "",
            "I can optimize:",
            "- Title tags and meta descriptions",
            "- Header structure (H1-H6)",
            "- Image alt text",
            "- Internal linking",
            "- Content optimization",
            "- Schema markup",
            "",
            "Specify: website and pages to optimize.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"project_type": "on_page"})

    def _handle_technical_seo(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Technical SEO",
            "",
            "I can help with:",
            "- Site speed optimization",
            "- Mobile responsiveness",
            "- XML sitemaps",
            "- Robots.txt configuration",
            "- Canonical tags",
            "- Structured data",
            "- Core Web Vitals",
            "",
            "Specify: website and technical issues to address.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"project_type": "technical_seo"})

    def _handle_ecommerce_optimization(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "eCommerce Optimization",
            "",
            "I can optimize:",
            "- Product page SEO",
            "- Category page structure",
            "- Checkout flow",
            "- Cart abandonment",
            "- Product descriptions",
            "- Site search functionality",
            "",
            "Specify: eCommerce platform and optimization goals.",
        ]
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"project_type": "ecommerce_optimization"},
        )

    def _handle_seo_audit(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "SEO Audit",
            "",
            "I can audit:",
            "- Overall SEO health",
            "- Technical issues",
            "- Content quality",
            "- Backlink profile",
            "- Competitor comparison",
            "- Mobile-friendliness",
            "",
            "Specify: website URL and audit scope.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"project_type": "seo_audit"})

    def _handle_general_seo(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "SEO & eCommerce Specialist Ready",
            "",
            "I can help with:",
            "- Keyword research and optimization",
            "- On-page and technical SEO",
            "- eCommerce conversion optimization",
            "- SEO audits and analysis",
            "- Site performance improvements",
            "",
            "What would you like me to optimize?",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _load_projects(self) -> List[SEOProject]:
        if not self.data_path.exists():
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            projects: List[SEOProject] = []
            for entry in data:
                try:
                    projects.append(
                        SEOProject(
                            website=entry.get("website", ""),
                            business=entry.get("business", ""),
                            project_type=entry.get("project_type", ""),
                            status=entry.get("status", "pending"),
                            priority=entry.get("priority", "medium"),
                            notes=entry.get("notes", ""),
                        )
                    )
                except Exception as exc:
                    LOGGER.debug("Skipping malformed SEO project: %s", exc)
            return projects
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

