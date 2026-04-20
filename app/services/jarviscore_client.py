"""
JarvisCore Client
Provides access to JarvisCore Supabase database for enterprise context,
financial data, AdAI metrics, and event emission.
"""

import logging
import os
import uuid
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

LOGGER = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # For write operations


def get_supabase_client(use_service_key: bool = False) -> Client:
    """Get a Supabase client.

    Args:
        use_service_key: If True, use service key for write operations.
                        If False, use anon key (read-only).
    """
    if not SUPABASE_URL:
        raise ValueError("Missing SUPABASE_URL in environment variables.")

    if use_service_key:
        if not SUPABASE_SERVICE_KEY:
            LOGGER.warning("SUPABASE_SERVICE_KEY not set, falling back to ANON key")
            key = SUPABASE_ANON_KEY
        else:
            key = SUPABASE_SERVICE_KEY
    else:
        if not SUPABASE_ANON_KEY:
            raise ValueError("Missing SUPABASE_ANON_KEY in environment variables.")
        key = SUPABASE_ANON_KEY

    return create_client(SUPABASE_URL, key)


class JarvisCoreClient:
    """Read-only client for accessing JarvisCore enterprise data."""

    def __init__(self):
        self.client = get_supabase_client()

    # Basic GET wrappers

    def get_tenant(self):
        """Get the Agyeman Enterprises tenant."""
        return (
            self.client
            .table("tenants")
            .select("*")
            .eq("slug", "agyeman-enterprises")
            .single()
            .execute()
        )

    def get_workspaces(self):
        """Get all workspaces."""
        return (
            self.client
            .table("workspaces")
            .select("*")
            .execute()
        )

    def get_workspace_units(self):
        """Get all workspace units (companies)."""
        return (
            self.client
            .table("jarvis_companies")
            .select("*")
            .execute()
        )

    def get_modules(self):
        """Get all modules."""
        return (
            self.client
            .table("modules")
            .select("*")
            .execute()
        )

    def get_knowledge_graph(self):
        """Get all knowledge graph entities."""
        return (
            self.client
            .table("jarvis_universe_nodes")
            .select("*")
            .execute()
        )

    def get_systems(self):
        """Get all global systems."""
        return (
            self.client
            .table("jarvis_global_systems")
            .select("*")
            .execute()
        )

    def get_system_roles(self):
        """Get all system workspace roles."""
        return (
            self.client
            .table("jarvis_system_workspace_roles")
            .select("*")
            .execute()
        )

    def get_system_module_mappings(self):
        """Get all system module mappings."""
        return (
            self.client
            .table("jarvis_system_module_mappings")
            .select("*")
            .execute()
        )

    def get_simulated_events(self):
        """Get all simulated events."""
        return (
            self.client
            .table("jarvis_events")
            .select("*")
            .eq("is_simulation", True)
            .execute()
        )

    # =========================================================================
    # Financial Data Queries (nexus_financial_* tables)
    # =========================================================================

    def get_financial_entities(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get financial entities (businesses tracked for financial metrics)."""
        query = self.client.table("nexus_financial_entities").select("*")
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        result = query.execute()
        return result.data if result.data else []

    def get_financial_snapshots(
        self,
        entity_id: Optional[str] = None,
        months: int = 6
    ) -> List[Dict[str, Any]]:
        """Get financial snapshots for trend analysis."""
        cutoff = (datetime.utcnow() - timedelta(days=months * 30)).date().isoformat()
        query = (
            self.client
            .table("nexus_financial_snapshots")
            .select("*")
            .gte("snapshot_date", cutoff)
            .order("snapshot_date", desc=True)
        )
        if entity_id:
            query = query.eq("entity_id", entity_id)
        result = query.execute()
        return result.data if result.data else []

    def get_financial_transactions(
        self,
        entity_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get recent financial transactions."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query = (
            self.client
            .table("nexus_financial_transactions")
            .select("*")
            .gte("transaction_date", cutoff)
            .order("transaction_date", desc=True)
        )
        if entity_id:
            query = query.eq("entity_id", entity_id)
        result = query.execute()
        return result.data if result.data else []

    def get_tax_positions(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tax positions for all entities."""
        query = self.client.table("nexus_tax_positions").select("*")
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        result = query.execute()
        return result.data if result.data else []

    # =========================================================================
    # AdAI Metrics Queries (adai_* tables)
    # =========================================================================

    def get_adai_campaigns(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all AdAI campaigns."""
        query = self.client.table("adai_campaigns").select("*")
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        result = query.execute()
        return result.data if result.data else []

    def get_adai_metrics_daily(
        self,
        workspace_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily AdAI metrics for spend/conversion analysis."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        query = (
            self.client
            .table("adai_metrics_daily")
            .select("*")
            .gte("metric_date", cutoff)
            .order("metric_date", desc=True)
        )
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        result = query.execute()
        return result.data if result.data else []

    def get_adai_decisions(
        self,
        workspace_id: Optional[str] = None,
        pending_only: bool = False,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get AdAI decisions (approvals, auto-actions)."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query = (
            self.client
            .table("adai_decisions")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
        )
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        if pending_only:
            query = query.eq("status", "pending")
        result = query.execute()
        return result.data if result.data else []

    def get_adai_platform_connections(
        self,
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get AdAI platform connections (Meta, Google, TikTok)."""
        query = self.client.table("adai_platform_connections").select("*")
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        result = query.execute()
        return result.data if result.data else []

    def get_adai_policies(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get AdAI automation policies."""
        query = self.client.table("adai_policies").select("*")
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        result = query.execute()
        return result.data if result.data else []


class JarvisCoreWriter:
    """Write client for persisting events and alerts to JarvisCore."""

    def __init__(self):
        self.client = get_supabase_client(use_service_key=True)

    def emit_event(
        self,
        event_type: str,
        source: str,
        payload: Dict[str, Any],
        workspace_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        is_simulation: bool = False,
    ) -> Dict[str, Any]:
        """
        Emit an event to the GEM (Global Event Mesh) via jarvis_events table.

        Args:
            event_type: Event type (e.g., 'nexus.briefing.completed', 'adai.run.completed')
            source: Event source (e.g., 'agent.nexus', 'agent.adai')
            payload: Event payload data
            workspace_id: Optional workspace scope
            subject_id: Optional subject entity ID
            correlation_id: Optional correlation ID for request tracing
            causation_id: Optional causation ID (event that triggered this one)
            is_simulation: Whether this is a simulated/test event

        Returns:
            The created event record.
        """
        event_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        event_record = {
            "id": event_id,
            "event_type": event_type,
            "source": source,
            "payload": payload,
            "workspace_id": workspace_id,
            "subject_id": subject_id,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "causation_id": causation_id,
            "status": "pending",
            "is_simulation": is_simulation,
            "created_at": now,
        }

        try:
            result = (
                self.client
                .table("jarvis_events")
                .insert(event_record)
                .execute()
            )
            LOGGER.info("Emitted GEM event: %s (%s)", event_type, event_id)
            return result.data[0] if result.data else event_record
        except Exception as exc:
            LOGGER.exception("Failed to emit GEM event: %s", exc)
            raise

    def create_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        workspace_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an alert by emitting a nexus.alert.triggered event.

        Args:
            alert_type: Type of alert (e.g., 'cash_flow', 'revenue_drop', 'ad_spend')
            severity: Alert severity ('critical', 'warning', 'info')
            title: Alert title
            description: Alert description
            workspace_id: Optional workspace scope
            entity_id: Optional related entity ID
            metadata: Optional additional metadata

        Returns:
            The created alert event record.
        """
        payload = {
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "description": description,
            "entity_id": entity_id,
            "metadata": metadata or {},
            "triggered_at": datetime.utcnow().isoformat(),
        }

        return self.emit_event(
            event_type="nexus.alert.triggered",
            source="agent.nexus",
            payload=payload,
            workspace_id=workspace_id,
            subject_id=entity_id,
        )

    def mark_event_processed(self, event_id: str) -> Dict[str, Any]:
        """Mark an event as processed."""
        try:
            result = (
                self.client
                .table("jarvis_events")
                .update({"status": "processed", "processed_at": datetime.utcnow().isoformat()})
                .eq("id", event_id)
                .execute()
            )
            return result.data[0] if result.data else {}
        except Exception as exc:
            LOGGER.exception("Failed to mark event processed: %s", exc)
            raise

    def mark_event_failed(self, event_id: str, error: str) -> Dict[str, Any]:
        """Mark an event as failed with error details."""
        try:
            result = (
                self.client
                .table("jarvis_events")
                .update({
                    "status": "failed",
                    "error": error,
                    "processed_at": datetime.utcnow().isoformat()
                })
                .eq("id", event_id)
                .execute()
            )
            return result.data[0] if result.data else {}
        except Exception as exc:
            LOGGER.exception("Failed to mark event failed: %s", exc)
            raise

