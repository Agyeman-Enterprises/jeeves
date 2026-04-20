"""
SEO Master Agent
Coordinates SEO specialists for search optimization and content strategy.
"""

from app.agents.base_master import MasterAgent
from typing import Dict, Any


class SEOMaster(MasterAgent):
    id = "master.seo"
    display_name = "SEO Master"
    domain = "seo"
    specialist_ids = [
        "spec.seo.seomi",
        "spec.seo.web_optimization",
        "spec.seo.content_gap",
        "spec.seo.competitor_keywords",
    ]

    def get_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "domain": self.domain,
            "specialist_count": len(self.specialist_ids),
        }

    def plan(self, objective: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return {
            "master": self.id,
            "objective": objective,
            "status": "planned",
            "note": "SEO planning logic to be implemented later.",
        }

