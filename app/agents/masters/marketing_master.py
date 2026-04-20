"""
Marketing Master Agent
Coordinates marketing specialists for campaigns, content, and brand management.
"""

from app.agents.base_master import MasterAgent
from app.brands.needful_things import NEEDFUL_THINGS_BRAND
from app.ai.local_llm import run_llm
from typing import Dict, Any


class MarketingMaster(MasterAgent):
    id = "master.marketing"
    display_name = "Marketing Master"
    domain = "marketing"
    specialist_ids = [
        "spec.marketing.soshie",
        "spec.marketing.emmie",
        "spec.marketing.penn",
        "spec.marketing.milli",
        "spec.marketing.commet",
        "spec.marketing.content_automation",
        "spec.marketing.brand_consistency",
        "spec.marketing.video_script",
        "spec.marketing.ad_creative",
    ]

    def get_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "domain": self.domain,
            "specialist_count": len(self.specialist_ids),
        }

    def plan(self, objective: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        High-level marketing strategy generator for Needful Things.
        """
        brand = NEEDFUL_THINGS_BRAND

        system_prompt = (
            "You are the Marketing Master for a luxury boutique brand. "
            "Produce a refined, aesthetic, luxury marketing plan using the brand tone rules."
        )

        user_prompt = f"""
Brand Name: {brand['name']}
Tone: {brand['tone']}
Voice Rules: {brand['voice_rules']}
Content Pillars: {brand['content_pillars']}
Objective: {objective}

Generate a high-level plan with:
- content themes
- posting rhythm recommendations
- tone guidelines
- seasonal hooks
"""

        plan_text = run_llm(user_prompt, system_prompt)

        return {
            "master": self.id,
            "objective": objective,
            "strategy": plan_text,
        }

