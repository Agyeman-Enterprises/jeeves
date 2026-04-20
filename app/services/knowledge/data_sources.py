"""
Data sources registry for knowledge graph.
Manages all source connectors (Dropbox, Gmail, Outlook, OneDrive, Google Drive, etc.)
"""

from __future__ import annotations

import logging

from app.services.knowledge.dropbox_source import DropboxSource

LOGGER = logging.getLogger(__name__)


class DataSources:
    """Registry of all data source connectors."""

    def __init__(self) -> None:
        self.dropbox = DropboxSource()
        # Future sources:
        # self.gmail = GmailSource()
        # self.outlook = OutlookSource()
        # self.onedrive = OneDriveSource()
        # self.gdrive = GoogleDriveSource()

        LOGGER.info("DataSources initialized")

    def get_all_sources(self) -> dict:
        """Get all configured sources."""
        sources = {}
        if self.dropbox.is_configured:
            sources["dropbox"] = self.dropbox
        # Add other sources as they're implemented
        return sources

