from typing import Dict, Any, List, Optional
import logging
import uuid
from datetime import datetime

from app.models.database_models import JarvisDatabase

LOGGER = logging.getLogger(__name__)


class AlertsService:
    """
    Creates and evaluates portfolio alerts.
    """

    def __init__(self, database: JarvisDatabase = None):
        self.db = database or JarvisDatabase()

    async def create_alert(
        self,
        user_id: str,
        business_id: Optional[str],
        name: str,
        condition_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new alert."""
        import json
        
        alert_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        self.db.execute_raw_write(
            """
            INSERT INTO alerts (id, user_id, business_id, name, condition_json, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert_id,
                user_id,
                business_id,
                name,
                json.dumps(condition_json),
                1,  # is_active
                created_at,
            )
        )
        
        return {
            "id": alert_id,
            "user_id": user_id,
            "business_id": business_id,
            "name": name,
            "condition_json": condition_json,
            "is_active": True,
            "created_at": created_at,
        }

    async def get_active_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active alerts for a user."""
        import json
        
        rows = self.db.execute_raw(
            """
            SELECT * FROM alerts
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        
        alerts = []
        for row in rows:
            try:
                alerts.append({
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "business_id": row["business_id"],
                    "name": row["name"],
                    "condition_json": json.loads(row["condition_json"]),
                    "is_active": bool(row["is_active"]),
                    "created_at": row["created_at"],
                })
            except Exception as exc:
                LOGGER.warning("Failed to parse alert: %s", exc)
        
        return alerts

    async def record_event(self, alert_id: str, payload: Dict[str, Any]) -> None:
        """Record an alert event (when an alert is triggered)."""
        import json
        
        event_id = str(uuid.uuid4())
        triggered_at = datetime.utcnow().isoformat()
        
        self.db.execute_raw_write(
            """
            INSERT INTO alert_events (id, alert_id, triggered_at, payload)
            VALUES (?, ?, ?, ?)
            """,
            (
                event_id,
                alert_id,
                triggered_at,
                json.dumps(payload),
            )
        )

    async def get_recent_events(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent alert events for a user."""
        import json
        
        rows = self.db.execute_raw(
            """
            SELECT a.name, e.triggered_at, e.payload
            FROM alert_events e
            JOIN alerts a ON a.id = e.alert_id
            WHERE a.user_id = ?
            ORDER BY e.triggered_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        
        events = []
        for row in rows:
            try:
                events.append({
                    "alert_name": row["name"],
                    "triggered_at": row["triggered_at"],
                    "payload": json.loads(row["payload"]),
                })
            except Exception as exc:
                LOGGER.warning("Failed to parse alert event: %s", exc)
        
        return events

    async def deactivate_alert(self, alert_id: str, user_id: str) -> bool:
        """Deactivate an alert."""
        self.db.execute_raw_write(
            """
            UPDATE alerts
            SET is_active = 0
            WHERE id = ? AND user_id = ?
            """,
            (alert_id, user_id)
        )
        return True

