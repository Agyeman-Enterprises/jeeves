"""
Dropbox source connector for knowledge graph.
Crawls Dropbox files and converts them to Document objects.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv

from app.services.knowledge.models import Document
from app.services.knowledge.utils import (
    classify_entity,
    classify_tags,
    extract_text_from_bytes,
)

load_dotenv()

LOGGER = logging.getLogger(__name__)

# Try to import Dropbox SDK
try:
    import dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False
    LOGGER.warning("dropbox not installed. Install with: pip install dropbox")
    dropbox = None  # type: ignore


class DropboxSource:
    """Source connector for Dropbox files."""

    def __init__(self) -> None:
        self.client: Optional[Any] = None
        self.is_configured = False

        if not DROPBOX_AVAILABLE:
            LOGGER.warning("Dropbox SDK not available")
            return

        access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
        if not access_token:
            LOGGER.warning("DROPBOX_ACCESS_TOKEN not configured")
            return

        try:
            self.client = dropbox.Dropbox(access_token)
            self.is_configured = True
            LOGGER.info("DropboxSource initialized successfully")
        except Exception as exc:
            LOGGER.error("Failed to initialize Dropbox client: %s", exc)

    def list_files(self, path: str = "") -> List[Any]:
        """
        Recursively list all Dropbox files.

        Args:
            path: Starting path (empty for root)

        Returns:
            List of FileMetadata objects
        """
        if not self.is_configured or not self.client:
            LOGGER.warning("Dropbox not configured")
            return []

        files = []
        try:
            result = self.client.files_list_folder(path, recursive=True)

            # Add initial entries
            files.extend([f for f in result.entries if isinstance(f, dropbox.files.FileMetadata)])

            # Continue pagination if needed
            while result.has_more:
                result = self.client.files_list_folder_continue(result.cursor)
                files.extend([f for f in result.entries if isinstance(f, dropbox.files.FileMetadata)])

            LOGGER.info("Listed %d files from Dropbox", len(files))
            return files
        except Exception as exc:
            LOGGER.error("Failed to list Dropbox files: %s", exc)
            return []

    def load_file(self, file: Any) -> Optional[Document]:
        """
        Download file and convert to Document.

        Args:
            file: Dropbox FileMetadata object

        Returns:
            Document object or None if extraction fails
        """
        if not self.is_configured or not self.client:
            return None

        try:
            # Download file
            _, res = self.client.files_download(file.path_lower)
            data = res.content

            # Extract text
            text = extract_text_from_bytes(data, file.name)

            if not text.strip():
                LOGGER.debug("No text extracted from %s", file.path_display)
                return None

            # Classify entity and tags
            entity = classify_entity(file.path_display)
            tags = classify_tags(text, file.path_display)

            # Convert timestamps
            created_at = file.client_modified if hasattr(file, "client_modified") else None
            updated_at = file.server_modified if hasattr(file, "server_modified") else None

            return Document(
                id=file.id,
                source="dropbox",
                path=file.path_display,
                title=file.name,
                content=text,
                created_at=created_at,
                updated_at=updated_at,
                entity=entity,
                tags=tags,
                metadata={"rev": file.rev, "size": file.size},
            )
        except Exception as exc:
            LOGGER.warning("Failed to load file %s: %s", file.path_display, exc)
            return None

    def fetch_all(self) -> List[Document]:
        """
        Fetch all files from Dropbox and convert to Documents.

        Returns:
            List of Document objects
        """
        if not self.is_configured:
            LOGGER.warning("Dropbox not configured, returning empty list")
            return []

        files = self.list_files()
        docs = []

        LOGGER.info("Processing %d files from Dropbox", len(files))

        for file in files:
            try:
                doc = self.load_file(file)
                if doc:
                    docs.append(doc)
            except Exception as exc:
                LOGGER.debug("Skipping file %s due to error: %s", file.path_display, exc)
                continue

        LOGGER.info("Successfully processed %d documents from Dropbox", len(docs))
        return docs

