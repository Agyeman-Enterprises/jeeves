"""
Enterprise Operations Analyzer
Analyzes operational complexity and identifies bottlenecks across workspaces.
"""

from typing import Dict, List, Any

from app.core.enterprise_graph import EnterpriseGraph


class EnterpriseOpsAnalyzer:
    """Analyzes operational aspects of the enterprise structure."""

    def __init__(self):
        self.graph = EnterpriseGraph()

    def workspace_complexity_score(self, ws: Dict[str, Any]) -> int:
        """
        Compute a simple complexity score for a workspace.
        More companies + more modules = higher ops load.
        """
        companies = self.graph.companies_by_workspace.get(ws["id"], [])
        modules = self.graph.modules_by_workspace.get(ws["id"], [])
        return len(companies) * 2 + len(modules)

    def analyze_workspace_ops(self) -> List[Dict[str, Any]]:
        """Analyze operational complexity for all workspaces."""
        results = []
        for ws in self.graph.workspaces:
            score = self.workspace_complexity_score(ws)
            results.append({
                "workspace": ws.get("name", "Unknown"),
                "workspace_slug": ws.get("slug"),
                "score": score,
                "companies": [
                    {"name": c.get("name", "Unknown"), "id": c.get("id")}
                    for c in self.graph.companies_by_workspace.get(ws["id"], [])
                ],
                "modules": [
                    {"name": m.get("name", "Unknown"), "id": m.get("id")}
                    for m in self.graph.modules_by_workspace.get(ws["id"], [])
                ],
            })
        return sorted(results, key=lambda x: x["score"], reverse=True)

    def find_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify workspaces with high operational complexity (bottlenecks)."""
        ops = self.analyze_workspace_ops()
        if not ops:
            return []
        threshold = max(x["score"] for x in ops) * 0.7
        return [x for x in ops if x["score"] >= threshold]

    def ops_summary(self) -> Dict[str, Any]:
        """Return a comprehensive operations summary."""
        return {
            "workspace_ops_ranking": self.analyze_workspace_ops(),
            "bottlenecks": self.find_bottlenecks(),
            "total_workspaces": len(self.graph.workspaces),
            "total_companies": len(self.graph.companies),
            "total_modules": len(self.graph.modules),
        }

