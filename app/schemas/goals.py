"""
Goal Schema — The ranking system at the heart of Jeeves.
Every goal has stated weight, revealed weight, effective weight,
contradiction score, volatility, confidence, and decay.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Goal(BaseModel):
    """A tracked goal with dynamic weighting."""
    goal_id: str
    label: str
    category: str = "general"  # income, health, logistics, creative, business, finance
    description: str = ""

    # The three weights
    stated_weight: float = 0.5       # what Akua says (0-1)
    revealed_weight: float = 0.0     # what behavior shows (0-1)
    effective_weight: float = 0.5    # computed: f(stated, revealed, persistence, recency, sacrifice)

    # Analysis
    confidence: float = 0.1          # how much data we have (0-1)
    contradiction_score: float = 0.0 # how misaligned stated vs revealed (0-1)
    volatility: float = 0.0          # how much the weight fluctuates

    # Counters
    action_count: int = 0
    skip_count: int = 0
    defer_count: int = 0

    # Decay
    decay_half_life_days: float = 30.0  # how fast intentions decay without action
    last_evidence_at: Optional[datetime] = None

    # Metadata
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GoalUpdate(BaseModel):
    """An action or observation related to a goal."""
    goal_id: str
    action_score: float  # 1.0 = strongly supports, -1.0 = strongly contradicts
    description: str = ""
    source: str = "manual"


# ── Seed goals for Akua ───────────────────────────────────────────────
SEED_GOALS: List[Goal] = [
    Goal(goal_id="replace_income", label="Replace Hospital Income",
         category="income", stated_weight=1.0,
         description="Target $1M/yr after taxes. Currently $165/hr hospital. Must replace by EOY 2026.",
         decay_half_life_days=14),
    Goal(goal_id="resolve_irs", label="Resolve IRS Debt",
         category="finance", stated_weight=1.0,
         description="$150K owed, passport seized. Blocks travel to Portugal/Ghana.",
         decay_half_life_days=7),
    Goal(goal_id="retire_medicine", label="Retire from Medicine Practice",
         category="income", stated_weight=0.95,
         description="Not retiring entirely — switching to running businesses from home.",
         decay_half_life_days=60),
    Goal(goal_id="launch_healthcare", label="Launch Healthcare SaaS Apps",
         category="business", stated_weight=0.9,
         description="AccessMD, MedRx, Linahla, MyHealthAlly, ScribeMD Pro, DrAMD.health",
         decay_half_life_days=14),
    Goal(goal_id="health_maintenance", label="Basic Health Maintenance",
         category="health", stated_weight=0.9,
         description="Hates cooking, eating out causing obesity. Likes swimming + weights.",
         decay_half_life_days=3),
    Goal(goal_id="move_abroad", label="Move to Portugal/Ghana",
         category="logistics", stated_weight=0.85,
         description="Owns property both. Portugal visa needs $3.5K/yr. Ghana is primary.",
         decay_half_life_days=90),
    Goal(goal_id="content_empire", label="Build Content Empire",
         category="business", stated_weight=0.8,
         description="17 books on Amazon (0 sales), DrAMD podcast, ScalpelNStack.",
         decay_half_life_days=21),
    Goal(goal_id="marketing_engine", label="Launch Marketing Engine",
         category="business", stated_weight=0.8,
         description="Stratova + ContentForge + Neuralia = autonomous marketing. No ad budget.",
         decay_half_life_days=14),
    Goal(goal_id="launch_tax", label="Launch Tax/Finance Apps",
         category="business", stated_weight=0.75,
         description="TaxRx + EntityTaxPro. Seasonal (Q1).",
         decay_half_life_days=30),
    Goal(goal_id="creative_arts", label="Creative Arts Practice",
         category="creative", stated_weight=0.6,
         description="Jewelry, pottery, glass, painting, drawing, shoemaking, 3D printing.",
         decay_half_life_days=30),
    Goal(goal_id="consolidate_stuff", label="Consolidate Physical Possessions",
         category="logistics", stated_weight=0.55,
         description="Stuff in AU, CA, GU, HI. 2 rented houses in GU. Shutting down HI.",
         decay_half_life_days=60),
    Goal(goal_id="launch_games", label="Launch Games Portfolio",
         category="business", stated_weight=0.5,
         description="Aeria/OpenArcade, ThreadHarp, Election Empire, Furfubu.",
         decay_half_life_days=60),
    Goal(goal_id="exercise", label="Exercise Regularly",
         category="health", stated_weight=0.4,
         description="Swimming + weight lifting. Running hated. 12hr shifts complicate scheduling.",
         decay_half_life_days=3),
    Goal(goal_id="launch_crypto", label="Launch Crypto (Purrkoin)",
         category="business", stated_weight=0.3,
         description="Meme coin now. SEC registration for full crypto. $100K+ cost.",
         decay_half_life_days=90),
]
