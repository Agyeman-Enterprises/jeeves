"""
Ad Experiments Specialist
Handles A/B testing for ad creatives, copy, audiences, and bidding strategies.
"""

from app.agents.base_specialist import SpecialistAgent
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics


class AdExperimentsSpecialist(SpecialistAgent):
    """
    Specialist for A/B testing in advertising.

    Responsibilities:
    - Create experiments with multiple arms
    - Track arm performance
    - Determine statistical significance
    - Declare winners
    - Auto-promote winners
    """

    id = "spec.ads.experiments"
    display_name = "Ad Experiments Specialist"
    master_id = "master.advertising"
    role = "experiments"

    # Minimum thresholds for declaring winner
    MIN_CONVERSIONS_PER_ARM = 10
    MIN_CONFIDENCE = 0.95  # 95% confidence
    MIN_LIFT_PERCENT = 10  # 10% improvement over control

    def get_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "role": self.role,
            "capabilities": [
                "create_experiment",
                "evaluate_experiment",
                "declare_winner",
                "get_experiment_status",
            ],
            "thresholds": {
                "min_conversions_per_arm": self.MIN_CONVERSIONS_PER_ARM,
                "min_confidence": self.MIN_CONFIDENCE,
                "min_lift_percent": self.MIN_LIFT_PERCENT,
            },
        }

    def run_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an experiment task.

        Task types:
        - create: Create a new experiment
        - evaluate: Evaluate experiment results
        - declare_winner: Declare and promote winner
        - status: Get experiment status

        Args:
            task_type: Type of task to execute
            payload: Task-specific parameters

        Returns:
            Task result with experiment data
        """
        handlers = {
            "create": self._create_experiment,
            "evaluate": self._evaluate_experiment,
            "declare_winner": self._declare_winner,
            "status": self._get_status,
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

    def _create_experiment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new A/B experiment."""
        workspace_id = payload.get("workspace_id")
        name = payload.get("name")
        hypothesis = payload.get("hypothesis")
        variable = payload.get("variable", "creative")  # creative, copy, audience, bid
        arms = payload.get("arms", [])

        return {
            "specialist": self.id,
            "task_type": "create",
            "status": "pending_implementation",
            "workspace_id": workspace_id,
            "name": name,
            "hypothesis": hypothesis,
            "variable": variable,
            "arm_count": len(arms),
        }

    def _evaluate_experiment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate experiment results and determine if ready for decision."""
        experiment_id = payload.get("experiment_id")
        arms = payload.get("arms", [])

        if len(arms) < 2:
            return {
                "specialist": self.id,
                "task_type": "evaluate",
                "status": "error",
                "error": "Experiment must have at least 2 arms",
            }

        # Find control arm
        control = next((a for a in arms if a.get("is_control")), arms[0])
        variants = [a for a in arms if a != control]

        evaluation = self.evaluate_arms(control, variants)

        return {
            "specialist": self.id,
            "task_type": "evaluate",
            "status": "success",
            "experiment_id": experiment_id,
            "evaluation": evaluation,
        }

    def _declare_winner(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Declare the winner of an experiment."""
        experiment_id = payload.get("experiment_id")
        winner_arm_id = payload.get("winner_arm_id")
        confidence = payload.get("confidence", 0)
        lift = payload.get("lift", 0)

        return {
            "specialist": self.id,
            "task_type": "declare_winner",
            "status": "pending_implementation",
            "experiment_id": experiment_id,
            "winner_arm_id": winner_arm_id,
            "confidence": confidence,
            "lift": lift,
        }

    def _get_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get current experiment status."""
        experiment_id = payload.get("experiment_id")

        return {
            "specialist": self.id,
            "task_type": "status",
            "status": "pending_implementation",
            "experiment_id": experiment_id,
        }

    def evaluate_arms(
        self,
        control: Dict[str, Any],
        variants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate experiment arms and determine if there's a winner.

        Args:
            control: Control arm metrics
            variants: List of variant arm metrics

        Returns:
            Evaluation results with winner recommendation
        """
        control_cpa = control.get("cpa", float('inf'))
        control_conversions = control.get("conversions", 0)

        # Check if control has enough data
        if control_conversions < self.MIN_CONVERSIONS_PER_ARM:
            return {
                "ready_for_decision": False,
                "reason": f"Control needs {self.MIN_CONVERSIONS_PER_ARM - control_conversions} more conversions",
                "control": control,
                "variants": variants,
                "winner": None,
            }

        # Evaluate each variant
        results = []
        for variant in variants:
            variant_cpa = variant.get("cpa", float('inf'))
            variant_conversions = variant.get("conversions", 0)

            # Check if variant has enough data
            if variant_conversions < self.MIN_CONVERSIONS_PER_ARM:
                results.append({
                    **variant,
                    "has_enough_data": False,
                    "lift": None,
                    "is_winner": False,
                })
                continue

            # Calculate lift (negative for CPA = good)
            if control_cpa > 0:
                lift = ((control_cpa - variant_cpa) / control_cpa) * 100
            else:
                lift = 0

            # Simple win condition: better CPA with enough lift
            is_winner = (
                variant_cpa < control_cpa and
                lift >= self.MIN_LIFT_PERCENT
            )

            results.append({
                **variant,
                "has_enough_data": True,
                "lift": round(lift, 1),
                "is_winner": is_winner,
            })

        # Find best performer
        ready_variants = [r for r in results if r.get("has_enough_data")]
        winner = None

        if ready_variants:
            # Sort by lift (highest first)
            sorted_variants = sorted(
                ready_variants,
                key=lambda x: x.get("lift", 0),
                reverse=True
            )
            if sorted_variants[0].get("is_winner"):
                winner = sorted_variants[0]

        return {
            "ready_for_decision": all(r.get("has_enough_data") for r in results),
            "reason": "Sufficient data collected" if winner else "No clear winner yet",
            "control": {
                **control,
                "lift": 0,
                "is_winner": winner is None,  # Control wins if no variant beats it
            },
            "variants": results,
            "winner": winner,
        }

    def suggest_next_experiment(
        self,
        workspace_id: str,
        recent_experiments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggest the next experiment to run based on past results.

        Args:
            workspace_id: Workspace to suggest for
            recent_experiments: List of recent experiment results

        Returns:
            Suggested experiment configuration
        """
        # Count experiment types
        type_counts = {}
        for exp in recent_experiments:
            var_type = exp.get("variable", "unknown")
            type_counts[var_type] = type_counts.get(var_type, 0) + 1

        # Suggest least-tested variable type
        all_types = ["creative", "copy", "audience", "bid"]
        min_count = float('inf')
        suggested_type = "creative"

        for var_type in all_types:
            count = type_counts.get(var_type, 0)
            if count < min_count:
                min_count = count
                suggested_type = var_type

        suggestions = {
            "creative": {
                "variable": "creative",
                "hypothesis": "Different visual styles will impact conversion rate",
                "suggested_arms": ["Static image", "Video", "Carousel"],
            },
            "copy": {
                "variable": "copy",
                "hypothesis": "Different messaging angles will impact CTR",
                "suggested_arms": ["Benefit-focused", "Pain-point focused", "Social proof"],
            },
            "audience": {
                "variable": "audience",
                "hypothesis": "Different targeting will impact CPA",
                "suggested_arms": ["Broad", "Interest-based", "Lookalike"],
            },
            "bid": {
                "variable": "bid",
                "hypothesis": "Different bid strategies will impact ROAS",
                "suggested_arms": ["Lowest cost", "Cost cap", "Bid cap"],
            },
        }

        return {
            "workspace_id": workspace_id,
            "suggested_experiment": suggestions[suggested_type],
            "reason": f"{suggested_type} has been tested least ({min_count} times)",
        }
