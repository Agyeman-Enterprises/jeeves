"""
Email service for Gmail and Outlook.
"""

import logging
import os
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)

# Gmail OAuth
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")

# Outlook OAuth
OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")
OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID", "common")


class EmailService:
    """Service for sending emails via Gmail or Outlook."""
    
    def __init__(self):
        self.gmail_available = False
        self.outlook_available = False
        self._setup_gmail()
        self._setup_outlook()
    
    def _setup_gmail(self):
        """Setup Gmail service."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request
            
            # Check if credentials exist
            creds_file = os.getenv("GMAIL_CREDENTIALS_FILE", "config/gmail_credentials.json")
            if os.path.exists(creds_file):
                self.gmail_available = True
                LOGGER.info("Gmail service available")
            else:
                LOGGER.warning("Gmail credentials not found. Set GMAIL_CREDENTIALS_FILE or configure OAuth")
        except ImportError:
            LOGGER.warning("Google API libraries not installed")
        except Exception as e:
            LOGGER.warning(f"Gmail setup error: {e}")
    
    def _setup_outlook(self):
        """Setup Outlook service."""
        try:
            import msal
            
            if OUTLOOK_CLIENT_ID and OUTLOOK_CLIENT_SECRET:
                self.outlook_available = True
                LOGGER.info("Outlook service available")
            else:
                LOGGER.warning("Outlook credentials not configured")
        except ImportError:
            LOGGER.warning("msal not installed")
        except Exception as e:
            LOGGER.warning(f"Outlook setup error: {e}")
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        provider: str = "gmail",  # "gmail" or "outlook"
        html: bool = False
    ) -> Dict[str, any]:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            provider: "gmail" or "outlook"
            html: Whether body is HTML
        
        Returns:
            Dict with success status
        """
        if provider == "gmail":
            return self._send_gmail(to, subject, body, html)
        elif provider == "outlook":
            return self._send_outlook(to, subject, body, html)
        else:
            return {
                "success": False,
                "error": f"Unknown provider: {provider}"
            }
    
    def _send_gmail(self, to: str, subject: str, body: str, html: bool) -> Dict[str, any]:
        """Send email via Gmail."""
        if not self.gmail_available:
            return {
                "success": False,
                "error": "Gmail not configured"
            }
        
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Load credentials
            creds_file = os.getenv("GMAIL_CREDENTIALS_FILE", "config/gmail_credentials.json")
            creds = Credentials.from_authorized_user_file(creds_file)
            
            # Refresh if needed
            if creds.expired:
                creds.refresh(Request())
            
            # Build service
            service = build('gmail', 'v1', credentials=creds)
            
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject
            
            if html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')
            message.attach(part)
            
            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            LOGGER.info(f"Gmail sent: {send_message['id']}")
            return {
                "success": True,
                "message_id": send_message['id']
            }
            
        except Exception as e:
            LOGGER.error(f"Failed to send Gmail: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _send_outlook(self, to: str, subject: str, body: str, html: bool) -> Dict[str, any]:
        """Send email via Outlook."""
        if not self.outlook_available:
            return {
                "success": False,
                "error": "Outlook not configured"
            }
        
        try:
            import msal
            import requests
            
            # Get access token (simplified - in production, use proper token management)
            app = msal.ConfidentialClientApplication(
                OUTLOOK_CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}",
                client_credential=OUTLOOK_CLIENT_SECRET
            )
            
            # This is a simplified flow - in production, handle token refresh properly
            token_cache_file = os.getenv("OUTLOOK_TOKEN_CACHE", "config/outlook_token_cache.json")
            # Token management would go here...
            
            # For now, return not implemented
            LOGGER.warning("Outlook email sending not fully implemented - requires token management")
            return {
                "success": False,
                "error": "Outlook email sending requires token management setup"
            }
            
        except Exception as e:
            LOGGER.error(f"Failed to send Outlook email: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
email_service = EmailService()

