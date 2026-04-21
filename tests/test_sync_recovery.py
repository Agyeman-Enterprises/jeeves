"""
Tests for sync_recovery dual-write contract.
Verifies: pending queue items are drained and marked synced when Docker returns.

Note: sync_recovery.py uses local imports inside run_sync_recovery().
Patches must target the source modules (app.memory.*), not sync_recovery itself.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch


def _build_supabase(pending_items: list) -> MagicMock:
    """Supabase mock that returns pending_items from jj_sync_queue select."""
    sb = MagicMock()

    # .table("jj_sync_queue").select(...).eq(...).order(...).limit(...).execute()
    sb.table.return_value.select.return_value \
        .eq.return_value.order.return_value \
        .limit.return_value.execute.return_value \
        = MagicMock(data=pending_items)

    # .table(...).update(...).eq(...).execute()  — called to mark synced/failed
    sb.table.return_value.update.return_value \
        .eq.return_value.execute.return_value \
        = MagicMock()

    return sb


def _make_mgr(sb: MagicMock) -> MagicMock:
    mgr = MagicMock()
    mgr._supabase = sb
    return mgr


def _make_mem0(available: bool = True) -> MagicMock:
    mem0 = MagicMock()
    mem0.available = available
    return mem0


def _run(pending_items: list, mem0_available: bool = True):
    """
    Helper: run run_sync_recovery() with the given queue contents.
    Returns (mgr_mock, mem0_mock, supabase_mock).
    """
    sb = _build_supabase(pending_items)
    mgr = _make_mgr(sb)
    mem0 = _make_mem0(available=mem0_available)

    with patch("app.memory.sync_manager.get_sync_manager", return_value=mgr), \
         patch("app.memory.mem0_service.get_mem0", return_value=mem0):
        from app.jobs import sync_recovery
        import importlib
        importlib.reload(sync_recovery)  # ensure fresh import picks up patches
        sync_recovery.run_sync_recovery()

    return mgr, mem0, sb


# ---------------------------------------------------------------------------
# Test: pending item applied and marked synced
# ---------------------------------------------------------------------------

class TestSyncRecoveryDrainsQueue:

    def test_pending_mem0_add_applied_and_marked_synced(self):
        """A pending mem0_add row is applied to mem0 and marked status='synced'."""
        pending = [{
            "id": "row-1",
            "operation": "mem0_add",
            "payload": {"content": "queued memory", "metadata": {"type": "conversation"}},
            "attempts": 0,
        }]

        sb = _build_supabase(pending)
        mgr = _make_mgr(sb)
        mem0 = _make_mem0(available=True)

        with patch("app.memory.sync_manager.get_sync_manager", return_value=mgr), \
             patch("app.memory.mem0_service.get_mem0", return_value=mem0):
            from app.jobs.sync_recovery import run_sync_recovery
            result = run_sync_recovery()

        # mem0.add() must be called with the queued content
        mem0.add.assert_called_once_with("queued memory", {"type": "conversation"})

        # Row must be marked synced
        update_calls = str(sb.table.return_value.update.call_args_list)
        assert "synced" in update_calls, f"Expected 'synced' in: {update_calls}"

        assert result["synced"] == 1
        assert result["failed"] == 0

    def test_mem0_reflect_applied(self):
        """mem0_reflect operation calls record_reflection on mem0."""
        pending = [{
            "id": "row-2",
            "operation": "mem0_reflect",
            "payload": {"content": "REFLECTION: an insight", "metadata": {"type": "reflection"}},
            "attempts": 0,
        }]

        sb = _build_supabase(pending)
        mgr = _make_mgr(sb)
        mem0 = _make_mem0(available=True)

        with patch("app.memory.sync_manager.get_sync_manager", return_value=mgr), \
             patch("app.memory.mem0_service.get_mem0", return_value=mem0):
            from app.jobs.sync_recovery import run_sync_recovery
            result = run_sync_recovery()

        mem0.record_reflection.assert_called_once_with("an insight")
        assert result["synced"] == 1

    def test_empty_queue_does_nothing(self):
        """No items in queue → no mem0 calls."""
        sb = _build_supabase([])
        mgr = _make_mgr(sb)
        mem0 = _make_mem0(available=True)

        with patch("app.memory.sync_manager.get_sync_manager", return_value=mgr), \
             patch("app.memory.mem0_service.get_mem0", return_value=mem0):
            from app.jobs.sync_recovery import run_sync_recovery
            result = run_sync_recovery()

        mem0.add.assert_not_called()
        mem0.record_reflection.assert_not_called()
        assert result["synced"] == 0
        assert result["checked"] == 0

    def test_skips_when_mem0_unavailable(self):
        """If mem0 is not available (Docker still down), recovery is a no-op."""
        pending = [{
            "id": "row-3",
            "operation": "mem0_add",
            "payload": {"content": "something", "metadata": {}},
            "attempts": 0,
        }]

        sb = _build_supabase(pending)
        mgr = _make_mgr(sb)
        mem0 = _make_mem0(available=False)

        with patch("app.memory.sync_manager.get_sync_manager", return_value=mgr), \
             patch("app.memory.mem0_service.get_mem0", return_value=mem0):
            from app.jobs.sync_recovery import run_sync_recovery
            run_sync_recovery()

        mem0.add.assert_not_called()

    def test_failed_apply_not_marked_synced(self):
        """When mem0.add() raises, the row is NOT marked synced."""
        pending = [{
            "id": "row-4",
            "operation": "mem0_add",
            "payload": {"content": "bad item", "metadata": {}},
            "attempts": 2,
        }]

        sb = _build_supabase(pending)
        mgr = _make_mgr(sb)
        mem0 = _make_mem0(available=True)
        mem0.add.side_effect = RuntimeError("qdrant error")

        with patch("app.memory.sync_manager.get_sync_manager", return_value=mgr), \
             patch("app.memory.mem0_service.get_mem0", return_value=mem0):
            from app.jobs.sync_recovery import run_sync_recovery
            result = run_sync_recovery()

        update_calls = str(sb.table.return_value.update.call_args_list)
        assert "synced" not in update_calls, "Should not mark synced on failure"
        assert result["failed"] == 1
        assert result["synced"] == 0
