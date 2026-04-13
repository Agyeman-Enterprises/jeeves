"""
Orchestrator — JJ's brain. v2.1
Adds: GoogleService, ProfileBuilder, evening_checkin, email triage, calendar awareness.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional
from app.config import get_settings
from app.core.context_assembler import ContextAssembler
from app.core.profile_builder import ProfileBuilder
from app.core.suggestion_engine import SuggestionEngine
from app.core.planner import Planner
from app.integrations.alrtme_client import AlrtMeClient
from app.integrations.ghexit_client import GhexitClient
from app.integrations.litellm_client import LLMClient
from app.integrations.nexus_client import NexusClient
from app.memory.aqui_client import AquiClient
from app.memory.event_store import EventStore
from app.modeling.contradiction_engine import ContradictionEngine
from app.modeling.mimograph import Mimograph
from app.modeling.weighting_engine import WeightingEngine
from app.services.action_dispatcher import ActionDispatcher
from app.services.google_service import GoogleService

LOGGER = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        LOGGER.info("[JJ] Initializing...")
        self.event_store = EventStore()
        self.aqui = AquiClient()
        self.mimograph = Mimograph()
        self.weighting = WeightingEngine(event_store=self.event_store)
        self.contradictions = ContradictionEngine(weighting=self.weighting, mimograph=self.mimograph)
        self.planner = Planner(weighting=self.weighting, mimograph=self.mimograph)
        self.suggestions = SuggestionEngine(weighting=self.weighting, mimograph=self.mimograph)
        self.profile = ProfileBuilder()
        self.context = ContextAssembler(weighting=self.weighting, mimograph=self.mimograph,
                                        event_store=self.event_store, aqui=self.aqui)
        self.llm = LLMClient()
        self.nexus = NexusClient()
        self.ghexit = GhexitClient()
        self.alrtme = AlrtMeClient()
        self.google = GoogleService()
        self.dispatcher = ActionDispatcher()
        LOGGER.info("[JJ] Ready.")

    async def chat(self, message: str, session_id: str = "default") -> str:
        profile_summary = self.profile.get_profile_summary()
        system_context = await self.context.assemble(user_message=message)
        response = await self.llm.complete(
            messages=[{"role": "user", "content": message}],
            system=f"{system_context}\n\n{profile_summary}",
            temperature=0.7, max_tokens=2000)
        from app.schemas.events import EventSource, NormalizedEvent
        self.event_store.ingest(NormalizedEvent(source=EventSource.TEXT,
            raw_text=f"User: {message}\nJJ: {response[:200]}", inferred_tags=["conversation"]))
        return response

    async def morning_briefing(self, weather: Optional[Dict] = None) -> Dict:
        plan = self.planner.generate_day_plan()
        nexus_alerts = await self.nexus.get_alerts()
        emails_needing_response = await self.google.get_emails_needing_response(hours_back=24)
        today_events = await self.google.get_todays_events()
        shifts_today = self.google.detect_shifts(today_events)
        free_blocks = self.google.get_free_blocks(today_events)
        energy_profile = "post_shift_low" if shifts_today else plan.energy_profile
        suggestions = self.suggestions.generate(weather=weather, calendar_events=today_events,
            nexus_alerts=nexus_alerts, energy_profile=energy_profile, max_suggestions=3)
        daily_question = self.profile.get_next_question()
        goals = self.weighting.get_goals()
        top_goal_labels = [g["label"] for g in goals[:3]]

        if emails_needing_response:
            email_lines = [f"{e['from'].split('<')[0].strip()}: {e['subject'][:50]}"
                           for e in emails_needing_response[:3]]
            email_summary = "Emails needing response:\n" + "\n".join(f"  - {l}" for l in email_lines)
        else:
            email_summary = "Inbox clear — no emails need your attention from the last 24 hours."

        if today_events:
            cal_lines = [f"{e['summary']} at {e['start'][11:16] if 'T' in e['start'] else 'all day'}"
                         for e in today_events[:5]]
            calendar_summary = "Today: " + ", ".join(cal_lines)
        else:
            calendar_summary = "Calendar is clear today."

        free_hint = ""
        if free_blocks and weather:
            b = free_blocks[0]
            if weather.get("condition") == "clear" and weather.get("temp_f", 0) > 75:
                free_hint = f"Free block {b['start']}–{b['end']} ({b['hours']}h) — good weather for a swim."

        suggestion_lines = "\n".join(f"  - {s.text}" for s in suggestions) or "  - Nothing urgent today."

        briefing_prompt = f"""You are JJ, Dr. Akua Agyeman's personal butler.
