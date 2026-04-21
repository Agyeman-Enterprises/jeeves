"""
JJ Dual-Write Sync Manager
==========================
Supabase Cloud (tzjygaxpzrtevlnganjs) is PRIMARY authority. Always written first.
Docker/local (mem0 Qdrant) is SECONDARY replica. Written second.

When Docker is down:
  - Write to Supabase Cloud succeeds
  - Local write is queued in jj_sync_queue (in Supabase, so it survives the outage)

When Docker comes back:
  - sync_recovery job drains jj_sync_queue → applies to local mem0
  - Cloud and Docker end up in sync. No data loss.

Usage:
    mgr = get_sync_manager()
    await mgr.write_memory(content, metadata)
    await mgr.write_reflection(insight)
    await mgr.write_preference(preference, context, outcome)
"""
from __future__ import annotations

import logging
import os
from typing import Any

LOGGER = logging.getLogger(__name__)

_USER_ID = "akua"


class SyncManager:
    """
    Dual-write coordinator.
    All writes go to Supabase Cloud first (primary), then to local mem0 (secondary).
    Failures on local side are queued in Supabase for later recovery.
    """

    def __init__(self) -> None:
        self._supabase = None
        self._mem0 = None
        self._init_supabase()
        self._init_mem0()

    def _init_supabase(self) -> None:
        try:
            from app.config import get_settings
            from supabase import create_client
            s = get_settings()
            self._supabase = create_client(s.supabase_url, s.supabase_service_role_key)
            LOGGER.info("[sync] Supabase Cloud connected ✓")
        except Exception as exc:
            LOGGER.error("[sync] Supabase init failed: %s", exc)

    def _init_mem0(self) -> None:
        try:
            from app.memory.mem0_service import get_mem0
            self._mem0 = get_mem0()
            if self._mem0.available:
                LOGGER.info("[sync] Local mem0 available ✓")
            else:
                LOGGER.warning("[sync] Local mem0 not available (Docker may be down)")
        except Exception as exc:
            LOGGER.warning("[sync] mem0 init: %s", exc)

    # ------------------------------------------------------------------
    # Public write interface
    # ------------------------------------------------------------------

    def write_memory(self, content: str, metadata: dict | None = None) -> bool:
        """
        Write a memory entry.
        1. Write to Supabase Cloud (primary) — always attempted.
        2. Write to local mem0 (secondary) — if down, queue for recovery.
        Returns True if cloud write succeeded.
        """
        metadata = metadata or {}

        # 1. Primary: Supabase Cloud
        cloud_ok = self._write_to_cloud("mem0_add", {"content": content, "metadata": metadata})

        # 2. Secondary: local mem0
        local_ok = False
        if self._mem0 and self._mem0.available:
            try:
                self._mem0.add(content, metadata)
                local_ok = True
            except Exception as exc:
                LOGGER.warning("[sync] local mem0 write failed: %s — queued", exc)

        if not local_ok:
            self._queue_for_sync("mem0_add", {"content": content, "metadata": metadata})

        return cloud_ok

    def write_reflection(self, insight: str) -> bool:
        """Write a reflection. Cloud primary, local secondary with queue fallback."""
        metadata = {"type": "reflection"}

        cloud_ok = self._write_to_cloud("mem0_reflect", {"content": f"REFLECTION: {insight}", "metadata": metadata})

        local_ok = False
        if self._mem0 and self._mem0.available:
            try:
                self._mem0.record_reflection(insight)
                local_ok = True
            except Exception as exc:
                LOGGER.warning("[sync] local reflection write failed: %s — queued", exc)

        if not local_ok:
            self._queue_for_sync("mem0_reflect", {"content": f"REFLECTION: {insight}", "metadata": metadata})

        return cloud_ok

    def write_preference(self, preference: str, context: str, outcome: str = "positive") -> bool:
        """Write a preference. Cloud primary, local secondary with queue fallback."""
        content = f"PREFERENCE [{outcome}]: {preference} (context: {context})"
        metadata = {"type": "preference", "outcome": outcome}

        cloud_ok = self._write_to_cloud("mem0_preference", {"content": content, "metadata": metadata})

        local_ok = False
        if self._mem0 and self._mem0.available:
            try:
                self._mem0.add(content, metadata)
                local_ok = True
            except Exception as exc:
                LOGGER.warning("[sync] local preference write failed: %s — queued", exc)

        if not local_ok:
            self._queue_for_sync("mem0_preference", {"content": content, "metadata": metadata})

        return cloud_ok

    def log_agent_run(self, agent_name: str, task: str, status: str,
                      result: dict | None = None, error: str | None = None) -> str | None:
        """Log an agent run to Supabase (primary). Returns inserted row id."""
        if not self._supabase:
            return None
        try:
            row = {
                "agent_name": agent_name,
                "task": task,
                "status": status,
                "result": result,
                "error": error,
            }
            if status in ("success", "failed"):
                row["finished_at"] = "now()"
            resp = self._supabase.table("jeeves_agent_runs").insert(row).execute()
            if resp.data:
                return resp.data[0].get("id")
        except Exception as exc:
            LOGGER.error("[sync] log_agent_run: %s", exc)
        return None

    def log_action(self, action: str, agent: str | None, payload: dict,
                   result: dict | None = None, status: str = "success") -> None:
        """Log a dispatched action to Supabase."""
        if not self._supabase:
            return
        try:
            self._supabase.table("jeeves_action_logs").insert({
                "action": action,
                "agent": agent,
                "payload": payload,
                "result": result,
                "status": status,
            }).execute()
        except Exception as exc:
            LOGGER.error("[sync] log_action: %s", exc)

    def emit_signal(self, signal_type: str, source: str, content: str, metadata: dict | None = None) -> None:
        """Emit a signal to the jeeves_signals timeline table."""
        if not self._supabase:
            return
        try:
            self._supabase.table("jeeves_signals").insert({
                "signal_type": signal_type,
                "source": source,
                "content": content,
                "metadata": metadata or {},
            }).execute()
        except Exception as exc:
            LOGGER.error("[sync] emit_signal: %s", exc)

    # ------------------------------------------------------------------
    # Read interface (cloud-first, local fallback)
    # ------------------------------------------------------------------

    def search_memory(self, query: str, limit: int = 10) -> list:
        """
        Search memory. Always tries local mem0 first (fast vector search).
        Falls back to cloud jeeves_signals text search if local is down.
        """
        if self._mem0 and self._mem0.available:
            try:
                results = self._mem0.search(query, limit=limit)
                if results:
                    return results
            except Exception as exc:
                LOGGER.warning("[sync] local search failed: %s", exc)

        # Cloud fallback: text search in jeeves_signals
        if self._supabase:
            try:
                resp = self._supabase.table("jeeves_signals") \
                    .select("content,created_at,metadata") \
                    .ilike("content", f"%{query}%") \
                    .order("created_at", desc=True) \
                    .limit(limit) \
                    .execute()
                return [{"memory": r["content"], "score": 0.5, "source": "cloud"} for r in (resp.data or [])]
            except Exception as exc:
                LOGGER.error("[sync] cloud search fallback: %s", exc)

        return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_to_cloud(self, operation: str, payload: dict) -> bool:
        """
        Record memory write to Supabase Cloud (jeeves_signals) as the canonical store.
        This makes Supabase the durable record even if local mem0 is unavailable.
        """
        if not self._supabase:
            return False
        try:
            content = payload.get("content", "")
            metadata = payload.get("metadata", {})
            self._supabase.table("jeeves_signals").insert({
                "signal_type": operation,
                "source": "jj_memory",
                "content": content,
                "metadata": metadata,
            }).execute()
            return True
        except Exception as exc:
            LOGGER.error("[sync] cloud write failed: %s", exc)
            return False

    def _queue_for_sync(self, operation: str, payload: dict) -> None:
        """
        Queue a failed local write in Supabase jj_sync_queue.
        Will be drained by sync_recovery job when Docker comes back online.
        """
        if not self._supabase:
            LOGGER.error("[sync] Cannot queue — Supabase unavailable. Write may be lost: %s", operation)
            return
        try:
            self._supabase.table("jj_sync_queue").insert({
                "operation": operation,
                "payload": payload,
                "status": "pending",
            }).execute()
            LOGGER.info("[sync] Queued for recovery: %s", operation)
        except Exception as exc:
            LOGGER.error("[sync] Failed to queue write for recovery: %s", exc)

    def local_available(self) -> bool:
        return bool(self._mem0 and self._mem0.available)

    def cloud_available(self) -> bool:
        return self._supabase is not None


# Singleton
_instance: SyncManager | None = None


def get_sync_manager() -> SyncManager:
    global _instance
    if _instance is None:
        _instance = SyncManager()
    return _instance
