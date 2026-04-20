from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.agents.base import AgentResponse, BaseAgent, AgentContext

if TYPE_CHECKING:
    # Avoid circular import at runtime; only for type hints
    from app.core.orchestrator import Orchestrator

LOGGER = logging.getLogger(__name__)


@dataclass
class SubTaskResult:
    agent: str
    query: str
    response: AgentResponse


class SupervisorAgent(BaseAgent):
    """
    Jarvis-as-Chief-of-Staff.

    Responsibilities:
    - Understand high-level intent behind a query.
    - Decide which specialist agent(s) should handle it.
    - Optionally break a big request into subtasks.
    - Call those agents through the Orchestrator.
    - Merge their results into a single AgentResponse.

    NOTE:
    - This agent does *not* talk to LLM directly; it orchestrates.
    - LLM calls are inside the specialist agents.
    """

    name: str = "SupervisorAgent"
    description: str = "High-level orchestrator that routes complex requests to the right specialist agents."
    capabilities: List[str] = [
        "routing",
        "decomposition",
        "multi-agent-coordination",
        "business-awareness",
        "schedule-awareness",
    ]

    def __init__(self, orchestrator: "Orchestrator") -> None:
        super().__init__()
        self.orchestrator = orchestrator

    def supports(self, query: str) -> bool:
        """
        Heuristic: We treat broad/strategic/multi-step requests as 'complex'.
        """
        q = query.lower()
        trigger_keywords = [
            "plan",
            "strategy",
            "launch",
            "campaign",
            "workflow",
            "set up",
            "coordinate",
            "manage",
            "briefing",
            "overview",
            "do xyz",
            "take care of",
            "handle this",
            "run",
            "automate",
        ]
        return any(k in q for k in trigger_keywords)

    def handle(self, query: str, context: Optional[AgentContext] = None) -> AgentResponse:
        """
        Decide which agents to call, call them via Orchestrator helper methods,
        and merge their responses.
        """
        context = context or {}

        business = context.get("business")  # e.g. "Bookadoc2u", "Needful Things"
        mode = context.get("mode")  # e.g. "marketing", "content", "tax"

        LOGGER.info("Supervisor handling query='%s' business=%s mode=%s", query, business, mode)

        plan = self._build_agent_plan(query, business, mode)
        if not plan:
            # Fallback: just let normal routing handle it
            return AgentResponse(
                agent=self.name,
                content=(
                    "I'm not detecting a multi-step workflow here. "
                    "It may be faster to ask a specific agent directly."
                ),
                data={"original_query": query},
                status="warning",
                warnings=["no_plan_built"],
            )

        subtasks: List[SubTaskResult] = []

        # Dispatch to each planned agent through orchestrator
        for agent_name, subquery in plan:
            resp = self.orchestrator.dispatch_to(agent_name, subquery, context)
            subtasks.append(SubTaskResult(agent=agent_name, query=subquery, response=resp))

        # Merge results into a single AgentResponse
        merged = self._merge_subtasks(query, subtasks, context)
        return merged

    # ---------- Internal helpers ----------

    def _build_agent_plan(
        self,
        query: str,
        business: Optional[str],
        mode: Optional[str],
    ) -> List[tuple[str, str]]:
        """
        Decide which agents to call and with what sub-queries.
        This is rule-based for now to avoid extra LLM cost.
        """

        q = query.lower()
        plan: List[tuple[str, str]] = []

        # Marketing / launch requests
        if mode == "marketing" or any(k in q for k in ("launch", "marketing", "campaign", "promo", "ads")):
            # Strategy → Copywriter → Social
            plan.append(("BusinessAgent", query))
            plan.append(("CopywriterAgent", query))
            plan.append(("SocialMediaManagerAgent", query))
            plan.append(("SEOEcommerceSpecialistAgent", query))
            return plan

        # Content flows (podcast, vlog, scripts, courses, etc.)
        if mode == "content" or any(k in q for k in ("podcast", "vlog", "script", "episode", "blog", "video")):
            plan.append(("CopywriterAgent", query))
            plan.append(("ContentAgent", query))
            plan.append(("SocialMediaManagerAgent", query))
            return plan

        # Sales / outreach flows
        if mode == "sales" or any(k in q for k in ("sales", "cold email", "outreach", "leads", "prospects")):
            plan.append(("SalesManagerAgent", query))
            plan.append(("BusinessDevelopmentSpecialistAgent", query))
            return plan

        # Analytics / reporting flows
        if mode == "analytics" or any(k in q for k in ("analytics", "forecast", "report", "dashboard", "metrics")):
            plan.append(("DataAnalystAgent", query))
            return plan

        # CEO briefing flows — delegate to executor for real data
        if any(k in q for k in ("briefing", "morning briefing", "daily briefing", "overview", "ceo brief")):
            # Pull NEXUS enterprise data via executor, then summarise
            self._trigger_nexus_briefing_async()
            plan.append(("EnterpriseCEOAgent", query))
            return plan

        # Default fallback: ask BusinessAgent for context, then Content/Copywriter
        plan.append(("BusinessAgent", query))
        plan.append(("CopywriterAgent", query))
        return plan

    def _trigger_nexus_briefing_async(self) -> None:
        """Fire-and-forget: ask executor to pull latest NEXUS briefing into context."""
        import asyncio
        try:
            from app.agents.jarvis_executor import get_executor, Decision, ActionType
            executor = get_executor()
            decision = Decision(
                action=ActionType.FETCH_NEXUS_BRIEFING,
                params={},
                reason="Supervisor triggered NEXUS pull for briefing query",
            )
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(executor.execute(decision))
            loop.close()
            if result.success and result.output:
                LOGGER.info(
                    "[SupervisorAgent] NEXUS briefing pulled: %d domains",
                    len(result.output) if isinstance(result.output, dict) else 1,
                )
        except Exception as exc:
            LOGGER.warning("[SupervisorAgent] NEXUS briefing pull failed (non-fatal): %s", exc)

    def _merge_subtasks(
        self,
        query: str,
        subtasks: List[SubTaskResult],
        context: AgentContext,
    ) -> AgentResponse:
        """
        Merge multiple AgentResponses into a single conversational Jarvis-style response.
        """
        if not subtasks:
            return AgentResponse(
                agent=self.name,
                content=(
                    "I attempted to coordinate, but none of the specialist agents were available. "
                    "We'll need to check the wiring."
                ),
                data={"original_query": query},
                status="error",
                warnings=["no_subtasks_executed"],
            )

        summary_lines: List[str] = []
        data: Dict[str, Any] = {"original_query": query, "subtasks": []}
        warnings: List[str] = []

        for st in subtasks:
            line = f"- {st.agent}: {st.response.status}"
            summary_lines.append(line)
            data["subtasks"].append(
                {
                    "agent": st.agent,
                    "query": st.query,
                    "status": st.response.status,
                    "data": st.response.data,
                    "warnings": st.response.warnings,
                }
            )
            warnings.extend(st.response.warnings or [])

        summary_block = "\n".join(summary_lines)

        # Short natural-language wrapper in Jarvis' voice
        content = (
            "I've coordinated the relevant systems. Here's what was done:\n\n"
            f"{summary_block}"
        )

        return AgentResponse(
            agent=self.name,
            content=content,
            data=data,
            status="success",
            warnings=warnings if warnings else None,
        )