Generate her morning briefing for {plan.date}.

CALENDAR:
{calendar_summary}
{f"Shifts today: {len(shifts_today)}" if shifts_today else "No hospital shifts today."}
{free_hint}

EMAIL:
{email_summary}

READY TO ACTION:
{suggestion_lines}

ACTIVE PRIORITIES: {', '.join(top_goal_labels)}

{"CLOSE WITH — 'One question for you today: ' + " + repr(daily_question['text']) if daily_question else ""}

RULES:
- Warm good morning + today's date
- Calendar and shifts first
- Email triage second (name and subject only)
- Action items third — options not commands
- Daily question to close if provided
- Under 200 words. Zero judgment. Zero pressure. Butler tone."""

        system = await self.context.assemble()
        profile_ctx = self.profile.get_profile_summary()
        text = await self.llm.complete(
            messages=[{"role": "user", "content": briefing_prompt}],
            system=f"{system}\n\n{profile_ctx}", max_tokens=700)

        return {"date": plan.date, "text": text,
                "emails_needing_response": len(emails_needing_response),
                "shifts_today": len(shifts_today), "free_blocks": free_blocks,
                "suggestions": [s.to_dict() for s in suggestions],
                "daily_question": daily_question, "energy_profile": energy_profile}

    async def evening_checkin(self) -> Dict:
        questions = self.profile.get_check_in_questions(count=2)
        answer_count = self.profile.get_answer_count()
        coverage = self.profile.get_domain_coverage()
        checkin_prompt = f"""You are JJ, Dr. Akua Agyeman's personal butler. It's evening.
Generate a brief check-in message.
Profile answers so far: {answer_count}
Domains: {', '.join(f"{k}:{v}" for k, v in coverage.items()) or 'none yet'}
Questions to weave in naturally:
{chr(10).join(f"  {i+1}. {q['text']}" for i, q in enumerate(questions))}
RULES: Acknowledge end of day warmly in one sentence. Ask questions conversationally.
Under 100 words. Trusted colleague tone, not therapist."""
        system = await self.context.assemble()
        text = await self.llm.complete(
            messages=[{"role": "user", "content": checkin_prompt}],
            system=system, max_tokens=300)
        return {"text": text, "questions": questions, "answer_count": answer_count}

    async def record_checkin_answer(self, question_id: str, answer: str) -> Dict:
        success = self.profile.record_answer(question_id, answer)
        if success:
            from app.schemas.events import EventSource, NormalizedEvent
            self.event_store.ingest(NormalizedEvent(source=EventSource.CHECKIN,
                raw_text=f"Profile answer [{question_id}]: {answer[:300]}",
                inferred_tags=["profile", "self_report"]))
        return {"status": "recorded" if success else "error", "question_id": question_id}

    async def health_check(self) -> Dict:
        aqui_ok = await self.aqui.health()
        nexus_ok = await self.nexus.health()
        ghexit_ok = await self.ghexit.health()
        google_ok = await self.google.health()
        goals = self.weighting.get_goals()
        return {"status": "alive", "version": get_settings().version,
                "services": {"aqui": "ok" if aqui_ok else "down",
                             "nexus": "ok" if nexus_ok else "down",
                             "ghexit": "ok" if ghexit_ok else "down",
                             "google": "ok" if google_ok else "down (check credentials)"},
                "brain": {"goals_tracked": len(goals),
                          "profile_answers": self.profile.get_answer_count(),
                          "domain_coverage": self.profile.get_domain_coverage()}}

_instance: Optional[Orchestrator] = None

def get_orchestrator() -> Orchestrator:
    global _instance
    if _instance is None:
        _instance = Orchestrator()
    return _instance
