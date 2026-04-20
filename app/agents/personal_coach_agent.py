from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)


@dataclass
class Goal:
    category: str  # health, career, personal, financial, learning
    description: str
    target_date: Optional[date] = None
    status: str = "active"  # active, completed, paused
    progress: int = 0  # 0-100

    def to_dict(self) -> Dict[str, str]:
        return {
            "category": self.category,
            "description": self.description,
            "target_date": self.target_date.isoformat() if self.target_date else "",
            "status": self.status,
            "progress": str(self.progress),
        }


class PersonalCoachAgent(BaseAgent):
    """Acts as a personal coach for goal setting, motivation, and personal development."""

    data_path = Path("data") / "sample_personal_goals.json"
    description = "Helps with goal setting, motivation, and personal development coaching."
    capabilities = [
        "Set and track personal goals",
        "Provide motivation and accountability",
        "Create action plans",
        "Track progress",
        "Offer coaching insights",
        "Help with work-life balance",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.goals = self._load_goals()

    def supports(self, query: str) -> bool:
        keywords = [
            "goal",
            "coach",
            "motivation",
            "personal",
            "development",
            "progress",
            "accountability",
            "balance",
            "wellness",
            "health",
        ]
        return any(keyword in query.lower() for keyword in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()

        if "goal" in query_lower:
            return self._handle_goals()
        elif "progress" in query_lower:
            return self._handle_progress_tracking()
        elif "motivation" in query_lower or "encourage" in query_lower:
            return self._handle_motivation(query, context)
        elif "plan" in query_lower or "action" in query_lower:
            return self._handle_action_plan(query, context)
        elif "balance" in query_lower or "wellness" in query_lower:
            return self._handle_work_life_balance()
        else:
            return self._handle_general_coaching(query, context)

    def _handle_goals(self) -> AgentResponse:
        active_goals = [g for g in self.goals if g.status == "active"]
        if not active_goals:
            return AgentResponse(
                agent=self.name,
                content="No active goals set. Let's set some goals to work towards!",
                data={"goals": []},
            )

        lines = [f"Active Goals: {len(active_goals)}"]
        by_category: Dict[str, List[Goal]] = {}
        for goal in active_goals:
            by_category.setdefault(goal.category, []).append(goal)

        for category, goals in by_category.items():
            lines.append(f"\n{category.title()}:")
            for goal in goals:
                progress_bar = "█" * (goal.progress // 10) + "░" * (10 - goal.progress // 10)
                lines.append(f"  {goal.description} [{progress_bar}] {goal.progress}%")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"goals": [g.to_dict() for g in active_goals]},
        )

    def _handle_progress_tracking(self) -> AgentResponse:
        active_goals = [g for g in self.goals if g.status == "active"]
        if not active_goals:
            return AgentResponse(
                agent=self.name,
                content="No goals to track. Set some goals first!",
                data={},
            )

        avg_progress = sum(g.progress for g in active_goals) / len(active_goals) if active_goals else 0
        lines = [
            "Progress Tracking",
            f"\nAverage progress across all goals: {avg_progress:.1f}%",
            f"Total active goals: {len(active_goals)}",
        ]

        # Highlight goals needing attention
        low_progress = [g for g in active_goals if g.progress < 30]
        if low_progress:
            lines.append(f"\nGoals needing attention ({len(low_progress)}):")
            for goal in low_progress[:3]:
                lines.append(f"- {goal.description} ({goal.progress}%)")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"average_progress": avg_progress, "goals": [g.to_dict() for g in active_goals]},
        )

    def _handle_motivation(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Motivation & Encouragement",
            "",
            "You're doing great! Here's some encouragement:",
            "",
            "💪 Remember: Progress, not perfection.",
            "🎯 Small steps lead to big achievements.",
            "🌟 You've accomplished so much already.",
            "",
            "What specific area would you like motivation for?",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _handle_action_plan(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Action Plan Creation",
            "",
            "I can help you create action plans for:",
            "- Achieving specific goals",
            "- Breaking down large objectives",
            "- Daily/weekly routines",
            "- Habit formation",
            "- Skill development",
            "",
            "Tell me what you want to achieve, and I'll create a step-by-step plan.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _handle_work_life_balance(self) -> AgentResponse:
        lines = [
            "Work-Life Balance",
            "",
            "I can help you:",
            "- Assess your current balance",
            "- Set boundaries",
            "- Prioritize self-care",
            "- Manage time effectively",
            "- Reduce burnout",
            "",
            "How are you feeling about your work-life balance right now?",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _handle_general_coaching(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Personal Coach Ready",
            "",
            "I'm here to help you:",
            "- Set and achieve goals",
            "- Stay motivated and accountable",
            "- Create action plans",
            "- Track your progress",
            "- Maintain work-life balance",
            "",
            "What would you like to work on today?",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _load_goals(self) -> List[Goal]:
        if not self.data_path.exists():
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            goals: List[Goal] = []
            for entry in data:
                try:
                    target_date = None
                    if entry.get("target_date"):
                        target_date = datetime.fromisoformat(entry["target_date"]).date()

                    goals.append(
                        Goal(
                            category=entry.get("category", "personal"),
                            description=entry.get("description", ""),
                            target_date=target_date,
                            status=entry.get("status", "active"),
                            progress=int(entry.get("progress", 0)),
                        )
                    )
                except Exception as exc:
                    LOGGER.debug("Skipping malformed goal: %s", exc)
            return goals
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

