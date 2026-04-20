"""
Pushover service for push notifications to all devices.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

# Configuration from environment
API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
USER_KEY = os.getenv("PUSHOVER_USER_KEY")

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

# Priority levels
PRIORITY_LOWEST = -2
PRIORITY_LOW = -1
PRIORITY_NORMAL = 0
PRIORITY_HIGH = 1
PRIORITY_EMERGENCY = 2


class PushoverService:
    """Service for Pushover push notifications."""

    def __init__(self) -> None:
        self.is_configured = bool(API_TOKEN and USER_KEY)
        if not self.is_configured:
            LOGGER.warning(
                "Pushover not configured. Set PUSHOVER_API_TOKEN and PUSHOVER_USER_KEY"
            )
        else:
            LOGGER.info("Pushover service configured")

    def send_notification(
        self,
        title: str,
        message: str,
        priority: int = PRIORITY_NORMAL,
        url: Optional[str] = None,
        url_title: Optional[str] = None,
        sound: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a push notification via Pushover.

        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (-2 to 2)
            url: Optional URL to include
            url_title: Optional title for the URL
            sound: Optional sound to play

        Returns:
            Dict with success status and request ID or error
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Pushover not configured. Set PUSHOVER_API_TOKEN and PUSHOVER_USER_KEY",
            }

        payload = {
            "token": API_TOKEN,
            "user": USER_KEY,
            "title": title,
            "message": message,
            "priority": priority,
        }

        if url:
            payload["url"] = url
        if url_title:
            payload["url_title"] = url_title
        if sound:
            payload["sound"] = sound

        try:
            response = requests.post(PUSHOVER_API_URL, data=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == 1:
                LOGGER.info("Pushover notification sent: %s", title)
                return {
                    "success": True,
                    "request_id": data.get("request"),
                }
            else:
                error = data.get("errors", ["Unknown error"])
                LOGGER.error("Pushover API error: %s", error)
                return {
                    "success": False,
                    "error": ", ".join(error) if isinstance(error, list) else str(error),
                }
        except requests.exceptions.RequestException as exc:
            LOGGER.error("Failed to send Pushover notification: %s", exc)
            return {
                "success": False,
                "error": str(exc),
            }

    def send_critical(self, title: str, message: str) -> Dict[str, Any]:
        """
        Send a critical priority notification (high priority, persistent).

        Args:
            title: Notification title
            message: Notification message

        Returns:
            Dict with success status and request ID or error
        """
        return self.send_notification(
            title=title,
            message=message,
            priority=PRIORITY_HIGH,
            sound="persistent",
        )

    def send_emergency(self, title: str, message: str) -> Dict[str, Any]:
        """
        Send an emergency priority notification (requires acknowledgment).

        Args:
            title: Notification title
            message: Notification message

        Returns:
            Dict with success status and request ID or error
        """
        return self.send_notification(
            title=title,
            message=message,
            priority=PRIORITY_EMERGENCY,
            sound="persistent",
        )

    def is_configured(self) -> bool:
        """Check if Pushover is properly configured."""
        return self.is_configured


# Singleton instance
pushover_service = PushoverService()
