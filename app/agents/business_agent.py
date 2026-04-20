from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.agents.base import AgentResponse, BaseAgent

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

LOGGER = logging.getLogger(__name__)
BUSINESS_CONFIG_PATH = Path("config") / "businesses.yaml"


@dataclass
class BusinessRecord:
    name: str
    category: str
    state: str
    entity: str
    ein: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "category": self.category,
            "state": self.state,
            "entity": self.entity,
            "ein": self.ein or "",
        }


class BusinessAgent(BaseAgent):
    """Answers structural questions about the user's business empire."""

    description = (
        "Provides structure, counts, and groupings for all businesses "
        "defined in config/businesses.yaml."
    )
    capabilities = [
        "List businesses by state",
        "Summarize category counts",
        "Highlight contractors and apps in development",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._records: List[BusinessRecord] = []
        self._apps: List[str] = []
        self._contractors: List[Dict[str, str]] = []
        self._phones: List[str] = []
        self._load_configuration()

    # BaseAgent ----------------------------------------------------------------
    def supports(self, query: str) -> bool:
        keywords = ["business", "company", "empire", "wyoming", "delaware"]
        lowered = query.lower()
        return any(word in lowered for word in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        if not self._records:
            return AgentResponse(
                agent=self.name,
                content="Business configuration file missing. "
                "Add config/businesses.yaml and restart.",
                data={},
                status="warning",
                warnings=["businesses.yaml not found or PyYAML not installed."],
            )

        state = self._extract_state(query)
        if state:
            matches = [record for record in self._records if record.state.lower() == state]
            if matches:
                lines = [f"Businesses in {state.title()}: {len(matches)}"]
                lines.extend(f"- {record.name} ({record.entity})" for record in matches)
                return AgentResponse(
                    agent=self.name,
                    content="\n".join(lines),
                    data={"businesses": [record.to_dict() for record in matches]},
                )

        category_counts = self._category_counts()
        lines = [
            f"Total businesses tracked: {len(self._records)}",
            "By category:",
        ]
        lines.extend(f"- {category}: {count}" for category, count in category_counts)
        if self._apps:
            lines.append(f"Apps in development: {len(self._apps)}")
        if self._contractors:
            lines.append(
                "Key contractors: "
                + ", ".join(contractor["name"] for contractor in self._contractors)
            )

        data = {
            "businesses": [record.to_dict() for record in self._records],
            "apps_in_development": self._apps,
            "contractors": self._contractors,
            "phones": self._phones,
        }
        return AgentResponse(agent=self.name, content="\n".join(lines), data=data)

    # Helpers ------------------------------------------------------------------
    def _load_configuration(self) -> None:
        if yaml is None:
            LOGGER.warning(
                "PyYAML is not installed. BusinessAgent will return a warning until "
                "you `pip install pyyaml`."
            )
            return

        if not BUSINESS_CONFIG_PATH.exists():
            LOGGER.warning("businesses.yaml not found at %s", BUSINESS_CONFIG_PATH)
            return

        config = yaml.safe_load(BUSINESS_CONFIG_PATH.read_text(encoding="utf-8"))
        businesses = config.get("businesses", {}) if isinstance(config, dict) else {}
        for category, entries in businesses.items():
            for entry in entries or []:
                try:
                    self._records.append(
                        BusinessRecord(
                            name=entry["name"],
                            category=category,
                            state=str(entry.get("state", "unknown")),
                            entity=str(entry.get("entity", "business")),
                            ein=entry.get("ein"),
                        )
                    )
                except KeyError as exc:
                    LOGGER.debug("Skipping malformed business entry: %s", exc)

        apps = config.get("apps_in_development", []) if isinstance(config, dict) else []
        self._apps = apps if isinstance(apps, list) else []

        contractors = config.get("contractors", []) if isinstance(config, dict) else []
        self._contractors = contractors if isinstance(contractors, list) else []

        phones = config.get("phones", []) if isinstance(config, dict) else []
        self._phones = phones if isinstance(phones, list) else []

    def _category_counts(self) -> List[Tuple[str, int]]:
        counts: Dict[str, int] = {}
        for record in self._records:
            counts[record.category] = counts.get(record.category, 0) + 1
        return sorted(counts.items(), key=lambda item: item[0])

    @staticmethod
    def _extract_state(query: str) -> Optional[str]:
        states = [
            "wyoming",
            "california",
            "delaware",
            "hawaii",
            "guam",
            "remote",
        ]
        lowered = query.lower()
        for state in states:
            if state in lowered:
                return state
        return None


