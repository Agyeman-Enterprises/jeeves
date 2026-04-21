from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from app.agents.base import AgentResponse, BaseAgent

try:
    from app.finance.fie_core import FinancialIntelligenceEngine, Transaction as FIETransaction
    from app.finance.fie_autobudget import AutoBudgetEngine
    from app.finance.fie_autopay import AutopayPlanner, Bill, Payday
    from app.services.plaid_service import PlaidService
    from app.services.stripe_service import StripeService
    from app.services.square_service import SquareService
    from app.services.subscription_detector import SubscriptionDetector, Subscription
    _FINANCE_AVAILABLE = True
except ImportError:
    _FINANCE_AVAILABLE = False

LOGGER = logging.getLogger(__name__)


@dataclass
class AccountSnapshot:
    """Represents a snapshot of an account balance at a point in time."""
    name: str
    balance: float
    institution: Optional[str] = None
    account_type: Optional[str] = None
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "balance": self.balance,
            "institution": self.institution,
            "account_type": self.account_type,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class FinanceAgent(BaseAgent):
    """Central brain for balances, cashflow, subscriptions, goals, and safety thresholds."""

    name = "FinanceAgent"
    description = "Manages financial accounts, transactions, subscriptions, goals, and safety thresholds."
    capabilities = [
        "Account balance tracking",
        "Cashflow analysis",
        "Subscription management",
        "Goal tracking (retirement, land, etc.)",
        "Safety threshold monitoring",
        "Business expense suggestions",
    ]

    def __init__(self, base_path: Optional[Path] = None) -> None:
        super().__init__()
        self.base_path = Path(base_path) if base_path else Path(".").resolve()
        self.data_dir = self.base_path / "data"
        self.finance_dir = self.data_dir / "finance"
        self.config_path = self.base_path / "config" / "finance_config.yaml"
        self.sample_path = self.finance_dir / "sample_finance.json"

        # External services
        self.plaid = PlaidService()
        self.stripe = StripeService()
        self.square = SquareService()
        self.subscription_detector = SubscriptionDetector()

        # Ensure finance directory exists
        self.finance_dir.mkdir(parents=True, exist_ok=True)
        (self.finance_dir / "subscriptions").mkdir(parents=True, exist_ok=True)

    def supports(self, query: str) -> bool:
        keywords = [
            "balance",
            "account",
            "cashflow",
            "spending",
            "subscription",
            "finance",
            "financial",
            "money",
            "budget",
            "goal",
            "retirement",
            "safety",
            "threshold",
            "7676",
            "bog",
            "bank",
            "failed payment",
            "bill",
            "license",
            "certification",
            "due",
        ]
        return any(keyword in query.lower() for keyword in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        ctx = context or {}
        q = query.lower().strip()

        config = self._load_config()

        # Dashboard-specific queries
        if any(k in q for k in ("failed payment", "payment fail", "failed transaction")):
            return self._handle_failed_payments()
        
        if any(k in q for k in ("bill due", "bills due", "upcoming bill", "due soon")):
            return self._handle_upcoming_bills()
        
        if any(k in q for k in ("license expir", "certification expir", "dea expir")):
            return self._handle_license_status()

        if any(k in q for k in ("snapshot", "overview", "summary", "how am i doing", "state of my finances")):
            return self._handle_overview_fie(q, config)

        if any(k in q for k in ("forecast", "cashflow", "runway", "projection")):
            return self._handle_forecast(q, config)

        if any(k in q for k in ("save money", "cut costs", "cut spending", "refinance", "savings opportunities")):
            return self._handle_savings_opportunities_fie(q, config)

        if any(k in q for k in ("budget", "autobudget", "allocate", "how should i divide")):
            return self._handle_budget(q, config)

        if any(k in q for k in ("autopay", "bill calendar", "bills calendar", "pay my bills")):
            return self._handle_autopay(q, config)

        if any(k in q for k in ("subscription", "subscriptions", "ai subscriptions", "cancel subscriptions")):
            return self._handle_subscriptions_fie(q, config)

        # Legacy handlers for backward compatibility
        if "save money" in q or "savings" in q or "save" in q:
            return self._handle_savings_opportunities()
        elif "refinance" in q or "loan" in q:
            return self._handle_savings_opportunities()
        elif "fee" in q and ("month" in q or "recent" in q):
            return self._handle_savings_opportunities()
        elif "subscription" in q and ("cancel" in q or "should" in q):
            return self._handle_savings_opportunities()
        elif "spending" in q or "cashflow" in q:
            return self._summarize_recent_spending()
        elif "goal" in q:
            return self._handle_goals()
        elif "balance" in q or "account" in q or "overview" in q:
            return self._handle_overview()
        else:
            return self._handle_overview_fie(q, config)

    def _load_config(self) -> Dict[str, Any]:
        """Load finance configuration from YAML."""
        return self._load_config_safe()

    def _load_config_safe(self) -> Dict[str, Any]:
        """Load finance configuration from YAML (safe version)."""
        if not self.config_path.exists():
            LOGGER.warning("finance_config.yaml not found at %s", self.config_path)
            return {}
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as exc:
            LOGGER.exception("Failed to load finance_config.yaml: %s", exc)
            return {}

    def _load_sample_finance(self) -> Dict[str, Any]:
        """Load sample finance data from JSON."""
        if not self.sample_path.exists():
            return {"accounts": [], "transactions": [], "subscriptions": [], "bills": []}
        try:
            with self.sample_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            LOGGER.exception("Failed to load sample_finance.json: %s", exc)
            return {"accounts": [], "transactions": [], "subscriptions": [], "bills": []}

    def _load_accounts_and_transactions(self) -> Dict[str, Any]:
        """
        Load accounts and transactions from multiple sources.
        For now: load from sample_finance.json.
        Cursor can later:
        - merge Plaid/bank CSV/Excel/PayPal data
        - merge email-derived subscriptions
        """
        data = self._load_sample_finance()

        # Try to merge Plaid data if available
        if self.plaid.is_enabled():
            try:
                plaid_accounts = self.plaid.fetch_accounts()
                plaid_transactions = self.plaid.fetch_recent_transactions(days=90)

                # Merge accounts
                existing_account_names = {a.get("name") for a in data.get("accounts", [])}
                for acc in plaid_accounts:
                    if acc.get("name") not in existing_account_names:
                        data.setdefault("accounts", []).append({
                            "name": acc.get("name", "PlaidAccount"),
                            "balance": acc.get("balance", {}).get("available", 0.0),
                        })

                # Merge transactions
                for txn in plaid_transactions:
                    data.setdefault("transactions", []).append({
                        "date": txn.get("date", ""),
                        "amount": txn.get("amount", 0.0),
                        "description": txn.get("description", ""),
                        "account_name": txn.get("account_id", "Account"),
                        "category": txn.get("category", ""),
                    })
            except Exception as exc:
                LOGGER.warning("Failed to merge Plaid data: %s", exc)

        return data

    def _load_account_snapshots(self) -> List[AccountSnapshot]:
        """Load account balances from Plaid (if available) or CSV/XLS fallback."""
        snapshots: List[AccountSnapshot] = []

        # 1) Try Plaid first
        if self.plaid.is_enabled():
            try:
                plaid_accounts = self.plaid.fetch_accounts()
                for acc in plaid_accounts:
                    snapshots.append(
                        AccountSnapshot(
                            name=acc.get("name") or acc.get("official_name") or "PlaidAccount",
                            balance=float(acc.get("balance", {}).get("available", 0.0)),
                            institution=acc.get("institution", "Unknown"),
                            account_type=acc.get("subtype", "unknown"),
                            last_updated=datetime.now(),
                        )
                    )
            except Exception as exc:
                LOGGER.warning("Failed to fetch accounts from Plaid: %s", exc)

        # 2) Fallback to CSV/XLS for unsupported banks (Bank of Guam, MVFCU, etc.)
        # TODO: Implement CSV/XLS parsing for manual account imports
        # For now, if Plaid is not enabled or returns no accounts, return empty list

        return snapshots

    def _handle_overview(self) -> AgentResponse:
        """Generate financial overview with balances and safety thresholds."""
        config = self._load_config()
        snapshots = self._load_account_snapshots()

        content_lines: List[str] = []
        data: Dict[str, Any] = {
            "snapshots": [s.to_dict() for s in snapshots],
            "total_balance": sum(s.balance for s in snapshots),
        }

        if not snapshots:
            content_lines.append("No account data available yet.")
            content_lines.append("\nTo connect accounts:")
            content_lines.append("1. Set up Plaid API keys in config/.env")
            content_lines.append("2. Link supported banks via Plaid")
            content_lines.append("3. For unsupported banks (Bank of Guam, MVFCU), use CSV/PDF import")
            return AgentResponse(
                agent=self.name,
                content="\n".join(content_lines),
                data=data,
                status="warning",
                warnings=["no_accounts_configured"],
            )

        # Calculate totals
        total_balance = sum(s.balance for s in snapshots)
        content_lines.append(f"Total Balance Across All Accounts: ${total_balance:,.2f}")
        content_lines.append("")

        # List accounts
        content_lines.append("Account Balances:")
        for snapshot in sorted(snapshots, key=lambda x: x.balance, reverse=True):
            content_lines.append(f"  {snapshot.name}: ${snapshot.balance:,.2f}")
            if snapshot.institution:
                content_lines.append(f"    ({snapshot.institution})")

        # Safety threshold check for primary salary account (7676)
        cfg_safety = config.get("safety_reserve", {})
        primary_account_name = config.get("primary_salary_account", "personal_bog_7676")
        min_balance = float(cfg_safety.get("minimum_balance", 0.0))
        alert_threshold = float(cfg_safety.get("alert_threshold", 0.0))

        primary_snapshot = next(
            (a for a in snapshots if a.name == primary_account_name or primary_account_name in a.name),
            None,
        )

        if primary_snapshot:
            content_lines.append("")
            content_lines.append(f"Primary salary account ({primary_snapshot.name}) balance: ${primary_snapshot.balance:,.2f}")

            if primary_snapshot.balance < min_balance:
                content_lines.append(
                    "⚠️ Warning: Your primary salary account is below the minimum safety reserve. "
                    "We should slow non-essential spending."
                )
                data["safety_warning"] = "below_minimum"
            elif primary_snapshot.balance < alert_threshold:
                content_lines.append(
                    "⚠️ Note: Your primary salary account is approaching the safety threshold."
                )
                data["safety_warning"] = "approaching_threshold"

        return AgentResponse(
            agent=self.name,
            content="\n".join(content_lines),
            data=data,
            status="success",
        )

    def _summarize_recent_spending(self) -> AgentResponse:
        """Summarize recent spending with business expense suggestions."""
        content_lines: List[str] = []
        data: Dict[str, Any] = {}

        # 1) Try Plaid transactions first
        transactions: List[Dict[str, Any]] = []
        if self.plaid.is_enabled():
            try:
                transactions = self.plaid.fetch_recent_transactions(days=30)
            except Exception as exc:
                LOGGER.warning("Failed to fetch transactions from Plaid: %s", exc)

        # 2) Fallback to CSV/XLS parsing (TODO: implement)

        if not transactions:
            content_lines.append("No transaction data available yet.")
            return AgentResponse(
                agent=self.name,
                content="\n".join(content_lines),
                data=data,
                status="warning",
                warnings=["no_transactions_available"],
            )

        # Calculate monthly spending
        monthly_spend = sum(abs(t.get("amount", 0)) for t in transactions if t.get("amount", 0) < 0)
        content_lines.append(f"Monthly Spending (Last 30 Days): ${monthly_spend:,.2f}")
        content_lines.append("")

        # Top categories
        categories = [t.get("category", "Uncategorized") for t in transactions if t.get("category")]
        category_counts = Counter(categories)
        if category_counts:
            content_lines.append("Top Spending Categories:")
            for category, count in category_counts.most_common(5):
                category_total = sum(
                    abs(t.get("amount", 0))
                    for t in transactions
                    if t.get("category") == category and t.get("amount", 0) < 0
                )
                content_lines.append(f"  {category}: ${category_total:,.2f} ({count} transactions)")

        # Identify suspected business expenses (ask, don't auto-tag)
        suspected_business = self._identify_suspected_business_expenses(transactions)
        if suspected_business:
            content_lines.append("")
            content_lines.append("⚠️ Suspected Business Expenses (needs your review):")
            for expense in suspected_business[:10]:  # Show top 10
                content_lines.append(
                    f"  {expense['merchant']}: ${abs(expense['amount']):,.2f} on {expense['date']}"
                )
            data["suspected_business_expenses"] = suspected_business
            data["needs_user_review"] = True

        data["monthly_spend"] = monthly_spend
        data["categories"] = dict(category_counts)
        data["transaction_count"] = len(transactions)

        return AgentResponse(
            agent=self.name,
            content="\n".join(content_lines),
            data=data,
            status="success",
        )

    def _identify_suspected_business_expenses(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify transactions that might be business-related (requires user confirmation)."""
        business_keywords = [
            "alibaba",
            "twilio",
            "hosting",
            "aws",
            "azure",
            "google cloud",
            "domain",
            "ssl",
            "server",
            "vps",
            "office",
            "supplies",
            "equipment",
            "software",
            "saas",
            "api",
            "stripe",
            "square",
            "payment processing",
        ]

        suspected = []
        for txn in transactions:
            merchant = (txn.get("merchant") or txn.get("name") or "").lower()
            description = (txn.get("description") or "").lower()
            combined = f"{merchant} {description}"

            if any(keyword in combined for keyword in business_keywords):
                suspected.append(
                    {
                        "merchant": txn.get("merchant") or txn.get("name", "Unknown"),
                        "amount": txn.get("amount", 0),
                        "date": txn.get("date", ""),
                        "description": txn.get("description", ""),
                        "transaction_id": txn.get("transaction_id", ""),
                        "needs_user_review": True,
                    }
                )

        return suspected

    def _handle_subscriptions(self) -> AgentResponse:
        """List and categorize subscriptions (AI, Apple, Education, etc.)."""
        content_lines: List[str] = []
        data: Dict[str, Any] = {}

        # Load subscriptions from email scan
        subscriptions_file = self.finance_dir / "subscriptions" / "email_subscriptions.json"
        subscriptions: List[Subscription] = []

        if subscriptions_file.exists():
            try:
                with open(subscriptions_file, "r", encoding="utf-8") as f:
                    subs_data = json.load(f)
                    for sub_dict in subs_data:
                        # Convert dict back to Subscription
                        subscriptions.append(
                            Subscription(
                                name=sub_dict.get("name", "Unknown"),
                                email_account=sub_dict.get("email_account", ""),
                                amount=sub_dict.get("amount"),
                                frequency=sub_dict.get("frequency"),
                                next_billing=datetime.fromisoformat(sub_dict["next_billing"])
                                if sub_dict.get("next_billing")
                                else None,
                                category=sub_dict.get("category"),
                                status=sub_dict.get("status", "active"),
                                receipt_date=datetime.fromisoformat(sub_dict["receipt_date"])
                                if sub_dict.get("receipt_date")
                                else None,
                                merchant=sub_dict.get("merchant"),
                                flagged_for_review=sub_dict.get("flagged_for_review", False),
                            )
                        )
            except Exception as exc:
                LOGGER.warning("Failed to load subscriptions: %s", exc)

        if not subscriptions:
            content_lines.append("No subscriptions found yet.")
            content_lines.append("\nRun subscription scan: 'Jarvis, scan my emails for subscriptions'")
            return AgentResponse(
                agent=self.name,
                content="\n".join(content_lines),
                data=data,
                status="warning",
                warnings=["no_subscriptions_found"],
            )

        # Classify subscriptions
        AI_MERCHANT_KEYWORDS = [
            "openai",
            "anthropic",
            "claude",
            "chatgpt",
            "midjourney",
            "stability",
            "runway",
            "perplexity",
            "elevenlabs",
            "cursor",
            "copilot",
            "notion ai",
            "ai",
            "gpt",
        ]

        APPLE_KEYWORDS = ["apple.com/bill", "apple", "itunes"]

        EDUCATION_KEYWORDS = [
            "udemy",
            "domestika",
            "skillshare",
            "masterclass",
            "craftsy",
            "creativelive",
            "coursera",
            "learnworlds",
        ]

        ai_subs, apple_subs, edu_subs, other_subs = [], [], [], []

        for s in subscriptions:
            name_lower = s.name.lower()
            if any(k in name_lower for k in AI_MERCHANT_KEYWORDS):
                ai_subs.append(s)
            elif any(k in name_lower for k in APPLE_KEYWORDS):
                apple_subs.append(s)
            elif any(k in name_lower for k in EDUCATION_KEYWORDS):
                edu_subs.append(s)
            else:
                other_subs.append(s)

        # Build content
        total_monthly = 0.0

        if ai_subs:
            content_lines.append("AI Subscriptions:")
            ai_total = 0.0
            for sub in ai_subs:
                amount_str = f"${sub.amount:,.2f}" if sub.amount else "Unknown"
                freq_str = f"/{sub.frequency}" if sub.frequency else ""
                content_lines.append(f"  {sub.name}: {amount_str}{freq_str}")
                if sub.amount and sub.frequency == "monthly":
                    ai_total += sub.amount
                elif sub.amount and sub.frequency == "annual":
                    ai_total += sub.amount / 12
            content_lines.append(f"  Total Monthly: ${ai_total:,.2f}")
            total_monthly += ai_total
            content_lines.append("")

        if apple_subs:
            content_lines.append("Apple App Store Subscriptions:")
            apple_total = 0.0
            for sub in apple_subs:
                amount_str = f"${sub.amount:,.2f}" if sub.amount else "Unknown"
                freq_str = f"/{sub.frequency}" if sub.frequency else ""
                content_lines.append(f"  {sub.name}: {amount_str}{freq_str}")
                if sub.amount and sub.frequency == "monthly":
                    apple_total += sub.amount
                elif sub.amount and sub.frequency == "annual":
                    apple_total += sub.amount / 12
            content_lines.append(f"  Total Monthly: ${apple_total:,.2f}")
            total_monthly += apple_total
            content_lines.append("")

        if edu_subs:
            content_lines.append("Education / Arts/Crafts Subscriptions:")
            edu_total = 0.0
            for sub in edu_subs:
                amount_str = f"${sub.amount:,.2f}" if sub.amount else "Unknown"
                freq_str = f"/{sub.frequency}" if sub.frequency else ""
                content_lines.append(f"  {sub.name}: {amount_str}{freq_str}")
                if sub.amount and sub.frequency == "monthly":
                    edu_total += sub.amount
                elif sub.amount and sub.frequency == "annual":
                    edu_total += sub.amount / 12
            content_lines.append(f"  Total Monthly: ${edu_total:,.2f}")
            total_monthly += edu_total
            content_lines.append("")

        if other_subs:
            content_lines.append("Other Subscriptions:")
            other_total = 0.0
            for sub in other_subs:
                amount_str = f"${sub.amount:,.2f}" if sub.amount else "Unknown"
                freq_str = f"/{sub.frequency}" if sub.frequency else ""
                content_lines.append(f"  {sub.name}: {amount_str}{freq_str}")
                if sub.amount and sub.frequency == "monthly":
                    other_total += sub.amount
                elif sub.amount and sub.frequency == "annual":
                    other_total += sub.amount / 12
            content_lines.append(f"  Total Monthly: ${other_total:,.2f}")
            total_monthly += other_total
            content_lines.append("")

        content_lines.append(f"Total Monthly Subscription Spend: ${total_monthly:,.2f}")

        # Check against constraint
        config = self._load_config()
        max_subscription_spend = config.get("constraints", {}).get("max_subscription_spend", 500)
        if total_monthly > max_subscription_spend:
            content_lines.append(
                f"⚠️ Warning: Monthly subscription spend (${total_monthly:,.2f}) exceeds "
                f"your constraint (${max_subscription_spend:,.2f})"
            )

        data["ai_subscriptions"] = [s.to_dict() for s in ai_subs]
        data["apple_subscriptions"] = [s.to_dict() for s in apple_subs]
        data["education_subscriptions"] = [s.to_dict() for s in edu_subs]
        data["other_subscriptions"] = [s.to_dict() for s in other_subs]
        data["total_monthly"] = total_monthly

        return AgentResponse(
            agent=self.name,
            content="\n".join(content_lines),
            data=data,
            status="success",
        )

    def _handle_goals(self) -> AgentResponse:
        """Track progress toward financial goals."""
        config = self._load_config()
        goals = config.get("goals", {})

        content_lines: List[str] = []
        data: Dict[str, Any] = {}

        if not goals:
            content_lines.append("No financial goals configured yet.")
            return AgentResponse(
                agent=self.name,
                content="\n".join(content_lines),
                data=data,
                status="warning",
            )

        # Get current total balance
        snapshots = self._load_account_snapshots()
        current_balance = sum(s.balance for s in snapshots)

        if "retirement" in goals:
            target = goals["retirement"].get("target_amount", 0)
            target_year = goals["retirement"].get("target_year", 2035)
            years_remaining = target_year - datetime.now().year
            progress = (current_balance / target * 100) if target > 0 else 0
            content_lines.append(f"Retirement Goal: ${target:,.2f} by {target_year}")
            content_lines.append(f"  Current: ${current_balance:,.2f} ({progress:.1f}%)")
            content_lines.append(f"  Remaining: ${target - current_balance:,.2f} ({years_remaining} years)")
            data["retirement"] = {
                "target": target,
                "current": current_balance,
                "progress": progress,
                "years_remaining": years_remaining,
            }

        if "land" in goals:
            target = goals["land"].get("target_amount", 0)
            target_year = goals["land"].get("target_year", 2026)
            years_remaining = target_year - datetime.now().year
            progress = (current_balance / target * 100) if target > 0 else 0
            content_lines.append(f"Land Goal: ${target:,.2f} by {target_year}")
            content_lines.append(f"  Current: ${current_balance:,.2f} ({progress:.1f}%)")
            content_lines.append(f"  Remaining: ${target - current_balance:,.2f} ({years_remaining} years)")
            data["land"] = {
                "target": target,
                "current": current_balance,
                "progress": progress,
                "years_remaining": years_remaining,
            }

        return AgentResponse(
            agent=self.name,
            content="\n".join(content_lines),
            data=data,
            status="success",
        )

    def _handle_savings_opportunities(self) -> AgentResponse:
        """Find key ways to save money: loans, fees, subscriptions."""
        content_lines: List[str] = []
        data: Dict[str, Any] = {
            "loans": [],
            "fees": [],
            "subscriptions": [],
        }

        config = self._load_config()

        # 1) Check for refinance opportunities (auto loans)
        accounts = config.get("accounts", [])
        loans = [acc for acc in accounts if acc.get("type") in ["auto_loan", "loan"]]
        for loan in loans:
            # Simple heuristic: if loan exists and is > 1 year old, suggest refinance
            data["loans"].append(
                {
                    "label": loan.get("name", "Unknown Loan"),
                    "institution": loan.get("institution", "Unknown"),
                    "type": loan.get("type"),
                    "reason": "Possible refinance candidate - check current rates",
                }
            )

        # 2) Check for fees in recent transactions
        if self.plaid.is_enabled():
            try:
                transactions = self.plaid.fetch_recent_transactions(days=30)
                fee_keywords = ["fee", "charge", "service", "maintenance", "overdraft", "nsf"]
                fees = []
                for txn in transactions:
                    merchant = (txn.get("merchant") or txn.get("name") or "").lower()
                    description = (txn.get("description") or "").lower()
                    combined = f"{merchant} {description}"

                    if any(keyword in combined for keyword in fee_keywords) and txn.get("amount", 0) < 0:
                        fees.append(
                            {
                                "amount": abs(txn.get("amount", 0)),
                                "reason": txn.get("merchant") or txn.get("name", "Unknown"),
                                "date": txn.get("date", ""),
                            }
                        )

                # Sum fees by reason
                fee_totals: Dict[str, float] = {}
                for fee in fees:
                    reason = fee["reason"]
                    fee_totals[reason] = fee_totals.get(reason, 0) + fee["amount"]

                for reason, total in fee_totals.items():
                    data["fees"].append(
                        {
                            "amount": total,
                            "reason": reason,
                            "count": sum(1 for f in fees if f["reason"] == reason),
                        }
                    )
            except Exception as exc:
                LOGGER.warning("Failed to fetch transactions for fee analysis: %s", exc)

        # 3) Check subscriptions for cancellation candidates
        subscriptions_file = self.finance_dir / "subscriptions" / "email_subscriptions.json"
        if subscriptions_file.exists():
            try:
                with open(subscriptions_file, "r", encoding="utf-8") as f:
                    subs_data = json.load(f)

                # Flag AI subscriptions and high-cost subscriptions
                max_subscription_spend = config.get("constraints", {}).get("max_subscription_spend", 500)
                total_monthly = 0.0

                for sub_dict in subs_data:
                    amount = sub_dict.get("amount")
                    frequency = sub_dict.get("frequency", "monthly")
                    category = sub_dict.get("category", "")

                    if amount:
                        if frequency == "monthly":
                            monthly_equiv = amount
                        elif frequency == "annual":
                            monthly_equiv = amount / 12
                        else:
                            monthly_equiv = amount

                        total_monthly += monthly_equiv

                        # Flag for review if:
                        # - AI subscription (often unused)
                        # - High cost
                        # - Already flagged
                        if (
                            category == "ai"
                            or monthly_equiv > 20
                            or sub_dict.get("flagged_for_review", False)
                        ):
                            reason = ""
                            if category == "ai":
                                reason = "AI tool - check if still needed"
                            elif monthly_equiv > 20:
                                reason = f"High cost (${monthly_equiv:,.2f}/month)"
                            else:
                                reason = "Flagged for review"

                            data["subscriptions"].append(
                                {
                                    "name": sub_dict.get("merchant") or sub_dict.get("name", "Unknown"),
                                    "monthly_equiv": monthly_equiv,
                                    "frequency": frequency,
                                    "category": category,
                                    "reason": reason,
                                }
                            )

                # If total exceeds constraint, flag all
                if total_monthly > max_subscription_spend:
                    content_lines.append(
                        f"⚠️ Total monthly subscriptions (${total_monthly:,.2f}) exceed your constraint "
                        f"(${max_subscription_spend:,.2f})"
                    )
            except Exception as exc:
                LOGGER.warning("Failed to load subscriptions for savings analysis: %s", exc)

        # Build content
        if data["loans"] or data["fees"] or data["subscriptions"]:
            content_lines.append("💡 Savings Opportunities:")
            content_lines.append("")

            # Loans
            if data["loans"]:
                for loan in data["loans"][:3]:  # Top 3
                    content_lines.append(
                        f"- Loan: {loan['label']} – {loan['reason']}"
                    )

            # Fees
            if data["fees"]:
                for fee in sorted(data["fees"], key=lambda x: x["amount"], reverse=True)[:3]:  # Top 3
                    content_lines.append(
                        f"- Fees: You were charged ${fee['amount']:,.2f} recently for {fee['reason']} "
                        f"({fee['count']} time{'s' if fee['count'] > 1 else ''})"
                    )

            # Subscriptions
            if data["subscriptions"]:
                for sub in sorted(data["subscriptions"], key=lambda x: x["monthly_equiv"], reverse=True)[:3]:  # Top 3
                    content_lines.append(
                        f"- Subscription: {sub['name']} at ${sub['monthly_equiv']:,.2f}/month – {sub['reason']}"
                    )
        else:
            content_lines.append("💡 Savings Opportunities:")
            content_lines.append("- No obvious savings opportunities detected yet; I'll keep monitoring.")

        return AgentResponse(
            agent=self.name,
            content="\n".join(content_lines),
            data=data,
            status="success",
        )

    # ---------- FIE-BASED HANDLERS ----------

    def _handle_overview_fie(self, query: str, config: Dict[str, Any]) -> AgentResponse:
        """FIE-based overview with cashflow forecast and burn rates."""
        data = self._load_accounts_and_transactions()
        accounts_raw = data.get("accounts", [])
        tx_raw = data.get("transactions", [])

        snapshots = [
            AccountSnapshot(name=a.get("name", "Account"), balance=float(a.get("balance", 0.0)))
            for a in accounts_raw
        ]
        balances = {a.name: a.balance for a in snapshots}

        primary_name = config.get("primary_salary_account", "personal_bog_7676")
        safety_cfg = config.get("safety_reserve", {})
        min_balance = float(safety_cfg.get("minimum_balance", 0.0))
        alert_threshold = float(safety_cfg.get("alert_threshold", min_balance))

        primary_balance = balances.get(primary_name, 0.0)

        lines: List[str] = []
        lines.append("Here's your current financial overview:")

        total_cash = sum(max(a.balance, 0.0) for a in snapshots)
        lines.append(f"- Total liquid balances across accounts: ${total_cash:,.2f}")
        lines.append(f"- Primary salary account ({primary_name}) balance: ${primary_balance:,.2f}")

        if primary_balance < min_balance:
            lines.append("⚠️ Your primary salary account is below your safety reserve.")
        elif primary_balance < alert_threshold:
            lines.append("⚠️ Your primary salary account is approaching your safety threshold.")

        # Use FIE for a quick 30-day cashflow forecast
        tx = self._tx_from_raw(tx_raw)
        engine = FinancialIntelligenceEngine(
            transactions=tx,
            primary_account_name=primary_name,
            current_balances=balances,
            config=config,
        )
        forecast_30 = engine.compute_cashflow_forecast(days=30)

        lines.append("")
        lines.append(
            f"Over the next 30 days, based on recent patterns, your primary account is projected to be "
            f"around ${forecast_30.projected_end_balance_primary:,.2f}."
        )
        if forecast_30.risk_of_negative:
            lines.append("⚠️ There is a risk of your primary account going negative without changes.")
        else:
            lines.append("✅ No immediate risk of going negative, assuming similar income/spending patterns.")

        burns = engine.compute_burn_rate_by_business()
        if burns:
            lines.append("")
            lines.append("Business burn (last ~30 days):")
            for b in burns:
                if b.monthly_burn < 0:
                    lines.append(f"- {b.label}: losing ${-b.monthly_burn:,.2f}/month")
                else:
                    lines.append(f"- {b.label}: surplus ${b.monthly_burn:,.2f}/month")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={
                "accounts": [a.to_dict() for a in snapshots],
                "forecast_30": forecast_30.__dict__,
                "burn_rates": [b.__dict__ for b in burns],
            },
            status="success",
            warnings=[],
        )

    def _handle_forecast(self, query: str, config: Dict[str, Any]) -> AgentResponse:
        """Cashflow forecast using FIE."""
        data = self._load_accounts_and_transactions()
        accounts_raw = data.get("accounts", [])
        tx_raw = data.get("transactions", [])

        snapshots = [
            AccountSnapshot(name=a.get("name", "Account"), balance=float(a.get("balance", 0.0)))
            for a in accounts_raw
        ]
        balances = {a.name: a.balance for a in snapshots}

        primary_name = config.get("primary_salary_account", "personal_bog_7676")

        tx = self._tx_from_raw(tx_raw)
        engine = FinancialIntelligenceEngine(
            transactions=tx,
            primary_account_name=primary_name,
            current_balances=balances,
            config=config,
        )

        forecast_7 = engine.compute_cashflow_forecast(days=7)
        forecast_30 = engine.compute_cashflow_forecast(days=30)
        forecast_90 = engine.compute_cashflow_forecast(days=90)

        lines: List[str] = []
        lines.append("Here's your projected cashflow based on recent patterns:")
        lines.append(
            f"- 7 days: ${forecast_7.projected_end_balance_primary:,.2f} "
            f"{'(risk of negative)' if forecast_7.risk_of_negative else ''}"
        )
        lines.append(
            f"- 30 days: ${forecast_30.projected_end_balance_primary:,.2f} "
            f"{'(risk of negative)' if forecast_30.risk_of_negative else ''}"
        )
        lines.append(
            f"- 90 days: ${forecast_90.projected_end_balance_primary:,.2f} "
            f"{'(risk of negative)' if forecast_90.risk_of_negative else ''}"
        )

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={
                "forecast_7": forecast_7.__dict__,
                "forecast_30": forecast_30.__dict__,
                "forecast_90": forecast_90.__dict__,
            },
            status="success",
            warnings=[],
        )

    def _handle_savings_opportunities_fie(self, query: str, config: Dict[str, Any]) -> AgentResponse:
        """FIE-based savings opportunities with duplicates, anomalies, and cut list."""
        data = self._load_accounts_and_transactions()
        tx_raw = data.get("transactions", [])
        subs_raw = data.get("subscriptions", [])
        accounts_raw = data.get("accounts", [])

        snapshots = [
            AccountSnapshot(name=a.get("name", "Account"), balance=float(a.get("balance", 0.0)))
            for a in accounts_raw
        ]
        balances = {a.name: a.balance for a in snapshots}

        primary_name = config.get("primary_salary_account", "personal_bog_7676")

        tx = self._tx_from_raw(tx_raw)
        engine = FinancialIntelligenceEngine(
            transactions=tx,
            primary_account_name=primary_name,
            current_balances=balances,
            config=config,
        )

        duplicates = engine.detect_duplicate_spend()
        anomalies = engine.detect_anomalies()
        cut_list = engine.generate_cut_list(subs_raw)

        lines: List[str] = []
        lines.append("Here are potential savings opportunities I see right now:")

        if cut_list:
            lines.append("")
            lines.append("📦 Subscriptions to review / cut:")
            for c in cut_list[:10]:
                lines.append(
                    f"- {c['name']}: ${c['monthly_equiv']:,.2f}/month – {c['reason']} (impact: {c['impact']})"
                )

        if duplicates:
            lines.append("")
            lines.append("🔁 Possible overlapping / duplicate spend:")
            for d in duplicates[:5]:
                lines.append(
                    f"- {d['name']}: about ${d['monthly_cost']:,.2f}/month across {d['count_30d']} recent charges."
                )

        if anomalies:
            lines.append("")
            lines.append("⚠️ Unusually large or suspicious-looking charges:")
            for a in anomalies[:5]:
                lines.append(
                    f"- {a['date']}: ${a['amount']:,.2f} at {a['description']} ({a['reason']})"
                )

        if not (cut_list or duplicates or anomalies):
            lines.append("")
            lines.append(
                "I don't see obvious savings opportunities yet with the data I have. "
                "Once more bank and subscription data flows in, I'll flag them for you."
            )

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={
                "cut_list": cut_list,
                "duplicates": duplicates,
                "anomalies": anomalies,
            },
            status="success",
            warnings=[],
        )

    def _handle_budget(self, query: str, config: Dict[str, Any]) -> AgentResponse:
        """Autobudget suggestions using FIE."""
        data = self._load_accounts_and_transactions()
        accounts_raw = data.get("accounts", [])
        tx_raw = data.get("transactions", [])

        snapshots = [
            AccountSnapshot(name=a.get("name", "Account"), balance=float(a.get("balance", 0.0)))
            for a in accounts_raw
        ]
        balances = {a.name: a.balance for a in snapshots}

        primary_name = config.get("primary_salary_account", "personal_bog_7676")
        primary_balance = balances.get(primary_name, 0.0)

        autobudget = AutoBudgetEngine(
            config=config,
            recent_transactions=tx_raw,
            primary_balance=primary_balance,
        )
        budget = autobudget.compute_monthly_budget()
        spend_free = autobudget.suggest_spend_free_days()

        lines: List[str] = []
        lines.append("Here's a suggested monthly budget based on your recent patterns:")

        lines.append(f"- Estimated monthly net cashflow: ${budget['estimated_monthly_net']:,.2f}")

        lines.append("")
        lines.append("Proposed allocations:")
        for b in budget["buckets"]:
            lines.append(f"- {b['name']}: ${b['amount']:,.2f} – {b['description']}")

        if budget["notes"]:
            lines.append("")
            lines.append("Notes:")
            for n in budget["notes"]:
                lines.append(f"- {n}")

        if spend_free["suggestion"]:
            s = spend_free["suggestion"]
            lines.append("")
            lines.append(f"🧘 Suggested: {s['days']} spend-free day(s) soon – {s['reason']}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={
                "budget": budget,
                "spend_free": spend_free,
            },
            status="success",
            warnings=[],
        )

    def _handle_autopay(self, query: str, config: Dict[str, Any]) -> AgentResponse:
        """Autopay calendar using FIE."""
        data = self._load_accounts_and_transactions()
        accounts_raw = data.get("accounts", [])
        bills_raw = data.get("bills", [])

        snapshots = [
            AccountSnapshot(name=a.get("name", "Account"), balance=float(a.get("balance", 0.0)))
            for a in accounts_raw
        ]
        balances = {a.name: a.balance for a in snapshots}

        primary_name = config.get("primary_salary_account", "personal_bog_7676")
        primary_balance = balances.get(primary_name, 0.0)

        safety_cfg = config.get("safety_reserve", {})
        min_balance = float(safety_cfg.get("minimum_balance", 0.0))

        bills: List[Bill] = []
        for b in bills_raw:
            try:
                bills.append(
                    Bill(
                        name=b["name"],
                        due_day=int(b["due_day"]),
                        amount=float(b["amount"]),
                        account_name=b.get("account_name"),
                        category=b.get("category"),
                    )
                )
            except Exception:
                continue

        # Paydays: for now use config, Cursor can wire to actual salary dates later.
        paydays_cfg = config.get("paydays", [{"day": 5, "description": "GMH salary"}])
        paydays: List[Payday] = []
        for p in paydays_cfg:
            try:
                paydays.append(Payday(day=int(p["day"]), description=p.get("description", "Salary")))
            except Exception:
                continue

        planner = AutopayPlanner(
            config=config,
            current_balance_primary=primary_balance,
            bills=bills,
            paydays=paydays,
            safety_minimum=min_balance,
        )
        plan = planner.generate_bill_calendar()

        lines: List[str] = []
        lines.append("Here's a simple bill / autopay calendar for this month:")

        for entry in plan["calendar"]:
            lines.append(
                f"- {entry['bill']}: ${entry['amount']:,.2f}, "
                f"due {entry['due_date']}, suggested autopay on {entry['suggested_autopay_date']}"
            )

        if plan["warnings"]:
            lines.append("")
            lines.append("Warnings:")
            for w in plan["warnings"]:
                lines.append(f"- {w}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data=plan,
            status="success",
            warnings=plan["warnings"],
        )

    def _handle_subscriptions_fie(self, query: str, config: Dict[str, Any]) -> AgentResponse:
        """Subscription breakdown using FIE classification."""
        data = self._load_accounts_and_transactions()
        subs_raw = data.get("subscriptions", [])

        # Normalize: ensure monthly_equiv exists
        subs_norm: List[Dict[str, Any]] = []
        for s in subs_raw:
            amount = float(s.get("amount", 0.0))
            period = (s.get("period") or "monthly").lower()
            if period == "yearly" or period == "annual":
                monthly_equiv = amount / 12.0
            else:
                monthly_equiv = amount
            subs_norm.append(
                {
                    "name": s.get("name"),
                    "amount": amount,
                    "period": period,
                    "monthly_equiv": monthly_equiv,
                    "category": s.get("category"),
                }
            )

        # Simple classification buckets for report
        AI_KEYS = ["openai", "anthropic", "claude", "chatgpt", "midjourney", "ai", "gpt"]
        APPLE_KEYS = ["apple.com/bill", "apple", "itunes"]
        EDU_KEYS = [
            "domestika",
            "skillshare",
            "udemy",
            "masterclass",
            "craftsy",
            "creativelive",
            "coursera",
        ]

        ai_subs: List[Dict[str, Any]] = []
        apple_subs: List[Dict[str, Any]] = []
        edu_subs: List[Dict[str, Any]] = []
        other_subs: List[Dict[str, Any]] = []

        for s in subs_norm:
            name_lower = str(s["name"] or "").lower()
            if any(k in name_lower for k in AI_KEYS):
                ai_subs.append(s)
            elif any(k in name_lower for k in APPLE_KEYS):
                apple_subs.append(s)
            elif any(k in name_lower for k in EDU_KEYS):
                edu_subs.append(s)
            else:
                other_subs.append(s)

        def total_monthly(subs: List[Dict[str, Any]]) -> float:
            return sum(s["monthly_equiv"] for s in subs)

        lines: List[str] = []
        lines.append("Here's a breakdown of your subscriptions (approx monthly cost):")
        lines.append(f"- AI tools: ${total_monthly(ai_subs):,.2f}")
        lines.append(f"- Apple App Store: ${total_monthly(apple_subs):,.2f}")
        lines.append(f"- Education / arts: ${total_monthly(edu_subs):,.2f}")
        lines.append(f"- Other: ${total_monthly(other_subs):,.2f}")
        lines.append(f"- TOTAL: ${total_monthly(subs_norm):,.2f}")

        if ai_subs:
            lines.append("")
            lines.append("AI subscriptions:")
            for s in ai_subs:
                lines.append(f"- {s['name']}: ${s['monthly_equiv']:,.2f}/month")

        if apple_subs:
            lines.append("")
            lines.append("Apple App Store subscriptions:")
            for s in apple_subs:
                lines.append(f"- {s['name']}: ${s['monthly_equiv']:,.2f}/month")

        if edu_subs:
            lines.append("")
            lines.append("Education / arts subscriptions:")
            for s in edu_subs:
                lines.append(f"- {s['name']}: ${s['monthly_equiv']:,.2f}/month")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={
                "ai": ai_subs,
                "apple": apple_subs,
                "education": edu_subs,
                "other": other_subs,
                "total_monthly": total_monthly(subs_norm),
            },
            status="success",
            warnings=[],
        )

    def _tx_from_raw(self, tx_raw: List[Dict[str, Any]]) -> List[FIETransaction]:
        """Convert raw transaction dicts to FIE Transaction objects."""
        tx: List[FIETransaction] = []
        for t in tx_raw:
            try:
                t_date_raw = t.get("date")
                if isinstance(t_date_raw, str):
                    t_date = date.fromisoformat(t_date_raw)
                elif isinstance(t_date_raw, date):
                    t_date = t_date_raw
                else:
                    continue
                tx.append(
                    FIETransaction(
                        date=t_date,
                        amount=float(t.get("amount", 0.0)),
                        description=t.get("description", ""),
                        account_name=t.get("account_name", "Account"),
                        category=t.get("category"),
                        business=t.get("business"),
                    )
                )
            except Exception:
                continue
        return tx



    # ===========================================
    # DASHBOARD CSV HANDLERS
    # ===========================================

    def _load_dashboard_csv(self) -> List[Dict[str, Any]]:
        """Load transactions from email scanner CSV"""
        import csv
        
        # Try financial-dashboard location first
        dashboard_csv = self.base_path.parent / "financial-dashboard" / "latest_financial_data.csv"
        if not dashboard_csv.exists():
            # Try data/finance fallback
            dashboard_csv = self.finance_dir / "latest_financial_data.csv"
        
        if not dashboard_csv.exists():
            LOGGER.warning("Dashboard CSV not found")
            return []
        
        try:
            with open(dashboard_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            LOGGER.error(f"Error loading dashboard CSV: {e}")
            return []

    def _handle_failed_payments(self) -> AgentResponse:
        """Handle 'any failed payments?' voice command"""
        rows = self._load_dashboard_csv()
        failed = [r for r in rows if r.get('Status', '').upper() == 'FAILED']
        
        if not failed:
            return AgentResponse(
                agent="FinanceAgent",
                content="✅ No failed payments detected. All transactions are current.",
                data={"failed_count": 0},
                status="success"
            )
        
        # Format response
        messages = [f"⚠️ {len(failed)} failed payment(s) detected:"]
        for f in failed[:5]:  # Limit to 5
            subject = f.get('Subject', 'Unknown')
            amount = f.get('Amount', 'N/A')
            entity = f.get('Entity', '')
            msg = f"• {subject}"
            if amount:
                msg += f" - {amount}"
            if entity:
                msg += f" ({entity})"
            messages.append(msg)
        
        if len(failed) > 5:
            messages.append(f"... and {len(failed) - 5} more. Check dashboard for details.")
        
        return AgentResponse(
            agent="FinanceAgent",
            content="\n".join(messages),
            data={
                "failed_count": len(failed),
                "failed_transactions": failed[:10]
            },
            status="warning"
        )

    def _handle_upcoming_bills(self) -> AgentResponse:
        """Handle 'bills due soon' voice command"""
        from datetime import datetime, timedelta
        
        rows = self._load_dashboard_csv()
        today = datetime.now().date()
        upcoming = []
        
        for r in rows:
            if r.get('DueDate'):
                try:
                    due = datetime.strptime(r['DueDate'], '%Y-%m-%d').date()
                    if today <= due <= today + timedelta(days=7):
                        upcoming.append(r)
                except (ValueError, TypeError):
                    pass
        
        if not upcoming:
            return AgentResponse(
                agent="FinanceAgent",
                content="✅ No bills due in the next 7 days.",
                data={"upcoming_count": 0},
                status="success"
            )
        
        # Sort by due date
        upcoming.sort(key=lambda x: x.get('DueDate', ''))
        
        messages = [f"📅 {len(upcoming)} bill(s) due in the next 7 days:"]
        for bill in upcoming[:5]:
            subject = bill.get('Subject', 'Unknown')
            due_date = bill.get('DueDate', 'N/A')
            amount = bill.get('Amount', 'N/A')
            msg = f"• {subject} - Due {due_date}"
            if amount:
                msg += f" ({amount})"
            messages.append(msg)
        
        if len(upcoming) > 5:
            messages.append(f"... and {len(upcoming) - 5} more.")
        
        return AgentResponse(
            agent="FinanceAgent",
            content="\n".join(messages),
            data={
                "upcoming_count": len(upcoming),
                "upcoming_bills": upcoming[:10]
            },
            status="success"
        )

    def _handle_license_status(self) -> AgentResponse:
        """Handle 'licenses expiring' voice command"""
        from datetime import datetime
        
        rows = self._load_dashboard_csv()
        license_keywords = ['license', 'dea', 'medical board', 'domain', 'ssl', 'certification']
        licenses = []
        
        for row in rows:
            subject = row.get('Subject', '').lower()
            if any(kw in subject for kw in license_keywords) and row.get('DueDate'):
                try:
                    exp_date = datetime.strptime(row['DueDate'], '%Y-%m-%d').date()
                    days_remaining = (exp_date - datetime.now().date()).days
                    licenses.append({
                        'subject': row.get('Subject'),
                        'expiration': row['DueDate'],
                        'days_remaining': days_remaining,
                        'entity': row.get('Entity')
                    })
                except (ValueError, TypeError):
                    pass
        
        # Filter to expiring soon (<90 days)
        expiring = [l for l in licenses if l['days_remaining'] < 90]
        
        if not expiring:
            return AgentResponse(
                agent="FinanceAgent",
                content="✅ All licenses and certifications are current (>90 days).",
                data={"expiring_count": 0},
                status="success"
            )
        
        # Sort by urgency
        expiring.sort(key=lambda x: x['days_remaining'])
        
        messages = [f"⚠️ {len(expiring)} license(s) expiring within 90 days:"]
        for lic in expiring[:5]:
            days = lic['days_remaining']
            status = "🔴 URGENT" if days < 30 else "🟠 WARNING"
            messages.append(f"• {lic['subject']} - {days} days ({status})")
        
        if len(expiring) > 5:
            messages.append(f"... and {len(expiring) - 5} more.")
        
        return AgentResponse(
            agent="FinanceAgent",
            content="\n".join(messages),
            data={
                "expiring_count": len(expiring),
                "licenses": expiring[:10]
            },
            status="warning" if any(l['days_remaining'] < 30 for l in expiring) else "success"
        )
