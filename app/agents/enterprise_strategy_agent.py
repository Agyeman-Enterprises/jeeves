"""
Enterprise Strategy Agent
Combines ops and finance analysis for strategic CEO recommendations.
"""

from pathlib import Path
from typing import Optional, Any

from app.agents.enterprise_ops_analyzer import EnterpriseOpsAnalyzer
from app.agents.enterprise_finance_analyzer import EnterpriseFinanceAnalyzer


def build_strategy_context() -> dict:
    """Build combined ops and finance context for strategic analysis."""
    ops = EnterpriseOpsAnalyzer()
    fin = EnterpriseFinanceAnalyzer()
    return {
        "ops": ops.ops_summary(),
        "finance": fin.financial_summary(),
    }


def answer_strategy_question(
    question: str,
    ollama_service: Optional[Any] = None,
) -> str:
    """
    Answer a strategic question using combined ops and finance analysis.
    
    Args:
        question: The strategic question to answer
        ollama_service: Optional OllamaService instance for LLM calls
    
    Returns:
        Generated strategic recommendation
    """
    try:
        ctx = build_strategy_context()
    except Exception as e:
        return f"Error building strategy context: {e}"

    ctx_text = f"""
Operations Analysis:
{ctx['ops']}

Financial Analysis:
{ctx['finance']}
"""

    # Load CEO system prompt
    prompt_path = Path("backend/ai/prompts/ceo_system_prompt.md")
    if prompt_path.exists():
        system_prompt = prompt_path.read_text(encoding="utf-8")
    else:
        system_prompt = "You are Jarvis, the AI CEO for Agyeman Enterprises."

    # Use OllamaService if provided, otherwise return fallback
    if ollama_service is None:
        return (
            "LLM strategy agent not fully wired yet.\n\n"
            "Here is your current enterprise analysis:\n\n"
            f"{ctx_text}\n\n"
            f"Original question: {question}"
        )

    try:
        user_prompt = (
            f"Enterprise Ops+Finance Context:\n{ctx_text}\n\n"
            f"Question: {question}\n\n"
            "Provide a CEO strategic recommendation."
        )

        response = ollama_service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        return response if isinstance(response, str) else str(response)

    except Exception as e:
        return (
            f"Error generating strategy response: {e}\n\n"
            "Here is your current enterprise analysis:\n\n"
            f"{ctx_text}\n\n"
            f"Original question: {question}"
        )

