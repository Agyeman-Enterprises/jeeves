"""
Suggestion Engine — JJ decides what to DO and suggests it.
Action-first, butler tone. Never lectures, never shames.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.modeling.weighting_engine import WeightingEngine
from app.modeling.mimograph import Mimograph

LOGGER = logging.getLogger(__name__)


class Suggestion:
    def __init__(self, text: str, action_type: str, category: str,
                 urgency: float = 0.5, requires_response: bool = False,
                 agent: Optional[str] = None, context: Optional[Dict] = None):
        self.text = text
        self.action_type = action_type
        self.category = category
        self.urgency = urgency
        self.requires_response = requires_response
        self.agent = agent
        self.context = context or {}

    def to_dict(self) -> Dict:
        return {"text": self.text, "action_type": self.action_type,
                "category": self.category, "urgency": self.urgency,
                "requires_response": self.requires_response,
                "agent": self.agent, "context": self.context}


class SuggestionEngine:
    """
    Generates proactive, action-first suggestions.
    JJ dispatches first, reports second.
    One clean ask per topic. No repeated nagging.
    """

    def __init__(self, weighting: WeightingEngine, mimograph: Mimograph):
        self.weighting = weighting
        self.mimograph = mimograph
        self._suggested_today: set = set()

    def generate(self, weather: Optional[Dict] = None,
                 calendar_events: Optional[List[Dict]] = None,
                 nexus_alerts: Optional[List[Dict]] = None,
                 energy_profile: str = "normal",
                 max_suggestions: int = 4) -> List[Suggestion]:
        candidates: List[Suggestion] = []
        calendar_events = calendar_events or []
        nexus_alerts = nexus_alerts or []

        # 1. Business / Revenue from Nexus alerts
        for alert in nexus_alerts[:3]:
            entity = alert.get("entity_name", "a business")
            alert_type = alert.get("type", "")
            if alert_type in ("no_revenue", "stalled", "needs_attention"):
                candidates.append(Suggestion(
                    text=f"Neuralia can scan leads for {entity}. Want me to kick it off?",
                    action_type="approval_needed", category="business", urgency=0.7,
                    requires_response=True, agent="neuralia", context={"entity": entity}))

        # 2. Content dispatch for stalled businesses
        goals = self.weighting.get_goals()
        business_goals = [g for g in goals if g.get("category") == "business"
                          and g.get("effective_weight", 0) > 0.5]
        for bg in business_goals[:2]:
            label = bg.get("label", "your business")
            days_since = self._days_since(bg.get("last_evidence_at"))
            if days_since > 4 and "content" not in self._suggested_today:
                candidates.append(Suggestion(
                    text=f"ContentForge can draft 3 posts for {label} — want me to queue them?",
                    action_type="approval_needed", category="work", urgency=0.65,
                    requires_response=True, agent="contentforge",
                    context={"goal": label, "days_since": days_since}))
                self._suggested_today.add("content")
                break

        # 3. Health / Exercise (weather + energy aware)
        if weather and energy_profile not in ("post_shift_low",):
            temp = weather.get("temp_f", 80)
            condition = weather.get("condition", "").lower()
            is_good = temp > 75 and "rain" not in condition and "storm" not in condition
            if is_good and "swim" not in self._suggested_today:
                candidates.append(Suggestion(
                    text=f"It's {temp}°F and clear. Good window for a swim around 4pm if you're home.",
                    action_type="heads_up", category="health", urgency=0.4))
                self._suggested_today.add("swim")

        # 4. Meal planning
        if "meal" not in self._suggested_today:
            candidates.append(Suggestion(
                text="Want me to pull this week's Marley Spoon menu and build a shopping list?",
                action_type="question", category="health", urgency=0.35,
                requires_response=True, agent="meal_planner"))
            self._suggested_today.add("meal")

        # 5. Shift heads-up
        shifts = [e for e in calendar_events
                  if any(k in e.get("summary", "").lower()
                         for k in ["shift", "gmh", "hospital", "call"])]
        if shifts and "shift_heads_up" not in self._suggested_today:
            candidates.append(Suggestion(
                text=f"You have a shift today ({shifts[0].get('summary', 'GMH')}). "
                     f"Non-urgent items held.",
                action_type="heads_up", category="life", urgency=0.5))
            self._suggested_today.add("shift_heads_up")

        # 6. Finance / TaxRx
        finance_goals = [g for g in goals if g.get("category") == "finance"
                         and g.get("effective_weight", 0) > 0.5]
        if finance_goals and "finance" not in self._suggested_today:
            candidates.append(Suggestion(
                text="I can pull your latest GMH shift log and update TaxRx. Run it now?",
                action_type="approval_needed", category="finance", urgency=0.55,
                requires_response=True, agent="taxrx"))
            self._suggested_today.add("finance")

        candidates.sort(key=lambda s: s.urgency, reverse=True)
        return candidates[:max_suggestions]

    def reset_daily(self):
        self._suggested_today.clear()

    @staticmethod
    def _days_since(iso_timestamp: Optional[str]) -> int:
        if not iso_timestamp:
            return 999
        try:
            dt = datetime.fromisoformat(str(iso_timestamp).replace("Z", "+00:00"))
            return (datetime.now(tz=timezone.utc) - dt).days
        except (ValueError, TypeError):
            return 999
