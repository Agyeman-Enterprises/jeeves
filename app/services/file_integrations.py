from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import requests

LOGGER = logging.getLogger(__name__)


@dataclass
class RemoteFile:
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


class FileProviderError(RuntimeError):
    pass


class BaseFileProvider:
    name = "file-provider"

    def list_recent(self, limit: int = 20) -> List[RemoteFile]:
        raise NotImplementedError


class DropboxProvider(BaseFileProvider):
    name = "Dropbox"
    api_url = "https://api.dropboxapi.com/2/files/list_folder"

    def __init__(self, access_token: str, root_path: str = "") -> None:
        self.access_token = access_token
        self.root_path = root_path

    def list_recent(self, limit: int = 20) -> List[RemoteFile]:
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"path": self.root_path, "recursive": True, "limit": limit}
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            raise FileProviderError(f"Dropbox request failed: {exc}") from exc

        entries = response.json().get("entries", [])
        files: List[RemoteFile] = []
        for entry in entries:
            if entry.get(".tag") != "file":
                continue
            files.append(
                RemoteFile(
                    name=entry["name"],
                    path=entry["path_display"],
                    modified=datetime.fromisoformat(entry["client_modified"].replace("Z", "+00:00")),
                    source=self.name,
                )
            )
        return files[:limit]


class GoogleDriveProvider(BaseFileProvider):
    name = "Google Drive"
    api_url = "https://www.googleapis.com/drive/v3/files"

    def __init__(self, api_key: str, folder_id: Optional[str] = None) -> None:
        self.api_key = api_key
        self.folder_id = folder_id

    def list_recent(self, limit: int = 20) -> List[RemoteFile]:
        params = {
            "pageSize": limit,
            "fields": "files(id,name,modifiedTime,parents)",
            "orderBy": "modifiedTime desc",
            "key": self.api_key,
        }
        if self.folder_id:
            params["q"] = f"'{self.folder_id}' in parents"
        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            raise FileProviderError(f"Google Drive request failed: {exc}") from exc

        files: List[RemoteFile] = []
        for item in response.json().get("files", []):
            files.append(
                RemoteFile(
                    name=item["name"],
                    path=f"https://drive.google.com/file/d/{item['id']}",
                    modified=datetime.fromisoformat(item["modifiedTime"].replace("Z", "+00:00")),
                    source=self.name,
                )
            )
        return files


class OneDriveProvider(BaseFileProvider):
    name = "OneDrive"
    api_url = "https://graph.microsoft.com/v1.0/me/drive/root/recent"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    def list_recent(self, limit: int = 20) -> List[RemoteFile]:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"top": limit}
        try:
            response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            raise FileProviderError(f"OneDrive request failed: {exc}") from exc

        files: List[RemoteFile] = []
        for item in response.json().get("value", []):
            files.append(
                RemoteFile(
                    name=item.get("name", "OneDrive file"),
                    path=item.get("parentReference", {}).get("path", ""),
                    modified=datetime.fromisoformat(item["lastModifiedDateTime"].replace("Z", "+00:00")),
                    source=self.name,
                )
            )
        return files


class FileIntegrationManager:
    """Aggregates recent files from connected storage providers."""

    def __init__(self) -> None:
        self.providers: List[BaseFileProvider] = []
        self._configure()

    def _configure(self) -> None:
        dropbox_token = os.getenv("DROPBOX_ACCESS_TOKEN")
        if dropbox_token:
            self.providers.append(DropboxProvider(dropbox_token))

        drive_api_key = os.getenv("GOOGLE_DRIVE_API_KEY")
        drive_folder = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        if drive_api_key:
            self.providers.append(GoogleDriveProvider(drive_api_key, drive_folder))

        onedrive_token = os.getenv("ONEDRIVE_ACCESS_TOKEN")
        if onedrive_token:
            self.providers.append(OneDriveProvider(onedrive_token))

    def list_recent(self, limit: int = 20) -> List[RemoteFile]:
        files: List[RemoteFile] = []
        for provider in self.providers:
            try:
                files.extend(provider.list_recent(limit=limit))
            except FileProviderError as exc:
                LOGGER.warning("%s skipped: %s", provider.name, exc)
        files.sort(key=lambda record: record.modified, reverse=True)
        return files[:limit]

    def has_providers(self) -> bool:
        return bool(self.providers)

