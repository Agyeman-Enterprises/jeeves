from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

from app.agents.base import AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)


@dataclass
class ContentItem:
    platform: str
    topic: str
    status: str
    due: date
    notes: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "platform": self.platform,
            "topic": self.topic,
            "status": self.status,
            "due": self.due.isoformat(),
            "notes": self.notes,
        }


class ContentAgent(BaseAgent):
    """Keeps track of content pipeline and can feed prompts to LLMs."""

    data_path = Path("data") / "sample_content_queue.json"
    description = "Tracks social content ideas/drafts across LinkedIn, X, IG, etc."
    capabilities = [
        "Summarize queued content",
        "Highlight drafts due today",
        "Feed prompts into the LLM for generation",
    ]

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        queue = self._load_sample_data()
        if not queue:
            return AgentResponse(
                agent=self.name,
                content="Content queue is empty. Connect planning docs to enable this agent.",
                data={"queue": []},
                status="warning",
                warnings=["Populate data/sample_content_queue.json or connect Notion."],
            )

        today = date.today()
        due_today = [item for item in queue if item.due == today]
        upcoming = [item for item in queue if item.due > today]

        lines = [
            f"In queue: {len(queue)}",
            f"Due today: {len(due_today)}",
            f"Upcoming: {len(upcoming)}",
        ]
        focus = due_today[:2] or upcoming[:2]
        for item in focus:
            lines.append(f"{item.platform}: {item.topic} ({item.status}, due {item.due})")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={
                "queue": [item.to_dict() for item in queue],
                "due_today": [item.to_dict() for item in due_today],
            },
        )

    # Helpers ------------------------------------------------------------------
    def _load_sample_data(self) -> List[ContentItem]:
        if not self.data_path.exists():
            LOGGER.info("Sample content data not found at %s", self.data_path)
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

        items: List[ContentItem] = []
        for entry in data:
            try:
                due = datetime.fromisoformat(entry["due"]).date()
                items.append(
                    ContentItem(
                        platform=entry["platform"],
                        topic=entry.get("topic", ""),
                        status=entry.get("status", "draft"),
                        due=due,
                        notes=entry.get("notes", ""),
                    )
                )
            except Exception as exc:
                LOGGER.debug("Skipping malformed content entry: %s", exc)
        return items


