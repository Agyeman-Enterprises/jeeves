"""
Mimograph — Layer 3: The personality/behavior graph.
Nodes: goals, behaviors, people, projects, emotions, blockers, routines, rewards.
Edges: supports, contradicts, precedes, predicts, drains, energizes.

This is the living portrait of who Akua IS (not just what she says).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.db import get_db
from app.schemas.beliefs import (
    SEED_EDGES,
    SEED_NODES,
    BeliefEdge,
    BeliefNode,
    EdgeType,
    NodeType,
)

LOGGER = logging.getLogger(__name__)

NODES_TABLE = "jeeves_belief_nodes"
EDGES_TABLE = "jeeves_belief_edges"


class Mimograph:
    """
    Graph-based personality model.
    Persists to Supabase. Answers questions like:
    - What blocks goal X?
    - What energizes Akua?
    - What contradicts her stated priorities?
    """

    def __init__(self):
        self._ensure_seed()

    # ── Seed ───────────────────────────────────────────────────────────
    def _ensure_seed(self):
        db = get_db()
        if not db:
            return
        try:
            existing = db.table(NODES_TABLE).select("node_id").limit(1).execute()
            if not existing.data:
                LOGGER.info("[Mimograph] Seeding %d nodes, %d edges", len(SEED_NODES), len(SEED_EDGES))
                for n in SEED_NODES:
                    db.table(NODES_TABLE).insert({
                        "node_id": n.node_id, "label": n.label,
                        "node_type": n.node_type.value, "strength": n.strength,
                        "confidence": n.confidence, "evidence_count": n.evidence_count,
                        "last_evidence": n.last_evidence,
                    }).execute()
                for e in SEED_EDGES:
                    db.table(EDGES_TABLE).insert({
                        "source_id": e.source_id, "target_id": e.target_id,
                        "edge_type": e.edge_type.value, "weight": e.weight,
                        "confidence": e.confidence, "evidence_count": e.evidence_count,
                    }).execute()
        except Exception as exc:
            LOGGER.warning("[Mimograph] Seed error (non-fatal): %s", exc)

    # ── Node operations ────────────────────────────────────────────────
    def get_node(self, node_id: str) -> Optional[Dict]:
        db = get_db()
        if not db:
            return None
        try:
            res = db.table(NODES_TABLE).select("*").eq("node_id", node_id).limit(1).execute()
            return res.data[0] if res.data else None
        except Exception as exc:
            LOGGER.error("[Mimograph] get_node error: %s", exc)
            return None

    def get_nodes_by_type(self, node_type: NodeType) -> List[Dict]:
        db = get_db()
        if not db:
            return []
        try:
            res = db.table(NODES_TABLE).select("*").eq("node_type", node_type.value).order("strength", desc=True).execute()
            return res.data or []
        except Exception as exc:
            LOGGER.error("[Mimograph] get_nodes_by_type error: %s", exc)
            return []

    def update_node(self, node_id: str, evidence: str, strength_delta: float = 0.05):
        """Update node strength based on new evidence."""
        db = get_db()
        if not db:
            return
        try:
            node = self.get_node(node_id)
            if not node:
                return
            new_strength = max(0.0, min(1.0, node["strength"] + strength_delta))
            new_confidence = min(1.0, node.get("confidence", 0.1) + 0.03)
            db.table(NODES_TABLE).update({
                "strength": round(new_strength, 4),
                "confidence": round(new_confidence, 4),
                "evidence_count": node.get("evidence_count", 0) + 1,
                "last_evidence": evidence[:200],
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("node_id", node_id).execute()
        except Exception as exc:
            LOGGER.error("[Mimograph] update_node error: %s", exc)

    def add_node(self, node_id: str, label: str, node_type: NodeType,
                 strength: float = 0.5, evidence: str = ""):
        """Discover a new node (trait, behavior, blocker, etc.)."""
        db = get_db()
        if not db:
            return
        try:
            db.table(NODES_TABLE).upsert({
                "node_id": node_id, "label": label,
                "node_type": node_type.value, "strength": strength,
                "confidence": 0.2, "evidence_count": 1,
                "last_evidence": evidence[:200],
            }).execute()
        except Exception as exc:
            LOGGER.error("[Mimograph] add_node error: %s", exc)

    # ── Edge operations ────────────────────────────────────────────────
    def get_edges_for(self, node_id: str) -> List[Dict]:
        """Get all edges connected to a node."""
        db = get_db()
        if not db:
            return []
        try:
            outgoing = db.table(EDGES_TABLE).select("*").eq("source_id", node_id).execute()
            incoming = db.table(EDGES_TABLE).select("*").eq("target_id", node_id).execute()
            return (outgoing.data or []) + (incoming.data or [])
        except Exception as exc:
            LOGGER.error("[Mimograph] get_edges_for error: %s", exc)
            return []

    def get_contradictions_for(self, node_id: str) -> List[Dict]:
        """Get all contradicting edges for a node."""
        db = get_db()
        if not db:
            return []
        try:
            res = db.table(EDGES_TABLE).select("*").eq("target_id", node_id).eq("edge_type", EdgeType.CONTRADICTS.value).order("weight", desc=True).execute()
            return res.data or []
        except Exception as exc:
            LOGGER.error("[Mimograph] get_contradictions_for error: %s", exc)
            return []

    def get_blockers_for(self, node_id: str) -> List[Dict]:
        """Get all blockers for a node."""
        db = get_db()
        if not db:
            return []
        try:
            res = db.table(EDGES_TABLE).select("*").eq("target_id", node_id).eq("edge_type", EdgeType.BLOCKS.value).execute()
            return res.data or []
        except Exception as exc:
            LOGGER.error("[Mimograph] get_blockers_for error: %s", exc)
            return []

    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType,
                 weight: float = 0.5):
        """Add or update an edge between nodes."""
        db = get_db()
        if not db:
            return
        try:
            # Upsert based on source+target+type
            db.table(EDGES_TABLE).upsert({
                "source_id": source_id, "target_id": target_id,
                "edge_type": edge_type.value, "weight": weight,
                "confidence": 0.3, "evidence_count": 1,
            }).execute()
        except Exception as exc:
            LOGGER.error("[Mimograph] add_edge error: %s", exc)

    # ── Graph queries ──────────────────────────────────────────────────
    def what_blocks(self, goal_id: str) -> List[Dict]:
        """What is blocking this goal?"""
        blockers = self.get_blockers_for(goal_id)
        result = []
        for b in blockers:
            node = self.get_node(b["source_id"])
            if node:
                result.append({"blocker": node["label"], "weight": b["weight"],
                               "node_id": b["source_id"]})
        return result

    def what_energizes(self) -> List[Dict]:
        """What energizes Akua?"""
        return self.get_nodes_by_type(NodeType.REWARD)

    def what_drains(self) -> List[Dict]:
        """What drains Akua?"""
        return self.get_nodes_by_type(NodeType.AVOIDANCE)

    def get_full_graph(self) -> Dict:
        """Export the entire belief graph."""
        db = get_db()
        if not db:
            return {"nodes": [], "edges": []}
        try:
            nodes = db.table(NODES_TABLE).select("*").execute()
            edges = db.table(EDGES_TABLE).select("*").execute()
            return {"nodes": nodes.data or [], "edges": edges.data or []}
        except Exception as exc:
            LOGGER.error("[Mimograph] get_full_graph error: %s", exc)
            return {"nodes": [], "edges": []}
