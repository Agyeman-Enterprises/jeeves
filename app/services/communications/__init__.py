"""Communications service modules for JARVIS.

Includes:
- CommunicationsHub: Unified gateway (Ghexit → Twilio/Resend fallback)
- TwilioService: Direct Twilio SMS/WhatsApp/Voice
- PushoverService: Push notifications
- GhexitService: Unified comms via Ghexit backend
- EmailService: Gmail/Outlook email
"""

from .hub import CommunicationsHub, communications_hub
from .twilio_service import TwilioService, twilio_service
from .pushover_service import PushoverService, pushover_service
from .ghexit_service import GhexitService, ghexit_service
from .email_service import EmailService, email_service

__all__ = [
    # Unified Hub (preferred interface)
    "CommunicationsHub",
    "communications_hub",
    # Individual services
    "TwilioService",
    "twilio_service",
    "PushoverService",
    "pushover_service",
    "GhexitService",
    "ghexit_service",
    "EmailService",
    "email_service",
]
