"""
Jarvis services package.

Re-exports core service classes for convenient importing.
"""

from app.services.ollama_service import OllamaService
from app.services.privacy_filter import PrivacyFilter
from app.services.rag_service import RAGService

try:
    from app.services.document_indexer import DocumentIndexer
except ImportError:
    DocumentIndexer = None  # type: ignore[assignment,misc]

__all__ = ["OllamaService", "PrivacyFilter", "RAGService", "DocumentIndexer"]
