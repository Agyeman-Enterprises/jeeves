"""
Contradiction Engine — Detects and analyzes contradictions.
The engine that says "you say X but you do Y".
"""

from __future__ import annotations

import logging
from typing import Dict, List

from app.modeling.mimograph import Mimograph
from app.modeling.weighting_engine import WeightingEngine
from app.schemas.beliefs import EdgeType

LOGGER = logging.getLogger(__name__)


class ContradictionEngine:
    """
    Combines weighting contradictions (stated vs revealed)
    with mimograph contradictions (behavioral edges)
    to produce a unified contradiction report.
    """

    def __init__(self, weighting: WeightingEngine, mimograph: Mimograph):
        self.weighting = weighting
        self.mimograph = mimograph

    def get_full_contradiction_report(self) -> List[Dict]:
        """
        Merge weight-based and graph-based contradictions.
        Returns sorted list with explanation text.
        """
        report = []

        # Weight-based contradictions
        weight_contradictions = self.weighting.get_contradictions()
        for wc in weight_contradictions:
            explanation = self._explain_weight_contradiction(wc)
            report.append({
                "source": "weighting",
                "goal_id": wc["goal_id"],
                "label": wc["label"],
                "severity": wc["severity"],
                "score": wc["contradiction_score"],
                "explanation": explanation,
                "question": self._generate_question(wc),
            })

        # Graph-based contradictions (behaviors that contradict goals)
        goals = self.weighting.get_goals()
        for g in goals:
            graph_contradictions = self.mimograph.get_contradictions_for(g["goal_id"])
            for gc in graph_contradictions:
                source_node = self.mimograph.get_node(gc["source_id"])
                if source_node:
                    report.append({
                        "source": "mimograph",
                        "goal_id": g["goal_id"],
                        "label": g["label"],
                        "severity": "warning" if gc["weight"] > 0.7 else "info",
                        "score": gc["weight"],
                        "explanation": f"'{source_node['label']}' contradicts '{g['label']}' (strength: {gc['weight']:.0%})",
                        "question": f"I notice '{source_node['label']}' while '{g['label']}' is a priority. What's going on?",
                    })

        # Deduplicate by goal_id, keep highest score
        seen = {}
        for item in report:
            key = item["goal_id"]
            if key not in seen or item["score"] > seen[key]["score"]:
                seen[key] = item
        report = sorted(seen.values(), key=lambda x: x["score"], reverse=True)

        return report

    def _explain_weight_contradiction(self, wc: Dict) -> str:
        stated = wc["stated_weight"]
        revealed = wc["revealed_weight"]
        actions = wc.get("action_count", 0)
        skips = wc.get("skip_count", 0)

        if stated > 0.8 and revealed < 0.3:
            return (f"You say '{wc['label']}' is {stated:.0%} important, "
                    f"but your actions show {revealed:.0%}. "
                    f"({actions} supporting actions vs {skips} skips). "
                    f"This is a core goal with low follow-through — likely fear, avoidance, or external blocker.")
        elif stated > 0.6 and revealed < stated * 0.5:
            return (f"'{wc['label']}' has a gap: stated {stated:.0%} vs revealed {revealed:.0%}. "
                    f"Either the goal needs reprioritizing or something is blocking progress.")
        else:
            return f"Minor misalignment on '{wc['label']}': stated {stated:.0%} vs revealed {revealed:.0%}."

    def _generate_question(self, wc: Dict) -> str:
        stated = wc["stated_weight"]
        label = wc["label"]
        skips = wc.get("skip_count", 0)

        if wc["severity"] == "critical":
            return (f"'{label}' is one of your top priorities ({stated:.0%}), "
                    f"but you've skipped it {skips} times. "
                    f"Is the goal wrong, is something blocking you, or do you need help?")
        elif wc["severity"] == "warning":
            return f"You haven't been acting on '{label}' lately. Should I deprioritize it or find a better time?"
        else:
            return f"How do you feel about progress on '{label}'?"
