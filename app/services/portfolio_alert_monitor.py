"""
Portfolio Alert Monitor - Background task that polls NEXUS for alerts.
When critical alerts appear, it:
- Plays spoken alert via TTS
- Sends Pushover notification
- Logs to console
"""

import logging
import asyncio
from typing import Optional, Set, Dict, Any
from datetime import datetime

from app.services.nexus_service import NexusService, NexusServiceError
from app.services.voice_service import VoiceService
from app.services.communications.pushover_service import PushoverService

LOGGER = logging.getLogger(__name__)


class PortfolioAlertMonitor:
    """
    Monitors NEXUS for portfolio alerts and notifies user when critical alerts appear.
    """

    def __init__(
        self,
        nexus_service: Optional[NexusService] = None,
        voice_service: Optional[VoiceService] = None,
        poll_interval_seconds: int = 300,  # 5 minutes
    ):
        self.nexus = nexus_service or NexusService()
        self.voice = voice_service or VoiceService()
        self.poll_interval = poll_interval_seconds
        self.seen_alert_ids: Set[str] = set()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the alert monitoring loop."""
        if self.is_running:
            LOGGER.warning("PortfolioAlertMonitor is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        LOGGER.info("PortfolioAlertMonitor started (polling every %d seconds)", self.poll_interval)

    async def stop(self) -> None:
        """Stop the alert monitoring loop."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        LOGGER.info("PortfolioAlertMonitor stopped")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_running:
            try:
                await self._check_alerts()
            except Exception as exc:
                LOGGER.exception("Error in alert monitor loop: %s", exc)

            # Wait before next poll
            try:
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break

    async def _check_alerts(self) -> None:
        """Check for new alerts from NEXUS."""
        try:
            alerts = await self.nexus.get_alerts(active_only=True)
            
            # Filter for new alerts
            new_alerts = []
            for alert in alerts:
                alert_id = alert.get("id") or alert.get("name", "")
                if alert_id and alert_id not in self.seen_alert_ids:
                    new_alerts.append(alert)
                    self.seen_alert_ids.add(alert_id)

            if new_alerts:
                LOGGER.info("Found %d new alerts", len(new_alerts))
                for alert in new_alerts:
                    await self._handle_new_alert(alert)

        except NexusServiceError as exc:
            LOGGER.debug("NEXUS unavailable for alert check: %s", exc)
        except Exception as exc:
            LOGGER.exception("Error checking alerts: %s", exc)

    async def _handle_new_alert(self, alert: Dict[str, Any]) -> None:
        """Handle a new alert - speak, notify, log."""
        alert_name = alert.get("name", "Unknown Alert")
        alert_message = f"Portfolio alert: {alert_name}"

        # Log to console
        LOGGER.warning("🚨 %s", alert_message)

        # Speak alert (if voice service available)
        try:
            await self.voice.synthesize(alert_message)
        except Exception as exc:
            LOGGER.warning("Failed to speak alert: %s", exc)

        # Send Pushover notification
        try:
            pushover = PushoverService()
            pushover.send_notification(
                title="Portfolio Alert",
                message=alert_message,
                priority=1,  # High priority
            )
        except Exception as exc:
            LOGGER.warning("Failed to send Pushover notification: %s", exc)

