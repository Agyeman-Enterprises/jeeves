"""
Tests for SyncManager dual-write contract.
Verifies: cloud write succeeds, local failure queues, search falls back to cloud.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers — build a SyncManager with mocked internals
# ---------------------------------------------------------------------------

def _make_manager(cloud_ok: bool = True, mem0_ok: bool = True):
    """
    Returns a SyncManager where Supabase and mem0 are replaced by mocks.
    cloud_ok  — whether _supabase mock behaves as connected
    mem0_ok   — whether mem0 mock reports available=True
    """
    from app.memory.sync_manager import SyncManager

    mgr = SyncManager.__new__(SyncManager)

    # Supabase mock
    if cloud_ok:
        supabase = MagicMock()
        supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        supabase.table.return_value.select.return_value.ilike.return_value \
            .order.return_value.limit.return_value.execute.return_value \
            = MagicMock(data=[{"content": "found it", "created_at": "2026-04-21", "metadata": {}}])
        mgr._supabase = supabase
    else:
        mgr._supabase = None

    # mem0 mock
    mem0 = MagicMock()
    mem0.available = mem0_ok
    mgr._mem0 = mem0

    return mgr


# ---------------------------------------------------------------------------
# Test: write_memory — cloud write succeeds, local write attempted
# ---------------------------------------------------------------------------

class TestWriteMemoryCloudAndLocal:
    def test_cloud_write_called(self):
        """write_memory always writes to Supabase Cloud first."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=True)
        result = mgr.write_memory("hello world", {"type": "conversation"})

        assert result is True
        assert mgr._supabase.table.called
        # Should insert into jeeves_signals
        table_calls = [str(c) for c in mgr._supabase.table.call_args_list]
        assert any("jeeves_signals" in c for c in table_calls)

    def test_local_write_attempted_when_available(self):
        """write_memory calls mem0.add() when local is available."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=True)
        mgr.write_memory("some fact", {"type": "fact"})

        mgr._mem0.add.assert_called_once()

    def test_returns_true_on_cloud_success(self):
        """Returns True when cloud write succeeds, regardless of local state."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=False)
        result = mgr.write_memory("content", {})
        assert result is True

    def test_returns_false_when_cloud_unavailable(self):
        """Returns False when Supabase is not configured."""
        mgr = _make_manager(cloud_ok=False, mem0_ok=True)
        result = mgr.write_memory("content", {})
        assert result is False


# ---------------------------------------------------------------------------
# Test: write_memory — local failure queues to jj_sync_queue
# ---------------------------------------------------------------------------

class TestWriteMemoryQueuesOnLocalFailure:
    def test_queues_when_local_unavailable(self):
        """When mem0 is down, write is queued in jj_sync_queue."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=False)
        mgr.write_memory("queued content", {"type": "conversation"})

        # Should insert into jj_sync_queue
        table_calls = [str(c) for c in mgr._supabase.table.call_args_list]
        assert any("jj_sync_queue" in c for c in table_calls)

    def test_queues_when_local_raises(self):
        """When mem0.add() raises, write is queued."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=True)
        mgr._mem0.add.side_effect = RuntimeError("qdrant down")

        mgr.write_memory("error content", {})

        table_calls = [str(c) for c in mgr._supabase.table.call_args_list]
        assert any("jj_sync_queue" in c for c in table_calls)

    def test_no_queue_when_local_succeeds(self):
        """When local write succeeds, jj_sync_queue is NOT written."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=True)
        mgr.write_memory("fine content", {})

        table_calls = [str(c) for c in mgr._supabase.table.call_args_list]
        assert not any("jj_sync_queue" in c for c in table_calls)


# ---------------------------------------------------------------------------
# Test: write_reflection
# ---------------------------------------------------------------------------

class TestWriteReflection:
    def test_calls_record_reflection_on_mem0(self):
        """write_reflection uses mem0.record_reflection(), not mem0.add()."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=True)
        mgr.write_reflection("Key insight about priorities")

        mgr._mem0.record_reflection.assert_called_once_with("Key insight about priorities")
        mgr._mem0.add.assert_not_called()

    def test_queues_reflection_when_local_down(self):
        """When mem0 is unavailable, reflection is queued."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=False)
        mgr.write_reflection("Insight")

        table_calls = [str(c) for c in mgr._supabase.table.call_args_list]
        assert any("jj_sync_queue" in c for c in table_calls)


# ---------------------------------------------------------------------------
# Test: search_memory — cloud fallback when local is down
# ---------------------------------------------------------------------------

class TestSearchMemoryFallback:
    def test_returns_local_results_when_available(self):
        """search_memory returns mem0 results when local is up."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=True)
        mgr._mem0.search.return_value = [{"memory": "local result", "score": 0.9}]

        results = mgr.search_memory("find something")

        assert len(results) == 1
        assert results[0]["memory"] == "local result"
        # Cloud should NOT be queried if local returned results
        mgr._mem0.search.assert_called_once_with("find something", limit=10)

    def test_falls_back_to_cloud_when_local_down(self):
        """search_memory falls back to jeeves_signals text search when mem0 is down."""
        mgr = _make_manager(cloud_ok=True, mem0_ok=False)

        results = mgr.search_memory("find something")

        assert len(results) == 1
        assert results[0]["memory"] == "found it"
        assert results[0]["source"] == "cloud"

    def test_returns_empty_when_both_unavailable(self):
        """Returns empty list when both local and cloud are unavailable."""
        mgr = _make_manager(cloud_ok=False, mem0_ok=False)
        results = mgr.search_memory("anything")
        assert results == []


# ---------------------------------------------------------------------------
# Test: availability flags
# ---------------------------------------------------------------------------

class TestAvailabilityFlags:
    def test_cloud_available_true_when_supabase_connected(self):
        mgr = _make_manager(cloud_ok=True)
        assert mgr.cloud_available() is True

    def test_cloud_available_false_when_supabase_none(self):
        mgr = _make_manager(cloud_ok=False)
        assert mgr.cloud_available() is False

    def test_local_available_true_when_mem0_up(self):
        mgr = _make_manager(mem0_ok=True)
        assert mgr.local_available() is True

    def test_local_available_false_when_mem0_down(self):
        mgr = _make_manager(mem0_ok=False)
        assert mgr.local_available() is False
