"""
Meta Creatives Specialist
Handles creative asset management for Meta (Facebook/Instagram) ads.
"""

from app.agents.base_specialist import SpecialistAgent
from typing import Dict, Any, List


class MetaCreativesSpecialist(SpecialistAgent):
    """
    Specialist for Meta ad creative management.

    Responsibilities:
    - Generate creative variants (copy, headlines, CTAs)
    - Manage creative library
    - Track creative performance
    - Rotate underperforming creatives
    """

    id = "spec.ads.meta.creatives"
    display_name = "Meta Creatives Specialist"
    master_id = "master.advertising"
    role = "creative_management"

    def get_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "role": self.role,
            "platform": "meta",
            "capabilities": [
                "generate_variants",
                "rotate_creative",
                "get_performance",
                "archive_creative",
            ],
        }

    def run_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a creative management task.

        Task types:
        - generate: Generate creative variants
        - rotate: Rotate underperforming creative
        - performance: Get creative performance metrics
        - archive: Archive a creative

        Args:
            task_type: Type of task to execute
            payload: Task-specific parameters

        Returns:
            Task result with status and data
        """
        handlers = {
            "generate": self._generate_variants,
            "rotate": self._rotate_creative,
            "performance": self._get_performance,
            "archive": self._archive_creative,
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

    def _generate_variants(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate creative variants from a base creative."""
        base_creative_id = payload.get("creative_id")
        variant_count = payload.get("variant_count", 3)
        variant_type = payload.get("variant_type", "copy")  # copy, headline, cta, image

        return {
            "specialist": self.id,
            "task_type": "generate",
            "status": "pending_implementation",
            "base_creative_id": base_creative_id,
            "variant_count": variant_count,
            "variant_type": variant_type,
        }

    def _rotate_creative(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Rotate out an underperforming creative."""
        ad_id = payload.get("ad_id")
        new_creative_id = payload.get("new_creative_id")
        reason = payload.get("reason", "performance_decline")

        return {
            "specialist": self.id,
            "task_type": "rotate",
            "status": "pending_implementation",
            "ad_id": ad_id,
            "new_creative_id": new_creative_id,
            "reason": reason,
        }

    def _get_performance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get creative performance metrics."""
        creative_id = payload.get("creative_id")
        date_range = payload.get("date_range", "last_7_days")

        return {
            "specialist": self.id,
            "task_type": "performance",
            "status": "pending_implementation",
            "creative_id": creative_id,
            "date_range": date_range,
        }

    def _archive_creative(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Archive a creative (soft delete)."""
        creative_id = payload.get("creative_id")

        return {
            "specialist": self.id,
            "task_type": "archive",
            "status": "pending_implementation",
            "creative_id": creative_id,
        }

    def suggest_rotation_candidates(
        self,
        creatives: List[Dict[str, Any]],
        threshold_ctr: float = 0.005,
        threshold_frequency: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Identify creatives that should be rotated based on performance.

        Rules:
        - CTR below threshold (default 0.5%)
        - Frequency above threshold (default 3.0)

        Args:
            creatives: List of creative dicts with metrics
            threshold_ctr: Minimum acceptable CTR
            threshold_frequency: Maximum acceptable frequency

        Returns:
            List of creatives recommended for rotation
        """
        candidates = []

        for creative in creatives:
            ctr = creative.get("ctr", 0)
            frequency = creative.get("frequency", 0)

            should_rotate = False
            reasons = []

            if ctr < threshold_ctr:
                should_rotate = True
                reasons.append(f"CTR below threshold ({ctr:.3%} < {threshold_ctr:.3%})")

            if frequency > threshold_frequency:
                should_rotate = True
                reasons.append(f"Frequency above threshold ({frequency:.1f} > {threshold_frequency:.1f})")

            if should_rotate:
                candidates.append({
                    **creative,
                    "rotation_reasons": reasons,
                })

        return candidates
