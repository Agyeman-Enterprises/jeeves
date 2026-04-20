"""
desktop_notify.py — Windows desktop toast notifications for JARVIS.

Uses plyer (already in requirements.txt) which calls Windows native
notification API. Falls back to Pushover if plyer unavailable.

Usage:
    from app.services.desktop_notify import notify
    notify("Reminder", "Have you eaten in the last few hours?")
    notify("Enterprise Alert", "3 urgent items", urgency="critical")
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Literal

LOGGER = logging.getLogger("backend.services.desktop_notify")

Urgency = Literal["low", "normal", "critical"]

# App name shown in Windows notification centre
_APP_NAME = "JARVIS"
_ICON_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "icon-192.png")


def notify(
    title: str,
    message: str,
    urgency: Urgency = "normal",
    timeout: int = 10,
) -> bool:
    """
    Show a Windows desktop toast notification.

    Returns True if the notification was shown, False if it failed.
    Failure is always silent — JARVIS never crashes because a toast failed.
    """
    # Truncate to Windows limits
    title = title[:64]
    message = message[:256]

    # ── Method 1: plyer (cross-platform, preferred) ──────────────────────
    try:
        from plyer import notification  # type: ignore
        icon = _ICON_PATH if os.path.exists(_ICON_PATH) else None
        notification.notify(
            title=title,
            message=message,
            app_name=_APP_NAME,
            app_icon=icon,
            timeout=timeout,
            toast=True,  # Windows Action Center toast
        )
        LOGGER.debug("[Notify] Toast sent: %s", title)
        return True
    except Exception as exc:
        LOGGER.debug("[Notify] plyer failed (%s), trying PowerShell", exc)

    # ── Method 2: PowerShell BurntToast fallback ─────────────────────────
    try:
        ps_script = (
            "[Windows.UI.Notifications.ToastNotificationManager, "
            "Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
            "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, "
            "ContentType = WindowsRuntime] | Out-Null; "
            f"$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
            f'$xml.LoadXml(\'<toast><visual><binding template="ToastGeneric">'
            f"<text>{_ps_escape(title)}</text>"
            f"<text>{_ps_escape(message)}</text>"
            f"</binding></visual></toast>'); "
            f'$toast = New-Object Windows.UI.Notifications.ToastNotification $xml; '
            f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{_APP_NAME}").Show($toast)'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
            timeout=8,
            capture_output=True,
            creationflags=0x08000000 if sys.platform == "win32" else 0,
        )
        LOGGER.debug("[Notify] PowerShell toast sent: %s", title)
        return True
    except Exception as exc:
        LOGGER.warning("[Notify] PowerShell fallback failed: %s", exc)

    return False


def _ps_escape(s: str) -> str:
    """Escape special chars for inline PowerShell XML string."""
    return s.replace("'", "''").replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")


# ── Convenience wrappers ──────────────────────────────────────────────────────

def notify_reminder(message: str) -> None:
    notify("JARVIS Reminder", message, urgency="normal", timeout=15)


def notify_alert(title: str, message: str) -> None:
    notify(f"⚠ {title}", message, urgency="critical", timeout=20)


def notify_briefing(summary: str) -> None:
    notify("JARVIS Morning Briefing", summary[:200], urgency="normal", timeout=30)


def notify_enterprise(alert_count: int, summary: str) -> None:
    title = f"Enterprise — {alert_count} alert{'s' if alert_count != 1 else ''}" if alert_count else "Enterprise Briefing"
    notify(title, summary[:200], urgency="critical" if alert_count else "normal", timeout=20)
