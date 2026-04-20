from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from app.agents.base import AgentResponse, BaseAgent
from app.services.file_integrations import (
    FileIntegrationManager,
    RemoteFile,
)

LOGGER = logging.getLogger(__name__)
ENV_PATH = Path("config") / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:  # pragma: no cover
    load_dotenv()


@dataclass
class FileRecord:
    name: str
    path: str
    modified: datetime
    source: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "path": self.path,
            "modified": self.modified.isoformat(),
            "source": self.source,
        }


class FileAgent(BaseAgent):
    """Surfaces recent files across Dropbox, Google Drive, and OneDrive."""

    data_path = Path("data") / "sample_files.json"
    description = "Finds recent or relevant documents across connected drives."
    capabilities = [
        "Show recent files",
        "Search across storage providers",
        "Find documents by keyword",
        "Retrieve metadata for follow-up",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.integration_manager = FileIntegrationManager()

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        files = self._load_live_files() or self._load_sample_data()
        if not files:
            return AgentResponse(
                agent=self.name,
                content="No storage integrations configured yet.",
                data={"files": []},
                status="warning",
                warnings=["Connect Dropbox/Drive/OneDrive for live file summaries."],
            )

        files.sort(key=lambda record: record.modified, reverse=True)
        recent = files[:3]
        lines = [f"Recent files ({len(recent)} of {len(files)} total):"]
        for record in recent:
            timestamp = record.modified.strftime("%a %m/%d %I:%M %p").lstrip("0")
            lines.append(f"{record.name} from {record.source} ({timestamp})")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"files": [record.to_dict() for record in files]},
        )

    # Helpers ------------------------------------------------------------------
    def _load_live_files(self) -> List[FileRecord]:
        if not self.integration_manager.has_providers():
            return []
        remote = self.integration_manager.list_recent(limit=20)
        records: List[FileRecord] = []
        for item in remote:
            records.append(
                FileRecord(
                    name=item.name,
                    path=item.path,
                    modified=item.modified,
                    source=item.source,
                )
            )
        return records

    def _load_sample_data(self) -> List[FileRecord]:
        if not self.data_path.exists():
            LOGGER.info("Sample file data not found at %s", self.data_path)
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

        records: List[FileRecord] = []
        for entry in data:
            try:
                modified = datetime.fromisoformat(entry["modified"])
                if modified.tzinfo is None:
                    modified = modified.replace(tzinfo=timezone.utc)
                records.append(
                    FileRecord(
                        name=entry["name"],
                        path=entry["path"],
                        modified=modified,
                        source=entry.get("source", "Unknown"),
                    )
                )
            except Exception as exc:
                LOGGER.debug("Skipping malformed file entry: %s", exc)
        return records

