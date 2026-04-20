from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from app.agents.base import AgentResponse, BaseAgent
from app.services.task_integrations import (
    RemoteTask,
    TaskIntegrationManager,
)

LOGGER = logging.getLogger(__name__)
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
ENV_PATH = Path("config") / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:  # pragma: no cover
    load_dotenv()


@dataclass
class TaskRecord:
    title: str
    due: date
    priority: str
    source: str
    business: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "due": self.due.isoformat(),
            "priority": self.priority,
            "source": self.source,
            "business": self.business,
        }


class TaskAgent(BaseAgent):
    """Aggregates tasks from Notion, Todoist, ClickUp, and Akiflow."""

    data_path = Path("data") / "sample_tasks.json"
    description = "Surfaces top priorities and overdue tasks across workspaces."
    capabilities = [
        "Show today's priorities",
        "Highlight overdue work",
        "Filter by business line",
        "Unify tasks across tools",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.integration_manager = TaskIntegrationManager()

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        tasks = self._load_live_tasks() or self._load_sample_data()
        if not tasks:
            return AgentResponse(
                agent=self.name,
                content="No task integrations configured yet.",
                data={"tasks": []},
                status="warning",
                warnings=["Connect Notion/Todoist/ClickUp/Akiflow for live tasks."],
            )

        today = date.today()
        overdue = [task for task in tasks if task.due < today]
        due_today = [task for task in tasks if task.due == today]
        upcoming = [task for task in tasks if task.due > today]

        lines = [
            f"Overdue: {len(overdue)}",
            f"Due today: {len(due_today)}",
            f"Upcoming: {len(upcoming)}",
        ]

        important = sorted(
            overdue + due_today,
            key=lambda task: (PRIORITY_ORDER.get(task.priority.lower(), 9), task.due),
        )[:3]

        for record in important:
            lines.append(
                f"{record.priority.upper()} - {record.title} "
                f"(due {record.due.isoformat()}, {record.source})"
            )

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={
                "overdue": [task.to_dict() for task in overdue],
                "due_today": [task.to_dict() for task in due_today],
                "upcoming": [task.to_dict() for task in upcoming],
            },
        )

    # Helpers ------------------------------------------------------------------
    def _load_live_tasks(self) -> List[TaskRecord]:
        if not self.integration_manager.has_providers():
            return []
        remote_tasks = self.integration_manager.fetch_all()
        records: List[TaskRecord] = []
        for task in remote_tasks:
            if not task.due:
                continue
            records.append(
                TaskRecord(
                    title=task.title,
                    due=task.due,
                    priority=task.priority,
                    source=task.source,
                    business=task.business,
                )
            )
        return records

    def _load_sample_data(self) -> List[TaskRecord]:
        if not self.data_path.exists():
            LOGGER.info("Sample task data not found at %s", self.data_path)
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

        records: List[TaskRecord] = []
        for entry in data:
            try:
                due = datetime.fromisoformat(entry["due"]).date()
                records.append(
                    TaskRecord(
                        title=entry["title"],
                        due=due,
                        priority=entry.get("priority", "medium"),
                        source=entry.get("source", "Unknown"),
                        business=entry.get("business", "General"),
                    )
                )
            except Exception as exc:
                LOGGER.debug("Skipping malformed task entry: %s", exc)
        return records

