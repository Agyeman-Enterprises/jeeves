"""
Enterprise CEO Agent
Provides AI CEO reasoning over the enterprise graph structure.

Also generates the ops health section for the morning briefing by pulling
data from Sentry (errors), PostHog (analytics), Resend (email), and Vercel
(deployment status).
"""

import logging
from pathlib import Path
from typing import Optional, Any

from app.core.enterprise_graph import EnterpriseGraph

LOGGER = logging.getLogger(__name__)


def build_ceo_context_snippet(graph: EnterpriseGraph) -> str:
    """Build a compact context string for the CEO prompt."""
    summary = graph.summarize_enterprise_structure()
    lines = []

    tenant = summary.get("tenant") or {}
    lines.append(f"Tenant: {tenant.get('name', 'Unknown')}")

    for ws in summary.get("workspaces", []):
        lines.append(f"\n- Workspace: {ws['workspace_name']} ({ws.get('workspace_slug', 'N/A')})")
        lines.append(f"  Companies ({ws['company_count']}): {', '.join(ws['companies']) if ws['companies'] else 'None'}")
        lines.append(f"  Modules ({ws['module_count']}): {', '.join(ws['modules']) if ws['modules'] else 'None'}")

    systems = summary.get("systems", [])
    if systems:
        lines.append(f"\nGlobal Systems: {', '.join(systems)}")

    return "\n".join(lines)


def answer_ceo_question(
    question: str,
    ollama_service: Optional[Any] = None,
) -> str:
    """
    Answer a CEO-level question about the enterprise structure.
    
    Args:
        question: The user's question about the enterprise
        ollama_service: Optional OllamaService instance for LLM calls
    
    Returns:
        Generated answer string
    """
    try:
        graph = EnterpriseGraph()
    except FileNotFoundError as e:
        return (
            f"Enterprise context not available: {e}\n\n"
            "Please run 'refresh enterprise context' to load data from JarvisCore."
        )

    context_snippet = build_ceo_context_snippet(graph)

    # Load CEO system prompt
    prompt_path = Path("backend/ai/prompts/ceo_system_prompt.md")
    if prompt_path.exists():
        system_prompt = prompt_path.read_text(encoding="utf-8")
    else:
        system_prompt = "You are Jarvis, the AI CEO for Agyeman Enterprises."

    # Use OllamaService if provided, otherwise return fallback
    if ollama_service is None:
        # Fallback: basic deterministic answer without LLM
        return (
            "LLM CEO agent not fully wired yet.\n\n"
            "Here is your current enterprise context:\n\n"
            f"{context_snippet}\n\n"
            f"Original question: {question}"
        )

    try:
        # Call Ollama via the service
        user_prompt = (
            f"Enterprise context:\n{context_snippet}\n\n"
            f"Question:\n{question}\n\n"
            "Answer as the AI CEO."
        )

        response = ollama_service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        return response if isinstance(response, str) else str(response)

    except Exception as e:
        return (
            f"Error generating CEO response: {e}\n\n"
            "Here is your current enterprise context:\n\n"
            f"{context_snippet}\n\n"
            f"Original question: {question}"
        )


# ── Ops health section (called by morning briefing scheduler) ─────────────────

def build_ops_health_section(hours: int = 24) -> str:
    """
    Pull live data from Sentry, PostHog, and Vercel and return a formatted
    markdown section for inclusion in the CEO morning briefing.

    Args:
        hours: Look-back window for new issues / failed deployments (default: 24)

    Returns:
        Markdown string with headings for each service.
    """
    sections: list[str] = ["# Ops Health Dashboard\n"]

    # ── Sentry ────────────────────────────────────────────────────────────────
    try:
        from app.services.sentry_service import SentryService
        sentry = SentryService()
        sections.append(sentry.format_briefing_section(hours=hours))
    except Exception as exc:
        LOGGER.warning("CEO ops health — Sentry section failed: %s", exc)
        sections.append("## Sentry Errors\n\n_Failed to load — check JARVIS logs._\n")

    sections.append("")

    # ── PostHog ───────────────────────────────────────────────────────────────
    try:
        from app.services.posthog_service import PostHogService
        posthog = PostHogService()
        sections.append(posthog.format_briefing_section())
    except Exception as exc:
        LOGGER.warning("CEO ops health — PostHog section failed: %s", exc)
        sections.append("## PostHog Analytics\n\n_Failed to load — check JARVIS logs._\n")

    sections.append("")

    # ── Vercel ────────────────────────────────────────────────────────────────
    try:
        from app.services.vercel_service import VercelService
        vercel = VercelService()
        sections.append(vercel.format_briefing_section(hours=hours))
    except Exception as exc:
        LOGGER.warning("CEO ops health — Vercel section failed: %s", exc)
        sections.append("## Vercel Deployments\n\n_Failed to load — check JARVIS logs._\n")

    return "\n".join(sections)


def get_ops_summary_for_briefing(hours: int = 24) -> dict[str, Any]:
    """
    Return a structured dict of key ops metrics for programmatic use
    (e.g. deciding whether to send an alert vs. a routine briefing).

    Returns:
        {
            "sentry_new_critical": int,
            "sentry_new_issues": int,
            "posthog_total_dau": float,
            "vercel_failed_deployments": int,
            "has_alerts": bool,
        }
    """
    result: dict[str, Any] = {
        "sentry_new_critical": 0,
        "sentry_new_issues": 0,
        "posthog_total_dau": 0.0,
        "vercel_failed_deployments": 0,
        "has_alerts": False,
    }

    try:
        from app.services.sentry_service import SentryService
        sentry = SentryService()
        if sentry.is_enabled():
            new_issues = sentry.get_new_issues(hours=hours)
            result["sentry_new_issues"] = len(new_issues)
            result["sentry_new_critical"] = sum(
                1 for i in new_issues if i.get("level") in ("critical", "fatal")
            )
    except Exception as exc:
        LOGGER.warning("get_ops_summary — Sentry failed: %s", exc)

    try:
        from app.services.posthog_service import PostHogService
        posthog = PostHogService()
        if posthog.is_enabled():
            result["posthog_total_dau"] = posthog.get_total_dau()
    except Exception as exc:
        LOGGER.warning("get_ops_summary — PostHog failed: %s", exc)

    try:
        from app.services.vercel_service import VercelService
        vercel = VercelService()
        if vercel.is_enabled():
            failed = vercel.get_failed_deployments(hours=hours)
            result["vercel_failed_deployments"] = len(failed)
    except Exception as exc:
        LOGGER.warning("get_ops_summary — Vercel failed: %s", exc)

    result["has_alerts"] = (
        result["sentry_new_critical"] > 0
        or result["vercel_failed_deployments"] > 0
    )

    return result

