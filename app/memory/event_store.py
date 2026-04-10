"""
Event Store — Layer 1-2: Ingest and persist normalized events.
Every input to Jeeves (voice, text, calendar, email, SMS, OCR, repo)
becomes a NormalizedEvent stored in Supabase.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from app.db import get_db
from app.schemas.events import EventModality, EventSource, NormalizedEvent

LOGGER = logging.getLogger(__name__)

TABLE = "jeeves_events"


class EventStore:
    """Persist and query normalized events."""

    def ingest(self, event: NormalizedEvent) -> str:
        """Store an event. Returns event ID."""
        db = get_db()
        event_id = event.id or str(uuid4())
        row = {
            "id": event_id,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source.value,
            "modality": event.modality.value,
            "raw_text": event.raw_text,
            "structured_payload": event.structured_payload,
            "entities": event.entities,
            "duration_minutes": event.duration_minutes,
            "linked_goals": event.linked_goals,
            "valence": event.valence,
            "arousal": event.arousal,
            "certainty": event.certainty,
            "inferred_tags": event.inferred_tags,
            "self_reported_intent": event.self_reported_intent,
            "inferred_intent": event.inferred_intent,
        }
        if db:
            try:
                db.table(TABLE).insert(row).execute()
            except Exception as exc:
                LOGGER.error("Event store insert failed: %s", exc)
        LOGGER.info("Event ingested: %s [%s] %s", event.source.value, event_id[:8], event.raw_text[:60])
        return event_id

    def query(
        self,
        hours: int = 24,
        source: Optional[EventSource] = None,
        goal_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Query recent events."""
        db = get_db()
        if not db:
            return []
        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            q = db.table(TABLE).select("*").gte("timestamp", since).order("timestamp", desc=True).limit(limit)
            if source:
                q = q.eq("source", source.value)
            if goal_id:
                q = q.contains("linked_goals", [goal_id])
            res = q.execute()
            return res.data or []
        except Exception as exc:
            LOGGER.error("Event store query failed: %s", exc)
            return []

    def count_by_goal(self, goal_id: str, hours: int = 168) -> Dict:
        """Count events supporting vs contradicting a goal in the last N hours."""
        events = self.query(hours=hours, goal_id=goal_id, limit=500)
        supports = sum(1 for e in events if e.get("valence", 0) > 0)
        contradicts = sum(1 for e in events if e.get("valence", 0) < 0)
        neutral = len(events) - supports - contradicts
        return {"supports": supports, "contradicts": contradicts, "neutral": neutral, "total": len(events)}

    def recent_by_category(self, hours: int = 24) -> Dict[str, int]:
        """Count recent events grouped by inferred category."""
        events = self.query(hours=hours, limit=500)
        counts: Dict[str, int] = {}
        for e in events:
            for tag in e.get("inferred_tags", []):
                counts[tag] = counts.get(tag, 0) + 1
        return counts
