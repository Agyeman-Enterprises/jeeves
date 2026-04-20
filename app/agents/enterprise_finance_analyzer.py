"""
Enterprise Finance Analyzer
Analyzes financial aspects including revenue potential, cost complexity, and risk levels.
"""

from typing import Dict, List, Any

from app.core.enterprise_graph import EnterpriseGraph


class EnterpriseFinanceAnalyzer:
    """Analyzes financial aspects of the enterprise structure."""

    def __init__(self):
        self.graph = EnterpriseGraph()

    def compute_revenue_potential(self, ws: Dict[str, Any]) -> int:
        """
        Compute revenue potential score for a workspace.
        Heuristic: number of modules * industry multiplier.
        """
        companies = self.graph.companies_by_workspace.get(ws["id"], [])
        modules = self.graph.modules_by_workspace.get(ws["id"], [])
        base = len(modules) * 3 + len(companies)
        return base

    def compute_cost_complexity(self, ws: Dict[str, Any]) -> int:
        """
        Compute cost complexity score for a workspace.
        More companies & modules = higher cost base.
        """
        comp = len(self.graph.companies_by_workspace.get(ws["id"], []))
        mod = len(self.graph.modules_by_workspace.get(ws["id"], []))
        return comp + mod * 2

    def compute_risk_levels(self, ws: Dict[str, Any]) -> str:
        """
        Compute risk level for a workspace based on industry/domain.
        """
        name = ws.get("name", "").lower()
        slug = ws.get("slug", "").lower()
        combined = f"{name} {slug}"

        if "health" in combined:
            return "high"
        if "crypto" in combined or "gaming" in combined:
            return "medium-high"
        if "engineering" in combined or "manufacturing" in combined:
            return "medium"
        if "finance" in combined:
            return "medium"
        return "low-medium"

    def financial_summary(self) -> List[Dict[str, Any]]:
        """Return a comprehensive financial summary for all workspaces."""
        summary = []
        for ws in self.graph.workspaces:
            summary.append({
                "workspace": ws.get("name", "Unknown"),
                "workspace_slug": ws.get("slug"),
                "revenue_potential": self.compute_revenue_potential(ws),
                "cost_complexity": self.compute_cost_complexity(ws),
                "risk": self.compute_risk_levels(ws),
                "company_count": len(self.graph.companies_by_workspace.get(ws["id"], [])),
                "module_count": len(self.graph.modules_by_workspace.get(ws["id"], [])),
            })
        return summary

