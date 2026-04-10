"""
Belief Schema — Mimograph nodes and edges.
The graph that represents who Akua really is.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    GOAL = "goal"
    BEHAVIOR = "behavior"
    PERSON = "person"
    PROJECT = "project"
    EMOTION = "emotion"
    BLOCKER = "blocker"
    ROUTINE = "routine"
    REWARD = "reward"
    AVOIDANCE = "avoidance"
    TRAIT = "trait"


class EdgeType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    PRECEDES = "precedes"
    PREDICTS = "predicts"
    DRAINS = "drains"
    ENERGIZES = "energizes"
    BLOCKS = "blocks"
    REQUIRES = "requires"


class BeliefNode(BaseModel):
    node_id: str
    label: str
    node_type: NodeType
    strength: float = 0.5    # 0-1
    confidence: float = 0.1  # 0-1
    evidence_count: int = 0
    last_evidence: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BeliefEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 0.5   # 0-1 strength of relationship
    confidence: float = 0.1
    evidence_count: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Seed beliefs for Akua ─────────────────────────────────────────────
SEED_NODES: List[BeliefNode] = [
    # Traits
    BeliefNode(node_id="trait_type_a", label="Type A Achiever", node_type=NodeType.TRAIT, strength=0.95, confidence=0.9),
    BeliefNode(node_id="trait_builder", label="Builder (not marketer)", node_type=NodeType.TRAIT, strength=0.9, confidence=0.85),
    BeliefNode(node_id="trait_direct", label="Responds to blunt feedback", node_type=NodeType.TRAIT, strength=0.8, confidence=0.7),
    # Behaviors
    BeliefNode(node_id="beh_avoids_marketing", label="Avoids marketing tasks", node_type=NodeType.BEHAVIOR, strength=0.7, confidence=0.6),
    BeliefNode(node_id="beh_builds_new", label="Builds new rather than sells existing", node_type=NodeType.BEHAVIOR, strength=0.8, confidence=0.7),
    BeliefNode(node_id="beh_eats_out", label="Eats out frequently", node_type=NodeType.BEHAVIOR, strength=0.8, confidence=0.8),
    BeliefNode(node_id="beh_defers_irs", label="Defers IRS-related tasks", node_type=NodeType.BEHAVIOR, strength=0.7, confidence=0.5),
    # Avoidances
    BeliefNode(node_id="avoid_cooking", label="Hates cooking", node_type=NodeType.AVOIDANCE, strength=0.9, confidence=0.9),
    BeliefNode(node_id="avoid_running", label="Hates running", node_type=NodeType.AVOIDANCE, strength=0.85, confidence=0.9),
    # Rewards
    BeliefNode(node_id="reward_swimming", label="Enjoys swimming", node_type=NodeType.REWARD, strength=0.7, confidence=0.8),
    BeliefNode(node_id="reward_crafts", label="Enjoys creative arts", node_type=NodeType.REWARD, strength=0.75, confidence=0.7),
    # Blockers
    BeliefNode(node_id="block_irs_passport", label="IRS seized passport", node_type=NodeType.BLOCKER, strength=1.0, confidence=1.0),
    BeliefNode(node_id="block_full_houses", label="Houses too full for crafts/3D printing", node_type=NodeType.BLOCKER, strength=0.85, confidence=0.9),
    BeliefNode(node_id="block_84hr_weeks", label="Works 84hr/week hospital", node_type=NodeType.BLOCKER, strength=0.95, confidence=0.95),
    # Projects (top ones)
    BeliefNode(node_id="proj_scribemd", label="ScribeMD Pro", node_type=NodeType.PROJECT, strength=0.8, confidence=0.7),
    BeliefNode(node_id="proj_taxrx", label="TaxRx", node_type=NodeType.PROJECT, strength=0.7, confidence=0.6),
    BeliefNode(node_id="proj_linahla", label="Linahla", node_type=NodeType.PROJECT, strength=0.7, confidence=0.6),
]

SEED_EDGES: List[BeliefEdge] = [
    # Contradictions
    BeliefEdge(source_id="beh_avoids_marketing", target_id="replace_income", edge_type=EdgeType.CONTRADICTS, weight=0.9),
    BeliefEdge(source_id="beh_builds_new", target_id="replace_income", edge_type=EdgeType.CONTRADICTS, weight=0.7),
    BeliefEdge(source_id="beh_eats_out", target_id="health_maintenance", edge_type=EdgeType.CONTRADICTS, weight=0.8),
    BeliefEdge(source_id="beh_defers_irs", target_id="resolve_irs", edge_type=EdgeType.CONTRADICTS, weight=0.9),
    # Blockers
    BeliefEdge(source_id="block_irs_passport", target_id="move_abroad", edge_type=EdgeType.BLOCKS, weight=1.0),
    BeliefEdge(source_id="block_full_houses", target_id="creative_arts", edge_type=EdgeType.BLOCKS, weight=0.85),
    BeliefEdge(source_id="block_84hr_weeks", target_id="exercise", edge_type=EdgeType.DRAINS, weight=0.9),
    # Supports
    BeliefEdge(source_id="proj_scribemd", target_id="replace_income", edge_type=EdgeType.SUPPORTS, weight=0.8),
    BeliefEdge(source_id="proj_taxrx", target_id="replace_income", edge_type=EdgeType.SUPPORTS, weight=0.6),
    BeliefEdge(source_id="reward_swimming", target_id="health_maintenance", edge_type=EdgeType.SUPPORTS, weight=0.7),
    BeliefEdge(source_id="trait_type_a", target_id="replace_income", edge_type=EdgeType.ENERGIZES, weight=0.8),
]
