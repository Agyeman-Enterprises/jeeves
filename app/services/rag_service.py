"""
RAG Service — triple-layer knowledge retrieval for JARVIS.

Layer 1: Pinecone vector index (jarvis-knowledge) — structured business docs,
         indexed emails, Dropbox/Drive files, custom knowledge vectors.
         Uses OpenAI text-embedding-3-small for embeddings (1536-dim).

Layer 2: Pinecone Assistant (jarvis) — conversational RAG with citations
         over all uploaded documents.

Layer 3: Aqui knowledge vault (localhost:3939) — all Claude/ChatGPT
         conversations, emails, sticky notes, cloud docs.
         POST /search endpoint — no embeddings needed.

Falls back gracefully when any layer is unavailable.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

LOGGER = logging.getLogger(__name__)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "jarvis-knowledge")
PINECONE_ASSISTANT_NAME = os.getenv("PINECONE_ASSISTANT_NAME", "jarvis")
AQUI_BASE_URL = os.getenv("AQUI_BASE_URL", "https://aqui.agyemanenterprises.com")
AQUI_API_KEY = os.getenv("AQUI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Cache: key → (timestamp, results)
_cache: Dict[str, tuple] = {}
_CACHE_TTL = 120  # seconds


def _ck(query: str, source: str, extra: str = "") -> str:
    return hashlib.md5(f"{source}:{extra}:{query[:200]}".encode()).hexdigest()


def _get_cached(key: str) -> Optional[List[Dict]]:
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, results = entry
    if time.time() - ts > _CACHE_TTL:
        del _cache[key]
        return None
    return results


def _set_cached(key: str, results: List[Dict]) -> None:
    _cache[key] = (time.time(), results)


class RAGService:
    """Triple-layer semantic search: Pinecone index + Assistant + Aqui vault."""

    def __init__(self) -> None:
        self._pinecone = None
        self._index = None
        self._assistant_obj = None
        self._aqui_headers: Dict[str, str] = {"Content-Type": "application/json"}
        if AQUI_API_KEY:
            self._aqui_headers["Authorization"] = f"Bearer {AQUI_API_KEY}"
        self._init_pinecone()

    # ── Init ─────────────────────────────────────────────────────────────────

    def _init_pinecone(self) -> None:
        if not PINECONE_API_KEY:
            LOGGER.info("PINECONE_API_KEY not set — Pinecone layers disabled")
            return
        try:
            from pinecone import Pinecone
            self._pinecone = Pinecone(api_key=PINECONE_API_KEY)
            self._index = self._pinecone.Index(PINECONE_INDEX_NAME)
            LOGGER.info("Pinecone index '%s' connected", PINECONE_INDEX_NAME)
        except Exception as exc:
            LOGGER.warning("Pinecone init failed: %s", exc)

    def _get_assistant(self):
        if self._assistant_obj:
            return self._assistant_obj
        if not self._pinecone:
            return None
        try:
            self._assistant_obj = self._pinecone.assistant.Assistant(
                assistant_name=PINECONE_ASSISTANT_NAME
            )
            return self._assistant_obj
        except Exception as exc:
            LOGGER.debug("Pinecone assistant init failed: %s", exc)
            return None

    def _embed(self, text: str) -> Optional[List[float]]:
        """Generate 1536-dim embedding via OpenAI text-embedding-3-small."""
        if not OPENAI_API_KEY:
            return None
        try:
            import openai
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            resp = client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000],
            )
            return resp.data[0].embedding
        except Exception as exc:
            LOGGER.debug("Embedding failed: %s", exc)
            return None

    # ── Layer 1: Pinecone vector index ────────────────────────────────────────

    def query_pinecone(self, prompt: str, top_k: int = 5) -> List[Dict]:
        """Search the Pinecone vector index for relevant document chunks."""
        if not self._index:
            return []
        key = _ck(prompt, "pinecone")
        cached = _get_cached(key)
        if cached is not None:
            return cached
        embedding = self._embed(prompt)
        if not embedding:
            return []
        try:
            results = self._index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
            )
            hits = [
                {
                    "content": m.get("metadata", {}).get("text", ""),
                    "metadata": m.get("metadata", {}),
                    "score": m.get("score", 0.0),
                    "source": "pinecone",
                }
                for m in results.get("matches", [])
                if m.get("metadata", {}).get("text")
            ]
            _set_cached(key, hits)
            return hits
        except Exception as exc:
            LOGGER.warning("Pinecone vector query failed: %s", exc)
            return []

    # ── Layer 2: Pinecone Assistant ───────────────────────────────────────────

    def ask_assistant(self, question: str) -> Optional[str]:
        """Ask the Pinecone JARVIS assistant — conversational RAG with citations."""
        assistant = self._get_assistant()
        if not assistant:
            return None
        key = _ck(question, "assistant")
        cached = _get_cached(key)
        if cached is not None:
            return cached[0]["content"] if cached else None
        try:
            from pinecone_plugins.assistant.models.chat import Message
            resp = assistant.chat(
                messages=[Message(content=question, role="user")]
            )
            answer = resp.message.content if resp.message else None
            if answer:
                _set_cached(key, [{"content": answer, "source": "pinecone_assistant"}])
            return answer
        except Exception as exc:
            LOGGER.debug("Pinecone assistant query failed: %s", exc)
            return None

    # ── Layer 3: Aqui vault ───────────────────────────────────────────────────

    def query_aqui(
        self,
        prompt: str,
        top_k: int = 5,
        provider: Optional[str] = None,
    ) -> List[Dict]:
        """Search Aqui knowledge vault (conversations, emails, docs)."""
        if not prompt or not prompt.strip():
            return []
        key = _ck(prompt, "aqui", provider or "")
        cached = _get_cached(key)
        if cached is not None:
            return cached
        body: Dict[str, Any] = {"query": prompt, "top_k": top_k}
        if provider:
            body["filter"] = {"provider": provider}
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(
                    f"{AQUI_BASE_URL}/search",
                    json=body,
                    headers=self._aqui_headers,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError:
            LOGGER.debug("Aqui unavailable at %s", AQUI_BASE_URL)
            return []
        except httpx.TimeoutException:
            LOGGER.debug("Aqui request timed out")
            return []
        except Exception as exc:
            LOGGER.debug("Aqui search failed: %s", exc)
            return []

        hits = [
            {
                "content": r.get("content", ""),
                "metadata": r.get("metadata", {}),
                "score": r.get("score", 0.0),
                "source": "aqui",
            }
            for r in data.get("results", [])
        ]
        _set_cached(key, hits)
        LOGGER.debug("Aqui returned %d results (provider=%s)", len(hits), provider or "all")
        return hits

    def search_aqui_conversations(
        self, query: str, provider: Optional[str] = None, top_k: int = 5
    ) -> List[Dict]:
        """Targeted search of AI conversation history in Aqui."""
        return self.query_aqui(query, top_k=top_k, provider=provider)

    # ── Combined: all layers merged ───────────────────────────────────────────

    def query(self, prompt: str, top_k: int = 5) -> List[Dict]:
        """
        Query all knowledge layers and return merged, deduplicated results.
        Order of priority: Pinecone vector → Aqui vault.
        """
        results: List[Dict] = []

        # Layer 1: Pinecone vector
        results.extend(self.query_pinecone(prompt, top_k=top_k))

        # Layer 3: Aqui (fill remaining slots)
        remaining = max(0, top_k - len(results))
        if remaining > 0:
            results.extend(self.query_aqui(prompt, top_k=remaining + 2))

        # Deduplicate by content fingerprint
        seen: set = set()
        deduped = []
        for r in results:
            fp = hashlib.md5(r["content"][:200].encode()).hexdigest()
            if fp not in seen and r["content"].strip():
                seen.add(fp)
                deduped.append(r)

        return deduped[:top_k]

    # ── Health check ──────────────────────────────────────────────────────────

    def health(self) -> Dict[str, bool]:
        pinecone_ok = self._index is not None
        aqui_ok = False
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{AQUI_BASE_URL}/health")
                aqui_ok = resp.status_code == 200
        except Exception:
            pass
        return {"pinecone": pinecone_ok, "aqui": aqui_ok}

    # ── Upsert into Pinecone ─────────────────────────────────────────────────

    def upsert(self, doc_id: str, text: str, metadata: Dict[str, Any]) -> bool:
        """Embed and index a document chunk into Pinecone."""
        if not self._index:
            return False
        embedding = self._embed(text)
        if not embedding:
            return False
        try:
            self._index.upsert(
                vectors=[{
                    "id": doc_id,
                    "values": embedding,
                    "metadata": {**metadata, "text": text[:1000]},
                }]
            )
            return True
        except Exception as exc:
            LOGGER.warning("Pinecone upsert failed for %s: %s", doc_id, exc)
            return False

    def upload_to_assistant(self, file_path: str) -> bool:
        """Upload a file to the Pinecone JARVIS assistant for RAG."""
        assistant = self._get_assistant()
        if not assistant:
            return False
        try:
            with open(file_path, "rb") as f:
                assistant.upload_file(file=f, timeout=30)
            LOGGER.info("Uploaded %s to Pinecone assistant", file_path)
            return True
        except Exception as exc:
            LOGGER.warning("Assistant file upload failed for %s: %s", file_path, exc)
            return False
