"""
Social Media Manager Specialist (Soshie)
Handles social media content and campaigns.
"""

from app.agents.base_specialist import SpecialistAgent
from app.ai.local_llm import run_llm
from app.brands.needful_things import NEEDFUL_THINGS_BRAND
from typing import Dict, Any


class SocialMediaManager(SpecialistAgent):
    id = "spec.marketing.soshie"
    display_name = "Social Media Manager (Soshie)"
    master_id = "master.marketing"
    role = "social_media"

    def get_summary(self) -> Dict[str, Any]:
        return {"id": self.id, "display_name": self.display_name, "role": self.role}

    def run_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        brand = NEEDFUL_THINGS_BRAND
        brand_name = brand["name"]

        if task_type == "generate_posts":
            count = payload.get("count", 5)
            system_prompt = (
                "You are a luxury social media copywriter. "
                "Write refined, elegant, aesthetic posts for a boutique brand."
            )
            user_prompt = f"""
Brand: {brand_name}
Tone: {brand['tone']}
Voice Rules: {brand['voice_rules']}
Content Pillars: {brand['content_pillars']}

Generate {count} Instagram-style posts.
Each post:
- 2–3 sentences max
- luxury + aesthetic
- poetic sensory language
- no hashtags included
"""
            posts = run_llm(user_prompt, system_prompt)

            return {
                "specialist": self.id,
                "task_type": task_type,
                "posts": posts,
            }

        if task_type == "content_calendar":
            system_prompt = "You are an elite luxury content planner."
            user_prompt = f"""
Brand: {brand_name}
Tone: {brand['tone']}
Voice: {brand['voice_rules']}

Create a 7-day content calendar with:
- post theme
- description
- suggested visual style
- CTA (subtle, elegant)
"""
            cal = run_llm(user_prompt, system_prompt)
            return {"specialist": self.id, "calendar": cal}

        if task_type == "hashtags":
            system_prompt = "You are an SEO/hashtag strategist for luxury brands."
            user_prompt = f"""
Generate 20 hashtags for {brand_name} with a luxury aesthetic vibe.
"""
            tags = run_llm(user_prompt, system_prompt)
            return {"specialist": self.id, "hashtags": tags}

        if task_type == "reels_script" or task_type == "tiktok_script":
            system_prompt = "You are a luxury short-form video scriptwriter."
            duration = payload.get("duration", "15-30 seconds")
            user_prompt = f"""
Brand: {brand_name}
Tone: {brand['tone']}
Voice Rules: {brand['voice_rules']}

Create a {duration} Reels/TikTok script for {brand_name}.
Include:
- hook (first 3 seconds)
- main content
- CTA
- visual cues
- music/style notes
"""
            script = run_llm(user_prompt, system_prompt)
            return {"specialist": self.id, "script": script}

        return {
            "specialist": self.id,
            "status": "unknown_task",
            "task_type": task_type,
        }

