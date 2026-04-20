"""
Finance fallback service for banks not supported by Plaid.
Handles Bank of Guam, Bank of Hawaii, and other unsupported banks.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)

UNSUPPORTED_BANKS = os.getenv("UNSUPPORTED_BANKS", "Bank of Guam,Bank of Hawaii").split(",")
UNSUPPORTED_BANKS = [b.strip() for b in UNSUPPORTED_BANKS if b.strip()]


class FinanceFallbackService:
    """Service for handling banks not supported by Plaid."""
    
    def __init__(self):
        self.unsupported_banks = UNSUPPORTED_BANKS
        LOGGER.info(f"Finance fallback service initialized. Unsupported banks: {self.unsupported_banks}")
    
    def is_unsupported(self, bank_name: str) -> bool:
        """Check if a bank is in the unsupported list."""
        bank_lower = bank_name.lower()
        return any(unsupported.lower() in bank_lower or bank_lower in unsupported.lower() 
                   for unsupported in self.unsupported_banks)
    
    def create_bill_reminder(
        self,
        bank_name: str,
        bill_name: str,
        amount: float,
        due_date: str,
        pay_url: Optional[str] = None,
        account_number: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Create a bill reminder for manual payment.
        
        Args:
            bank_name: Name of the bank
            bill_name: Name of the bill
            amount: Amount due
            due_date: Due date (ISO format or YYYY-MM-DD)
            pay_url: Optional payment URL
            account_number: Optional account number (last 4 digits)
        
        Returns:
            Dict with reminder details
        """
        reminder = {
            "bank": bank_name,
            "bill": bill_name,
            "amount": amount,
            "due_date": due_date,
            "pay_url": pay_url,
            "account_number": account_number,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "requires_manual_payment": True
        }
        
        LOGGER.info(f"Created bill reminder: {bill_name} - ${amount} due {due_date}")
        return reminder
    
    def generate_payment_instructions(self, reminder: Dict[str, any]) -> str:
        """
        Generate human-readable payment instructions.
        
        Args:
            reminder: Reminder dict from create_bill_reminder
        
        Returns:
            Formatted instructions string
        """
        instructions = f"""
Payment Required: {reminder['bill']}
Amount: ${reminder['amount']:.2f}
Due Date: {reminder['due_date']}
Bank: {reminder['bank']}
"""
        
        if reminder.get('pay_url'):
            instructions += f"\nPay online: {reminder['pay_url']}"
        
        if reminder.get('account_number'):
            instructions += f"\nAccount: ****{reminder['account_number']}"
        
        instructions += "\n\nThis payment requires manual action as the bank is not supported by Plaid."
        
        return instructions.strip()
    
    def mark_as_paid(self, reminder: Dict[str, any]) -> Dict[str, any]:
        """Mark a reminder as paid."""
        reminder["status"] = "paid"
        reminder["paid_at"] = datetime.now().isoformat()
        LOGGER.info(f"Marked bill as paid: {reminder['bill']}")
        return reminder


# Global instance
finance_fallback_service = FinanceFallbackService()

