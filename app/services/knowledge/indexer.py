"""
Knowledge graph indexer.
Indexes documents into Pinecone via RAGService (replaces broken ChromaDB).
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.knowledge.models import Document

LOGGER = logging.getLogger(__name__)


class KnowledgeIndexer:
    """Indexes documents into the Pinecone knowledge index via RAGService."""

    def __init__(self) -> None:
        self._rag: Optional[Any] = None
        self._init_rag()

    def _init_rag(self) -> None:
        try:
            from app.services.rag_service import RAGService
            self._rag = RAGService()
            LOGGER.info("KnowledgeIndexer backed by RAGService (Pinecone + Aqui)")
        except Exception as exc:
            LOGGER.error("KnowledgeIndexer RAGService init failed: %s", exc)
            self._rag = None

    def index_documents(self, documents: List[Document], source: str = "unknown") -> int:
        """
        Embed and upsert documents into Pinecone.

        Returns:
            Number of documents successfully indexed.
        """
        if not self._rag:
            LOGGER.error("KnowledgeIndexer not ready — RAGService unavailable")
            return 0
        if not documents:
            return 0

        LOGGER.info("Indexing %d documents from source: %s", len(documents), source)
        count = 0
        for doc in documents:
            try:
                doc_id = f"{source}:{doc.id}"
                metadata: Dict[str, Any] = {
                    "source": doc.source,
                    "path": doc.path,
                    "title": doc.title,
                    "entity": doc.entity or "",
                    "tags": ",".join(doc.tags),
                    "created_at": doc.created_at.isoformat() if doc.created_at else "",
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else "",
                    **{k: str(v) for k, v in doc.metadata.items()},
                }
                ok = self._rag.upsert(doc_id, doc.content, metadata)
                if ok:
                    count += 1
            except Exception as exc:
                LOGGER.warning("Failed to index document %s: %s", doc.id, exc)

        LOGGER.info("Successfully indexed %d/%d documents", count, len(documents))
        return count

    def search(
        self, query: str, top_k: int = 5, filters: Optional[dict] = None
    ) -> List[dict]:
        """
        Search the knowledge graph via Pinecone + Aqui.

        Returns:
            List of dicts with 'content', 'metadata', 'score', 'source'.
        """
        if not self._rag:
            return []
        if not query.strip():
            return []
        try:
            return self._rag.query(query, top_k=top_k)
        except Exception as exc:
            LOGGER.error("Knowledge search failed: %s", exc)
            return []

    def delete_by_source(self, source: str) -> int:
        """
        Delete documents by source prefix from Pinecone.

        Note: Pinecone serverless supports delete by prefix in the SDK; if not
        available on this index, logs a warning and returns 0.
        """
        if not self._rag or not self._rag._index:
            return 0
        try:
            # Pinecone serverless delete_many by metadata filter
            self._rag._index.delete(filter={"source": source})
            LOGGER.info("Deleted documents from source: %s", source)
            return -1  # count unknown with filter delete
        except Exception as exc:
            LOGGER.warning("delete_by_source failed for %s: %s — skipping", source, exc)
            return 0


# Global instance
knowledge_indexer = KnowledgeIndexer()


def index_documents(documents: List[Document], source: str = "unknown") -> int:
    """Convenience function to index documents."""
    return knowledge_indexer.index_documents(documents, source)
