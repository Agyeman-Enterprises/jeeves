"""
Knowledge graph models for document representation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    """Represents a document in the knowledge graph."""

    id: str
    source: str  # "dropbox", "gmail", "outlook", "onedrive", "gdrive", etc.
    path: str
    title: str
    content: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    entity: Optional[str] = None  # Classified entity (e.g., "ohimaa", "purrkoin")
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "source": self.source,
            "path": self.path,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "entity": self.entity,
            "tags": self.tags,
            "metadata": self.metadata,
        }

