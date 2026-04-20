"""Email service modules for Gmail and Outlook integration."""

from .gmail_service import GmailService, gmail_service
from .outlook_service import OutlookService, outlook_service

__all__ = ["GmailService", "gmail_service", "OutlookService", "outlook_service"]

