"""
JJ Sync Recovery Job
====================
Drains jj_sync_queue when Docker/local comes back online.

Supabase Cloud is primary. When Docker was down, writes were queued in
jj_sync_queue (which lives in Supabase, so it survived the outage).

This job runs:
  - At JJ startup (catches up immediately)
  - Every 15 minutes via APScheduler

It replays queued mem0 writes to local, then marks them synced.
Cloud and Docker end up consistent. No data loss.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

LOGGER = logging.getLogger(__name__)

MAX_BATCH = 100  # items per recovery run


def run_sync_recovery() -> dict:
    """
    Drain jj_sync_queue → apply to local mem0.
    Returns summary dict.
    """
    from app.memory.sync_manager import get_sync_manager
    from app.memory.mem0_service import get_mem0

    mgr = get_sync_manager()
    mem0 = get_mem0()
    supabase = mgr._supabase

    summary = {"checked": 0, "synced": 0, "skipped": 0, "failed": 0, "local_available": mem0.available}

    if not supabase:
        LOGGER.warning("[sync_recovery] Supabase not available — cannot drain queue")
        return summary

    if not mem0.available:
        LOGGER.info("[sync_recovery] Local mem0 not available — skipping recovery (will retry next run)")
        return summary

    # Fetch pending items
    try:
        resp = supabase.table("jj_sync_queue") \
            .select("id,operation,payload,attempts") \
            .eq("status", "pending") \
            .order("created_at", desc=False) \
            .limit(MAX_BATCH) \
            .execute()
        items = resp.data or []
    except Exception as exc:
        LOGGER.error("[sync_recovery] Failed to fetch queue: %s", exc)
        return summary

    summary["checked"] = len(items)
    LOGGER.info("[sync_recovery] Draining %d queued items", len(items))

    for item in items:
        item_id = item["id"]
        operation = item["operation"]
        payload = item["payload"]
        attempts = item.get("attempts", 0)

        try:
            content = payload.get("content", "")
            metadata = payload.get("metadata", {})

            if operation == "mem0_add":
                mem0.add(content, metadata)
            elif operation == "mem0_reflect":
                # Strip the REFLECTION: prefix if present, let record_reflection re-add it
                insight = content.removeprefix("REFLECTION: ")
                mem0.record_reflection(insight)
            elif operation == "mem0_preference":
                mem0.add(content, metadata)
            else:
                LOGGER.warning("[sync_recovery] Unknown operation %s — skipping", operation)
                summary["skipped"] += 1
                continue

            # Mark synced
            supabase.table("jj_sync_queue").update({
                "status": "synced",
                "synced_at": "now()",
                "attempts": attempts + 1,
            }).eq("id", item_id).execute()
            summary["synced"] += 1

        except Exception as exc:
            LOGGER.error("[sync_recovery] Failed to apply item %s: %s", item_id, exc)
            # Increment attempt count; after 5 failures mark as failed
            new_status = "failed" if attempts >= 4 else "pending"
            try:
                supabase.table("jj_sync_queue").update({
                    "attempts": attempts + 1,
                    "status": new_status,
                    "error": str(exc),
                }).eq("id", item_id).execute()
            except Exception:
                pass
            summary["failed"] += 1

    LOGGER.info("[sync_recovery] Done — synced=%d failed=%d skipped=%d",
                summary["synced"], summary["failed"], summary["skipped"])
    return summary
