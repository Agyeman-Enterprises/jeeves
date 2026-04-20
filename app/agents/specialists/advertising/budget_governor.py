"""
Budget Governor Specialist
Enforces budget policies, caps, and approval rules for ad spend.
"""

from app.agents.base_specialist import SpecialistAgent
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class BudgetGovernorSpecialist(SpecialistAgent):
    """
    Specialist for ad budget governance.

    Responsibilities:
    - Enforce daily/monthly spend caps
    - Scale budgets for winners (with limits)
    - Pause overspending campaigns
    - Require approval for high-impact changes
    - Detect spend anomalies
    """

    id = "spec.ads.budget"
    display_name = "Budget Governor Specialist"
    master_id = "master.advertising"
    role = "budget_governance"

    # Default policy values
    DEFAULT_DAILY_CAP = 50.0
    DEFAULT_SCALE_STEP = 0.20  # 20%
    DEFAULT_COOLDOWN_HOURS = 24
    DEFAULT_APPROVAL_THRESHOLD = 50.0
    DEFAULT_ANOMALY_MULTIPLIER = 2.0  # 2x spike = anomaly

    def get_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "role": self.role,
            "capabilities": [
                "check_spend_cap",
                "propose_scale",
                "check_anomaly",
                "require_approval",
            ],
            "default_policy": {
                "daily_cap": self.DEFAULT_DAILY_CAP,
                "scale_step": self.DEFAULT_SCALE_STEP,
                "cooldown_hours": self.DEFAULT_COOLDOWN_HOURS,
                "approval_threshold": self.DEFAULT_APPROVAL_THRESHOLD,
            },
        }

    def run_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a budget governance task.

        Task types:
        - check_cap: Check if spend is within cap
        - propose_scale: Propose budget scaling for a winner
        - check_anomaly: Check for spend anomalies
        - evaluate_approval: Determine if change needs approval

        Args:
            task_type: Type of task to execute
            payload: Task-specific parameters

        Returns:
            Task result with status and recommendations
        """
        handlers = {
            "check_cap": self._check_spend_cap,
            "propose_scale": self._propose_scale,
            "check_anomaly": self._check_anomaly,
            "evaluate_approval": self._evaluate_approval,
        }

        handler = handlers.get(task_type)
        if not handler:
            return {
                "specialist": self.id,
                "task_type": task_type,
                "status": "error",
                "error": f"Unknown task type: {task_type}",
            }

        return handler(payload)

    def _check_spend_cap(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check if current spend is within the daily cap."""
        current_spend = payload.get("current_spend", 0)
        daily_cap = payload.get("daily_cap", self.DEFAULT_DAILY_CAP)
        entity_id = payload.get("entity_id")
        entity_type = payload.get("entity_type", "campaign")

        remaining = max(0, daily_cap - current_spend)
        utilization = (current_spend / daily_cap * 100) if daily_cap > 0 else 100

        is_over_cap = current_spend >= daily_cap
        is_near_cap = utilization >= 80

        return {
            "specialist": self.id,
            "task_type": "check_cap",
            "status": "success",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "current_spend": current_spend,
            "daily_cap": daily_cap,
            "remaining": remaining,
            "utilization_percent": round(utilization, 1),
            "is_over_cap": is_over_cap,
            "is_near_cap": is_near_cap,
            "recommendation": "pause" if is_over_cap else ("monitor" if is_near_cap else "continue"),
        }

    def _propose_scale(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Propose budget scaling for a winning campaign/adset."""
        current_budget = payload.get("current_budget", 0)
        scale_step = payload.get("scale_step", self.DEFAULT_SCALE_STEP)
        max_budget = payload.get("max_budget")
        entity_id = payload.get("entity_id")
        entity_type = payload.get("entity_type", "adset")

        # Calculate proposed new budget
        increase = current_budget * scale_step
        proposed_budget = current_budget + increase

        # Cap at max budget if specified
        if max_budget and proposed_budget > max_budget:
            proposed_budget = max_budget
            capped = True
        else:
            capped = False

        return {
            "specialist": self.id,
            "task_type": "propose_scale",
            "status": "success",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "current_budget": current_budget,
            "proposed_budget": round(proposed_budget, 2),
            "increase_amount": round(proposed_budget - current_budget, 2),
            "increase_percent": round(scale_step * 100, 1),
            "capped_at_max": capped,
        }

    def _check_anomaly(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check for spend anomalies (sudden spikes)."""
        current_spend = payload.get("current_spend", 0)
        average_spend = payload.get("average_spend", 0)
        anomaly_threshold = payload.get("anomaly_threshold", self.DEFAULT_ANOMALY_MULTIPLIER)
        entity_id = payload.get("entity_id")

        # Avoid division by zero
        if average_spend <= 0:
            is_anomaly = current_spend > 0
            multiplier = float('inf') if is_anomaly else 0
        else:
            multiplier = current_spend / average_spend
            is_anomaly = multiplier >= anomaly_threshold

        return {
            "specialist": self.id,
            "task_type": "check_anomaly",
            "status": "success",
            "entity_id": entity_id,
            "current_spend": current_spend,
            "average_spend": average_spend,
            "multiplier": round(multiplier, 2) if multiplier != float('inf') else "infinite",
            "threshold": anomaly_threshold,
            "is_anomaly": is_anomaly,
            "recommendation": "panic_pause" if is_anomaly else "continue",
        }

    def _evaluate_approval(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Determine if a proposed change requires approval."""
        change_type = payload.get("change_type")  # scale, pause, create, etc.
        impact_amount = payload.get("impact_amount", 0)
        approval_threshold = payload.get("approval_threshold", self.DEFAULT_APPROVAL_THRESHOLD)
        entity_id = payload.get("entity_id")

        requires_approval = abs(impact_amount) >= approval_threshold

        return {
            "specialist": self.id,
            "task_type": "evaluate_approval",
            "status": "success",
            "entity_id": entity_id,
            "change_type": change_type,
            "impact_amount": impact_amount,
            "approval_threshold": approval_threshold,
            "requires_approval": requires_approval,
            "reason": f"Impact ${impact_amount:.2f} {'exceeds' if requires_approval else 'within'} threshold ${approval_threshold:.2f}",
        }

    def evaluate_decisions(
        self,
        decisions: List[Dict[str, Any]],
        policy: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate a batch of proposed decisions against policy.

        Args:
            decisions: List of proposed decision dicts
            policy: Workspace policy overrides

        Returns:
            Decisions with governance annotations
        """
        pol = policy or {}
        daily_cap = pol.get("daily_spend_cap", self.DEFAULT_DAILY_CAP)
        approval_threshold = pol.get("requires_approval_above", self.DEFAULT_APPROVAL_THRESHOLD)
        cooldown_hours = pol.get("cooldown_hours", self.DEFAULT_COOLDOWN_HOURS)

        evaluated = []
        for decision in decisions:
            impact = decision.get("impact_estimate", 0)

            evaluation = {
                **decision,
                "governance": {
                    "requires_approval": abs(impact) >= approval_threshold,
                    "within_daily_cap": impact <= (daily_cap - decision.get("current_spend", 0)),
                    "cooldown_hours": cooldown_hours,
                }
            }
            evaluated.append(evaluation)

        return evaluated
