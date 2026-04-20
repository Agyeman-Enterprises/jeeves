from typing import Dict, Any, List
import logging
from pathlib import Path
import yaml

from app.models.database_models import JarvisDatabase

LOGGER = logging.getLogger(__name__)


class PortfolioService:
    """
    Aggregates KPIs across all businesses for a given user.
    """

    def __init__(self, database: JarvisDatabase = None):
        self.db = database or JarvisDatabase()
        self.business_config_path = Path("config") / "businesses.yaml"

    def _load_businesses(self) -> List[Dict[str, Any]]:
        """Load businesses from config file."""
        if not self.business_config_path.exists():
            LOGGER.warning("Businesses config file not found: %s", self.business_config_path)
            return []

        try:
            with open(self.business_config_path, "r") as f:
                config = yaml.safe_load(f)
            
            businesses = []
            for category, biz_list in config.get("businesses", {}).items():
                for biz in biz_list:
                    businesses.append({
                        "name": biz.get("name", ""),
                        "category": category,
                        "state": biz.get("state", ""),
                        "entity": biz.get("entity", ""),
                        "ein": biz.get("ein", ""),
                    })
            return businesses
        except Exception as exc:
            LOGGER.error("Failed to load businesses config: %s", exc)
            return []

    async def get_portfolio_overview(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get portfolio overview across all businesses.
        For each business, pull latest KPIs if available.
        """
        businesses = self._load_businesses()

        # For each business, try to get KPIs from database
        result = []
        for biz in businesses:
            business_id = biz["name"].lower().replace(" ", "_")
            
            # Try to fetch KPIs for this business
            kpis = []
            try:
                rows = self.db.execute_raw(
                    """
                    SELECT payload FROM kpis
                    WHERE id LIKE ?
                    ORDER BY updated_at DESC
                    LIMIT 20
                    """,
                    (f"{business_id}%",)
                )
                for row in rows:
                    try:
                        kpi_data = self.db.encryption.decrypt(row["payload"])
                        kpis.append(kpi_data)
                    except Exception:
                        pass
            except Exception as exc:
                LOGGER.debug("No KPIs found for business %s: %s", biz["name"], exc)

            result.append({
                "business_id": business_id,
                "business_name": biz["name"],
                "category": biz["category"],
                "state": biz["state"],
                "entity": biz["entity"],
                "kpis": kpis,
            })

        return {
            "businesses": result,
            "total_businesses": len(result),
        }

    async def get_business_kpis(self, business_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get KPIs for a specific business."""
        business_id = business_name.lower().replace(" ", "_")
        
        try:
            rows = self.db.execute_raw(
                """
                SELECT payload FROM kpis
                WHERE id LIKE ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (f"{business_id}%", limit)
            )
            kpis = []
            for row in rows:
                try:
                    kpi_data = self.db.encryption.decrypt(row["payload"])
                    kpis.append(kpi_data)
                except Exception:
                    pass
            return kpis
        except Exception as exc:
            LOGGER.error("Failed to fetch KPIs for %s: %s", business_name, exc)
            return []

