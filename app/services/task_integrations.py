from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional

import requests

LOGGER = logging.getLogger(__name__)


@dataclass
class RemoteTask:
    title: str
    due: Optional[date]
    priority: str
    source: str
    business: str = "General"

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "due": self.due.isoformat() if self.due else "",
            "priority": self.priority,
            "source": self.source,
            "business": self.business,
        }


class TaskProviderError(RuntimeError):
    pass


class BaseTaskProvider:
    name = "task-provider"

    def fetch_tasks(self) -> List[RemoteTask]:
        raise NotImplementedError


class NotionTaskProvider(BaseTaskProvider):
    name = "Notion"
    base_url = "https://api.notion.com/v1/databases"

    def __init__(self, api_key: str, database_id: str) -> None:
        self.api_key = api_key
        self.database_id = database_id

    def fetch_tasks(self) -> List[RemoteTask]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
        }
        url = f"{self.base_url}/{self.database_id}/query"
        try:
            response = requests.post(url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            raise TaskProviderError(f"Notion request failed: {exc}") from exc

        results = response.json().get("results", [])
        tasks: List[RemoteTask] = []
        for item in results:
            props = item.get("properties", {})
            title = self._extract_title(props)
            due = self._extract_due(props)
            priority = self._extract_priority(props)
            business = self._extract_business(props)
            tasks.append(
                RemoteTask(
                    title=title,
                    due=due,
                    priority=priority,
                    source=self.name,
                    business=business,
                )
            )
        return tasks

    @staticmethod
    def _extract_title(props: Dict[str, Dict]) -> str:
        name = props.get("Name", {})
        rich_text = name.get("title", [])
        if rich_text:
            return rich_text[0].get("plain_text", "Untitled task")
        return "Untitled task"

    @staticmethod
    def _extract_due(props: Dict[str, Dict]) -> Optional[date]:
        due = props.get("Due", {}).get("date")
        if due and due.get("start"):
            return datetime.fromisoformat(due["start"]).date()
        return None

    @staticmethod
    def _extract_priority(props: Dict[str, Dict]) -> str:
        select = props.get("Priority", {}).get("select")
        return select["name"] if select else "medium"

    @staticmethod
    def _extract_business(props: Dict[str, Dict]) -> str:
        select = props.get("Business", {}).get("select")
        return select["name"] if select else "General"


class TodoistTaskProvider(BaseTaskProvider):
    name = "Todoist"
    base_url = "https://api.todoist.com/rest/v2/tasks"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def fetch_tasks(self) -> List[RemoteTask]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(self.base_url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            raise TaskProviderError(f"Todoist request failed: {exc}") from exc

        tasks: List[RemoteTask] = []
        for item in response.json():
            due = item.get("due", {}).get("date")
            tasks.append(
                RemoteTask(
                    title=item.get("content", "Todoist Task"),
                    due=datetime.fromisoformat(due).date() if due else None,
                    priority=self._map_priority(item.get("priority", 1)),
                    source=self.name,
                    business="Personal",
                )
            )
        return tasks

    @staticmethod
    def _map_priority(value: int) -> str:
        mapping = {1: "low", 2: "medium", 3: "high", 4: "high"}
        return mapping.get(value, "medium")


class ClickUpTaskProvider(BaseTaskProvider):
    name = "ClickUp"
    base_url = "https://api.clickup.com/api/v2"

    def __init__(self, api_key: str, list_id: str) -> None:
        self.api_key = api_key
        self.list_id = list_id

    def fetch_tasks(self) -> List[RemoteTask]:
        headers = {"Authorization": self.api_key}
        url = f"{self.base_url}/list/{self.list_id}/task"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            raise TaskProviderError(f"ClickUp request failed: {exc}") from exc

        tasks: List[RemoteTask] = []
        for item in response.json().get("tasks", []):
            due = item.get("due_date")
            tasks.append(
                RemoteTask(
                    title=item.get("name", "ClickUp Task"),
                    due=datetime.fromtimestamp(int(due) / 1000).date()
                    if due
                    else None,
                    priority=item.get("priority", {}).get("priority", "medium"),
                    source=self.name,
                    business=item.get("folder", {}).get("name", "General"),
                )
            )
        return tasks


class AkiflowTaskProvider(BaseTaskProvider):
    name = "Akiflow"
    base_url = "https://api.akiflow.com/v1/tasks"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def fetch_tasks(self) -> List[RemoteTask]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(self.base_url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            raise TaskProviderError(f"Akiflow request failed: {exc}") from exc

        tasks: List[RemoteTask] = []
        for item in response.json().get("tasks", []):
            due = item.get("due_at")
            tasks.append(
                RemoteTask(
                    title=item.get("title", "Akiflow Task"),
                    due=datetime.fromisoformat(due).date() if due else None,
                    priority=item.get("priority", "medium"),
                    source=self.name,
                    business=item.get("workspace", "General"),
                )
            )
        return tasks


class TaskIntegrationManager:
    """Aggregates tasks from whichever providers have credentials configured."""

    def __init__(self) -> None:
        self.providers: List[BaseTaskProvider] = []
        self._configure()

    def _configure(self) -> None:
        notion_key = os.getenv("NOTION_API_KEY")
        notion_db = os.getenv("NOTION_TASKS_DATABASE_ID")
        if notion_key and notion_db:
            self.providers.append(NotionTaskProvider(notion_key, notion_db))

        todoist_key = os.getenv("TODOIST_API_KEY")
        if todoist_key:
            self.providers.append(TodoistTaskProvider(todoist_key))

        clickup_key = os.getenv("CLICKUP_API_KEY")
        clickup_list = os.getenv("CLICKUP_LIST_ID")
        if clickup_key and clickup_list:
            self.providers.append(ClickUpTaskProvider(clickup_key, clickup_list))

        akiflow_key = os.getenv("AKIFLOW_API_KEY")
        if akiflow_key:
            self.providers.append(AkiflowTaskProvider(akiflow_key))

    def fetch_all(self) -> List[RemoteTask]:
        tasks: List[RemoteTask] = []
        for provider in self.providers:
            try:
                tasks.extend(provider.fetch_tasks())
            except TaskProviderError as exc:
                LOGGER.warning("%s skipped: %s", provider.name, exc)
        return tasks

    def has_providers(self) -> bool:
        return bool(self.providers)


