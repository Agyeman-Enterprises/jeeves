"""
Action Dispatcher — JJ dispatches work to agents, then reports.
JJ never says "you should post more." JJ says "ContentForge has 3 posts ready. Approve?"
"""
from __future__ import annotations
import logging
import re
from typing import Dict, List, Optional
import httpx
from app.config import get_settings

LOGGER = logging.getLogger(__name__)


class ActionDispatcher:
    def __init__(self):
        s = get_settings()
        self.contentforge_url = "https://contentforge-nine.vercel.app"
        self.neuralia_url = "https://neuralia.vercel.app"
        self.stratova_url = "https://stratova.vercel.app"
        self._key = s.nexus_internal_key

    async def dispatch_content(self, business_name: str, content_type: str = "social", count: int = 3) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(f"{self.contentforge_url}/api/generate",
                    json={"business": business_name, "type": content_type, "count": count},
                    headers=self._auth_headers())
                resp.raise_for_status()
                data = resp.json()
                drafts = data.get("drafts", data.get("posts", []))
                LOGGER.info("[Dispatch] ContentForge: %d drafts for %s", len(drafts), business_name)
                return {"status": "ready", "business": business_name, "drafts": drafts}
        except Exception as exc:
            LOGGER.warning("[Dispatch] ContentForge failed: %s", exc)
            return {"status": "error", "business": business_name, "error": str(exc)}

    async def dispatch_lead_scan(self, business_name: str, target_audience: str = "") -> Dict:
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(f"{self.neuralia_url}/api/scan",
                    json={"business": business_name, "audience": target_audience},
                    headers=self._auth_headers())
                resp.raise_for_status()
                data = resp.json()
                leads = data.get("leads", data.get("results", []))
                return {"status": "ready", "business": business_name, "leads": leads}
        except Exception as exc:
            LOGGER.warning("[Dispatch] Neuralia failed: %s", exc)
            return {"status": "error", "business": business_name, "error": str(exc)}

    async def dispatch_strategy(self, business_name: str, goal: str = "growth") -> Dict:
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(f"{self.stratova_url}/api/strategy",
                    json={"business": business_name, "goal": goal},
                    headers=self._auth_headers())
                resp.raise_for_status()
                return {"status": "ready", "business": business_name, "brief": resp.json()}
        except Exception as exc:
            LOGGER.warning("[Dispatch] Stratova failed: %s", exc)
            return {"status": "error", "business": business_name, "error": str(exc)}

    async def dispatch_meal_plan(self, preferences: Optional[Dict] = None) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get("https://www.marleyspoon.com/menu",
                    headers={"User-Agent": "Mozilla/5.0 (compatible; JJ-Butler/1.0)"},
                    follow_redirects=True)
                titles = re.findall(r'"name"\s*:\s*"([^"]{10,60})"', resp.text)[:10]
                if not titles:
                    titles = ["Sheet Pan Lemon Herb Salmon", "Cauliflower Rice Stir-Fry",
                              "Zucchini Noodles Turkey Bolognese", "Egg-Stuffed Avocado", "Greek Chicken Bowl"]
                return {"status": "ready", "recipes": titles[:5],
                        "note": "Reply 'shopping list' to generate ingredients."}
        except Exception as exc:
            LOGGER.warning("[Dispatch] Meal plan failed: %s", exc)
            return {"status": "error", "error": str(exc),
                    "recipes": ["Sheet Pan Salmon", "Chicken Bowl", "Egg Avocado"]}

    def _auth_headers(self) -> Dict:
        h = {"Content-Type": "application/json"}
        if self._key:
            h["Authorization"] = f"Bearer {self._key}"
        return h
