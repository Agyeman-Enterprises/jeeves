# backend/services/personal_life_service.py
"""
Personal Life Service

Manages all personal life tracking for JARVIS:
- Health metrics (weight, sleep, exercise)
- Important dates (birthdays, anniversaries)
- Personal renewals (licenses, insurance, subscriptions)
- Reminders
- Goals and accountability
- Daily logs

Provides the personal briefing data for the morning ritual.
"""

import logging
import os
from dataclasses import asdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from app.models.personal_life_models import (
    DailyLog,
    DateCategory,
    GoalCategory,
    GoalStatus,
    HealthMetric,
    HealthMetricType,
    ImportantDate,
    PersonalGoal,
    PersonalReminder,
    PersonalRenewal,
    RenewalCategory,
    RenewalStatus,
)

LOGGER = logging.getLogger("backend.services.personal_life")


class PersonalLifeService:
    """
    Service for managing personal life tracking.

    Connects to JarvisCore (Supabase) for data persistence.
    """

    def __init__(self):
        self.supabase_url = os.getenv("JARVISCORE_SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        self.supabase_key = os.getenv("JARVISCORE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self._client: Optional[Client] = None

    @property
    def client(self) -> Optional[Client]:
        """Lazy-load Supabase client."""
        if self._client is None and self.supabase_url and self.supabase_key:
            try:
                self._client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                LOGGER.error(f"Failed to create Supabase client: {e}")
        return self._client

    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return self.client is not None

    # =========================================================================
    # PERSONAL BRIEFING (for morning ritual)
    # =========================================================================

    async def get_personal_briefing(self) -> Dict[str, Any]:
        """
        Get aggregated personal briefing for morning ritual.

        Returns health status, upcoming dates, renewals due, and goals progress.
        """
        briefing = {
            "timestamp": datetime.now().isoformat(),
            "health": await self._get_health_summary(),
            "upcoming_dates": await self._get_upcoming_dates(days=14),
            "renewals_due": await self._get_renewals_due(days=30),
            "reminders_today": await self._get_reminders_today(),
            "goals": await self._get_goals_summary(),
            "yesterday_log": await self._get_yesterday_log(),
            "spoken_summary": "",
        }

        # Generate spoken summary
        briefing["spoken_summary"] = self._generate_spoken_summary(briefing)

        return briefing

    async def _get_health_summary(self) -> Dict[str, Any]:
        """Get recent health metrics summary."""
        if not self.client:
            return self._mock_health_summary()

        try:
            # Get latest weight
            weight_result = self.client.table("jarvis_health_metrics").select("*").eq(
                "metric_type", "weight"
            ).order("recorded_at", desc=True).limit(1).execute()

            latest_weight = weight_result.data[0] if weight_result.data else None

            # Get weight from 7 days ago for trend
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            weight_week_ago = self.client.table("jarvis_health_metrics").select("*").eq(
                "metric_type", "weight"
            ).lt("recorded_at", week_ago).order("recorded_at", desc=True).limit(1).execute()

            weight_change = None
            if latest_weight and weight_week_ago.data:
                weight_change = float(latest_weight["value"]) - float(weight_week_ago.data[0]["value"])

            # Get last night's sleep
            sleep_result = self.client.table("jarvis_health_metrics").select("*").eq(
                "metric_type", "sleep_hours"
            ).order("recorded_at", desc=True).limit(1).execute()

            latest_sleep = sleep_result.data[0] if sleep_result.data else None

            return {
                "weight": {
                    "current": float(latest_weight["value"]) if latest_weight else None,
                    "unit": latest_weight.get("unit", "lbs") if latest_weight else "lbs",
                    "weekly_change": weight_change,
                    "trend": "down" if weight_change and weight_change < 0 else "up" if weight_change else "stable",
                },
                "sleep": {
                    "last_night": float(latest_sleep["value"]) if latest_sleep else None,
                    "goal": 7.0,
                    "met_goal": float(latest_sleep["value"]) >= 7.0 if latest_sleep else False,
                },
                "streak": {
                    "exercise_days": 0,  # TODO: Calculate from logs
                    "logging_days": 0,
                },
            }
        except Exception as e:
            LOGGER.warning(f"Failed to get health summary: {e}")
            return self._mock_health_summary()

    def _mock_health_summary(self) -> Dict[str, Any]:
        """Mock health summary when DB not available."""
        return {
            "weight": {
                "current": 185.5,
                "unit": "lbs",
                "weekly_change": -2.0,
                "trend": "down",
            },
            "sleep": {
                "last_night": 6.5,
                "goal": 7.0,
                "met_goal": False,
            },
            "streak": {
                "exercise_days": 3,
                "logging_days": 12,
            },
        }

    async def _get_upcoming_dates(self, days: int = 14) -> List[Dict[str, Any]]:
        """Get important dates coming up."""
        if not self.client:
            return self._mock_upcoming_dates()

        try:
            today = date.today()
            # Get all dates and filter in Python (for recurring yearly dates)
            result = self.client.table("jarvis_important_dates").select("*").execute()

            upcoming = []
            for row in result.data or []:
                event_date = datetime.strptime(row["event_date"], "%Y-%m-%d").date()
                # Adjust for recurring yearly
                if row.get("is_recurring", True):
                    next_occurrence = event_date.replace(year=today.year)
                    if next_occurrence < today:
                        next_occurrence = next_occurrence.replace(year=today.year + 1)
                else:
                    next_occurrence = event_date

                days_until = (next_occurrence - today).days
                if 0 <= days_until <= days:
                    upcoming.append({
                        "id": row["id"],
                        "title": row["title"],
                        "category": row["category"],
                        "date": next_occurrence.isoformat(),
                        "days_until": days_until,
                        "person_name": row.get("person_name"),
                        "gift_ideas": row.get("gift_ideas"),
                    })

            return sorted(upcoming, key=lambda x: x["days_until"])
        except Exception as e:
            LOGGER.warning(f"Failed to get upcoming dates: {e}")
            return self._mock_upcoming_dates()

    def _mock_upcoming_dates(self) -> List[Dict[str, Any]]:
        """Mock upcoming dates."""
        today = date.today()
        return [
            {
                "id": "mock-1",
                "title": "Mom's Birthday",
                "category": "birthday",
                "date": (today + timedelta(days=3)).isoformat(),
                "days_until": 3,
                "person_name": "Mom",
                "gift_ideas": "Flowers, spa gift card",
            },
            {
                "id": "mock-2",
                "title": "Wedding Anniversary",
                "category": "anniversary",
                "date": (today + timedelta(days=12)).isoformat(),
                "days_until": 12,
                "person_name": None,
                "gift_ideas": None,
            },
        ]

    async def _get_renewals_due(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get renewals expiring soon."""
        if not self.client:
            return self._mock_renewals_due()

        try:
            cutoff = (date.today() + timedelta(days=days)).isoformat()
            result = self.client.table("jarvis_personal_renewals").select("*").lte(
                "expiration_date", cutoff
            ).eq("status", "active").order("expiration_date").execute()

            today = date.today()
            renewals = []
            for row in result.data or []:
                exp_date = datetime.strptime(row["expiration_date"], "%Y-%m-%d").date()
                days_until = (exp_date - today).days
                renewals.append({
                    "id": row["id"],
                    "title": row["title"],
                    "category": row["category"],
                    "provider": row.get("provider"),
                    "expiration_date": row["expiration_date"],
                    "days_until": days_until,
                    "cost": row.get("cost"),
                    "auto_renew": row.get("auto_renew", False),
                    "is_overdue": days_until < 0,
                })

            return renewals
        except Exception as e:
            LOGGER.warning(f"Failed to get renewals: {e}")
            return self._mock_renewals_due()

    def _mock_renewals_due(self) -> List[Dict[str, Any]]:
        """Mock renewals due."""
        today = date.today()
        return [
            {
                "id": "mock-1",
                "title": "Car Insurance",
                "category": "insurance",
                "provider": "GEICO",
                "expiration_date": (today + timedelta(days=12)).isoformat(),
                "days_until": 12,
                "cost": 890.00,
                "auto_renew": True,
                "is_overdue": False,
            },
            {
                "id": "mock-2",
                "title": "Medical License",
                "category": "license",
                "provider": "State Medical Board",
                "expiration_date": (today + timedelta(days=45)).isoformat(),
                "days_until": 45,
                "cost": 350.00,
                "auto_renew": False,
                "is_overdue": False,
            },
        ]

    async def _get_reminders_today(self) -> List[Dict[str, Any]]:
        """Get reminders for today."""
        if not self.client:
            return []

        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
            today_end = datetime.now().replace(hour=23, minute=59, second=59).isoformat()

            result = self.client.table("jarvis_personal_reminders").select("*").eq(
                "is_active", True
            ).gte("remind_at", today_start).lte("remind_at", today_end).execute()

            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "description": row.get("description"),
                    "remind_at": row["remind_at"],
                    "priority": row.get("priority", "normal"),
                }
                for row in result.data or []
            ]
        except Exception as e:
            LOGGER.warning(f"Failed to get reminders: {e}")
            return []

    async def _get_goals_summary(self) -> Dict[str, Any]:
        """Get active goals summary."""
        if not self.client:
            return self._mock_goals_summary()

        try:
            result = self.client.table("jarvis_personal_goals").select("*").eq(
                "status", "active"
            ).execute()

            goals = []
            for row in result.data or []:
                goals.append({
                    "id": row["id"],
                    "title": row["title"],
                    "category": row["category"],
                    "progress_pct": float(row.get("progress_pct", 0)),
                    "streak_days": row.get("streak_days", 0),
                    "target_date": row.get("target_date"),
                    "needs_check_in": self._needs_check_in(row),
                })

            return {
                "active_count": len(goals),
                "goals": goals,
                "needing_attention": [g for g in goals if g.get("needs_check_in")],
            }
        except Exception as e:
            LOGGER.warning(f"Failed to get goals: {e}")
            return self._mock_goals_summary()

    def _mock_goals_summary(self) -> Dict[str, Any]:
        """Mock goals summary."""
        return {
            "active_count": 3,
            "goals": [
                {
                    "id": "mock-1",
                    "title": "Lose 20 lbs",
                    "category": "fitness",
                    "progress_pct": 35.0,
                    "streak_days": 12,
                    "target_date": (date.today() + timedelta(days=60)).isoformat(),
                    "needs_check_in": False,
                },
                {
                    "id": "mock-2",
                    "title": "Exercise 4x per week",
                    "category": "fitness",
                    "progress_pct": 75.0,
                    "streak_days": 3,
                    "target_date": None,
                    "needs_check_in": True,
                },
            ],
            "needing_attention": [],
        }

    def _needs_check_in(self, goal: Dict) -> bool:
        """Check if goal needs a check-in."""
        if not goal.get("accountability_enabled", True):
            return False

        last_check_in = goal.get("last_check_in")
        if not last_check_in:
            return True

        last_dt = datetime.fromisoformat(last_check_in.replace("Z", "+00:00"))
        frequency = goal.get("check_in_frequency", "daily")

        if frequency == "daily":
            return (datetime.now(last_dt.tzinfo) - last_dt).days >= 1
        elif frequency == "weekly":
            return (datetime.now(last_dt.tzinfo) - last_dt).days >= 7

        return False

    async def _get_yesterday_log(self) -> Optional[Dict[str, Any]]:
        """Get yesterday's daily log for reflection."""
        if not self.client:
            return self._mock_yesterday_log()

        try:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            result = self.client.table("jarvis_daily_logs").select("*").eq(
                "log_date", yesterday
            ).limit(1).execute()

            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            LOGGER.warning(f"Failed to get yesterday log: {e}")
            return None

    def _mock_yesterday_log(self) -> Dict[str, Any]:
        """Mock yesterday's log."""
        return {
            "mood_score": 7,
            "energy_score": 6,
            "sleep_hours": 6.5,
            "exercise_minutes": 30,
            "tasks_completed": 8,
        }

    def _generate_spoken_summary(self, briefing: Dict) -> str:
        """Generate TTS-ready personal summary."""
        parts = []

        # Health
        health = briefing.get("health", {})
        weight = health.get("weight", {})
        sleep = health.get("sleep", {})

        if sleep.get("last_night"):
            hours = sleep["last_night"]
            goal = sleep.get("goal", 7)
            if hours < goal:
                parts.append(f"You slept {hours} hours last night, below your {goal}-hour goal.")
            else:
                parts.append(f"You got {hours} hours of sleep. Well rested.")

        if weight.get("weekly_change"):
            change = weight["weekly_change"]
            if change < 0:
                parts.append(f"Weight is down {abs(change):.1f} pounds this week. Good progress.")
            elif change > 0:
                parts.append(f"Weight is up {change:.1f} pounds this week.")

        # Upcoming dates
        dates = briefing.get("upcoming_dates", [])
        urgent_dates = [d for d in dates if d.get("days_until", 999) <= 3]
        if urgent_dates:
            first = urgent_dates[0]
            parts.append(f"{first['title']} is in {first['days_until']} days.")

        # Renewals
        renewals = briefing.get("renewals_due", [])
        urgent_renewals = [r for r in renewals if r.get("days_until", 999) <= 14 and not r.get("auto_renew")]
        if urgent_renewals:
            first = urgent_renewals[0]
            parts.append(f"{first['title']} expires in {first['days_until']} days.")

        # Goals needing attention
        goals = briefing.get("goals", {})
        needs_attention = goals.get("needing_attention", [])
        if needs_attention:
            parts.append(f"{len(needs_attention)} goal{'s' if len(needs_attention) > 1 else ''} need check-in.")

        if not parts:
            parts.append("All personal items on track.")

        return " ".join(parts)

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    async def log_health_metric(
        self,
        metric_type: HealthMetricType,
        value: float,
        unit: str = "",
        notes: Optional[str] = None,
        source: str = "manual",
    ) -> Optional[Dict]:
        """Log a health metric reading."""
        if not self.client:
            LOGGER.warning("Cannot log metric - Supabase not configured")
            return None

        try:
            result = self.client.table("jarvis_health_metrics").insert({
                "metric_type": metric_type.value,
                "value": value,
                "unit": unit,
                "notes": notes,
                "source": source,
                "recorded_at": datetime.now().isoformat(),
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            LOGGER.error(f"Failed to log health metric: {e}")
            return None

    async def add_important_date(self, date_info: ImportantDate) -> Optional[Dict]:
        """Add an important date."""
        if not self.client:
            return None

        try:
            result = self.client.table("jarvis_important_dates").insert({
                "title": date_info.title,
                "category": date_info.category.value,
                "event_date": date_info.date.isoformat(),
                "is_recurring": date_info.is_recurring,
                "person_name": date_info.person_name,
                "remind_days_before": date_info.remind_days_before,
                "notes": date_info.notes,
                "gift_ideas": date_info.gift_ideas,
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            LOGGER.error(f"Failed to add important date: {e}")
            return None

    async def add_renewal(self, renewal: PersonalRenewal) -> Optional[Dict]:
        """Add a personal renewal to track."""
        if not self.client:
            return None

        try:
            result = self.client.table("jarvis_personal_renewals").insert({
                "title": renewal.title,
                "category": renewal.category.value,
                "provider": renewal.provider,
                "status": renewal.status.value,
                "expiration_date": renewal.expiration_date.isoformat(),
                "auto_renew": renewal.auto_renew,
                "cost": renewal.cost,
                "billing_frequency": renewal.billing_frequency,
                "remind_days_before": renewal.remind_days_before,
                "account_number": renewal.account_number,
                "website": renewal.website,
                "notes": renewal.notes,
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            LOGGER.error(f"Failed to add renewal: {e}")
            return None

    async def log_daily(self, log: DailyLog) -> Optional[Dict]:
        """Log or update daily entry."""
        if not self.client:
            return None

        try:
            data = {
                "log_date": log.log_date.isoformat(),
                "mood_score": log.mood_score,
                "energy_score": log.energy_score,
                "stress_score": log.stress_score,
                "sleep_hours": log.sleep_hours,
                "sleep_quality": log.sleep_quality,
                "exercise_minutes": log.exercise_minutes,
                "exercise_type": log.exercise_type,
                "steps": log.steps,
                "water_glasses": log.water_glasses,
                "calories": log.calories,
                "focus_score": log.focus_score,
                "tasks_completed": log.tasks_completed,
                "gratitude": log.gratitude,
                "wins": log.wins,
                "challenges": log.challenges,
                "notes": log.notes,
                "updated_at": datetime.now().isoformat(),
            }

            result = self.client.table("jarvis_daily_logs").upsert(
                data, on_conflict="log_date"
            ).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            LOGGER.error(f"Failed to log daily: {e}")
            return None


# Singleton instance
_personal_life_service: Optional[PersonalLifeService] = None


def get_personal_life_service() -> PersonalLifeService:
    """Get or create the personal life service singleton."""
    global _personal_life_service
    if _personal_life_service is None:
        _personal_life_service = PersonalLifeService()
    return _personal_life_service
