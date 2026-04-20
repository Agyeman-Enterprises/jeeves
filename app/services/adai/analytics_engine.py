"""
AdAI Analytics Engine
Calculates KPIs, generates reports, and provides performance insights.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)


@dataclass
class PerformanceThresholds:
    """Thresholds for performance evaluation."""
    ctr_warning: float = 0.5    # CTR below this is concerning
    ctr_good: float = 2.0       # CTR above this is good
    cpa_max: float = 50.0       # CPA above this needs attention
    roas_min: float = 2.0       # ROAS below this needs attention
    roas_good: float = 4.0      # ROAS above this is excellent
    frequency_max: float = 3.0  # Frequency above this means fatigue


@dataclass
class PerformanceScore:
    """Performance evaluation score."""
    score: float  # 0-100
    grade: str    # A, B, C, D, F
    factors: Dict[str, Dict[str, Any]]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "grade": self.grade,
            "factors": self.factors,
            "recommendations": self.recommendations,
        }


class AnalyticsEngine:
    """
    Analytics engine for ad performance analysis.

    Features:
    - KPI calculation
    - Performance scoring
    - Trend analysis
    - Anomaly detection
    - Recommendations generation
    """

    def __init__(self, thresholds: Optional[PerformanceThresholds] = None):
        """Initialize analytics engine with optional custom thresholds."""
        self.thresholds = thresholds or PerformanceThresholds()

    def calculate_kpis(
        self,
        impressions: int,
        clicks: int,
        spend: float,
        conversions: int,
        revenue: float = 0.0,
    ) -> Dict[str, float]:
        """
        Calculate standard advertising KPIs.

        Args:
            impressions: Total impressions
            clicks: Total clicks
            spend: Total spend in USD
            conversions: Total conversions
            revenue: Total revenue in USD

        Returns:
            Dict of KPI values
        """
        return {
            "ctr": round((clicks / impressions * 100) if impressions > 0 else 0, 2),
            "cpc": round((spend / clicks) if clicks > 0 else 0, 2),
            "cpa": round((spend / conversions) if conversions > 0 else 0, 2),
            "roas": round((revenue / spend) if spend > 0 else 0, 2),
            "cvr": round((conversions / clicks * 100) if clicks > 0 else 0, 2),
            "cpm": round((spend / impressions * 1000) if impressions > 0 else 0, 2),
        }

    def evaluate_performance(
        self,
        impressions: int,
        clicks: int,
        spend: float,
        conversions: int,
        revenue: float = 0.0,
        frequency: float = 0.0,
    ) -> PerformanceScore:
        """
        Evaluate overall campaign performance.

        Args:
            impressions: Total impressions
            clicks: Total clicks
            spend: Total spend
            conversions: Total conversions
            revenue: Total revenue
            frequency: Ad frequency

        Returns:
            PerformanceScore with score, grade, and recommendations
        """
        kpis = self.calculate_kpis(impressions, clicks, spend, conversions, revenue)
        factors = {}
        recommendations = []
        total_score = 0
        factor_count = 0

        # Evaluate CTR
        ctr = kpis["ctr"]
        if ctr >= self.thresholds.ctr_good:
            ctr_score = 100
            ctr_status = "excellent"
        elif ctr >= self.thresholds.ctr_warning:
            ctr_score = 60 + (ctr - self.thresholds.ctr_warning) / (self.thresholds.ctr_good - self.thresholds.ctr_warning) * 40
            ctr_status = "good"
        else:
            ctr_score = max(0, ctr / self.thresholds.ctr_warning * 60)
            ctr_status = "needs_attention"
            recommendations.append("Low CTR: Consider refreshing ad creative or adjusting targeting")

        factors["ctr"] = {"value": ctr, "score": round(ctr_score, 1), "status": ctr_status}
        total_score += ctr_score
        factor_count += 1

        # Evaluate CPA (if conversions exist)
        if conversions > 0:
            cpa = kpis["cpa"]
            if cpa <= self.thresholds.cpa_max * 0.5:
                cpa_score = 100
                cpa_status = "excellent"
            elif cpa <= self.thresholds.cpa_max:
                cpa_score = 100 - (cpa / self.thresholds.cpa_max * 50)
                cpa_status = "acceptable"
            else:
                cpa_score = max(0, 50 - (cpa - self.thresholds.cpa_max) / self.thresholds.cpa_max * 50)
                cpa_status = "needs_attention"
                recommendations.append(f"High CPA (${cpa:.2f}): Consider optimizing for conversions or reducing bids")

            factors["cpa"] = {"value": cpa, "score": round(cpa_score, 1), "status": cpa_status}
            total_score += cpa_score
            factor_count += 1

        # Evaluate ROAS (if revenue exists)
        if revenue > 0:
            roas = kpis["roas"]
            if roas >= self.thresholds.roas_good:
                roas_score = 100
                roas_status = "excellent"
            elif roas >= self.thresholds.roas_min:
                roas_score = 60 + (roas - self.thresholds.roas_min) / (self.thresholds.roas_good - self.thresholds.roas_min) * 40
                roas_status = "good"
            else:
                roas_score = max(0, roas / self.thresholds.roas_min * 60)
                roas_status = "needs_attention"
                recommendations.append(f"Low ROAS ({roas:.2f}x): Review targeting and consider higher-value audiences")

            factors["roas"] = {"value": roas, "score": round(roas_score, 1), "status": roas_status}
            total_score += roas_score
            factor_count += 1

        # Evaluate frequency
        if frequency > 0:
            if frequency <= self.thresholds.frequency_max * 0.5:
                freq_score = 100
                freq_status = "good"
            elif frequency <= self.thresholds.frequency_max:
                freq_score = 100 - (frequency / self.thresholds.frequency_max * 30)
                freq_status = "acceptable"
            else:
                freq_score = max(0, 70 - (frequency - self.thresholds.frequency_max) * 10)
                freq_status = "fatigue_risk"
                recommendations.append(f"High frequency ({frequency:.1f}): Consider rotating creatives or expanding audience")

            factors["frequency"] = {"value": frequency, "score": round(freq_score, 1), "status": freq_status}
            total_score += freq_score
            factor_count += 1

        # Calculate overall score
        overall_score = total_score / factor_count if factor_count > 0 else 0

        # Determine grade
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return PerformanceScore(
            score=overall_score,
            grade=grade,
            factors=factors,
            recommendations=recommendations,
        )

    def detect_anomalies(
        self,
        current: Dict[str, float],
        baseline: Dict[str, float],
        threshold_pct: float = 20.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies by comparing current metrics to baseline.

        Args:
            current: Current period metrics
            baseline: Baseline/previous period metrics
            threshold_pct: Percentage change threshold for anomaly

        Returns:
            List of anomaly dicts
        """
        anomalies = []
        metrics_to_check = ["spend", "impressions", "clicks", "conversions", "ctr", "cpa", "roas"]

        for metric in metrics_to_check:
            current_val = current.get(metric, 0)
            baseline_val = baseline.get(metric, 0)

            if baseline_val == 0:
                continue

            change_pct = ((current_val - baseline_val) / baseline_val) * 100

            if abs(change_pct) >= threshold_pct:
                direction = "increase" if change_pct > 0 else "decrease"
                severity = "high" if abs(change_pct) >= threshold_pct * 2 else "medium"

                # Determine if change is positive or negative for this metric
                # For cost metrics (spend, cpa, cpc), decrease is good
                # For performance metrics (roas, ctr, conversions), increase is good
                cost_metrics = ["spend", "cpa", "cpc", "cpm"]
                is_positive = (
                    (metric in cost_metrics and change_pct < 0) or
                    (metric not in cost_metrics and change_pct > 0)
                )

                anomalies.append({
                    "metric": metric,
                    "current_value": round(current_val, 2),
                    "baseline_value": round(baseline_val, 2),
                    "change_pct": round(change_pct, 1),
                    "direction": direction,
                    "severity": severity,
                    "is_positive": is_positive,
                })

        return anomalies

    def generate_daily_report(
        self,
        campaigns: List[Dict[str, Any]],
        date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generate a daily performance report.

        Args:
            campaigns: List of campaign data dicts
            date: Report date (defaults to today)

        Returns:
            Report dict with summary and details
        """
        report_date = date or datetime.utcnow()

        # Aggregate metrics
        total_impressions = sum(c.get("impressions", 0) for c in campaigns)
        total_clicks = sum(c.get("clicks", 0) for c in campaigns)
        total_spend = sum(c.get("spend", 0) for c in campaigns)
        total_conversions = sum(c.get("conversions", 0) for c in campaigns)
        total_revenue = sum(c.get("revenue", 0) for c in campaigns)

        kpis = self.calculate_kpis(
            total_impressions,
            total_clicks,
            total_spend,
            total_conversions,
            total_revenue,
        )

        # Evaluate overall performance
        performance = self.evaluate_performance(
            total_impressions,
            total_clicks,
            total_spend,
            total_conversions,
            total_revenue,
        )

        # Identify top and bottom performers
        sorted_by_roas = sorted(
            [c for c in campaigns if c.get("spend", 0) > 0],
            key=lambda x: x.get("revenue", 0) / x.get("spend", 1) if x.get("spend", 0) > 0 else 0,
            reverse=True,
        )

        top_performers = sorted_by_roas[:3]
        bottom_performers = sorted_by_roas[-3:] if len(sorted_by_roas) > 3 else []

        return {
            "date": report_date.date().isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_campaigns": len(campaigns),
                "active_campaigns": len([c for c in campaigns if c.get("status") == "ACTIVE"]),
                "total_spend": round(total_spend, 2),
                "total_conversions": total_conversions,
                "total_revenue": round(total_revenue, 2),
            },
            "kpis": kpis,
            "performance": performance.to_dict(),
            "top_performers": [
                {
                    "name": c.get("name"),
                    "spend": round(c.get("spend", 0), 2),
                    "conversions": c.get("conversions", 0),
                    "roas": round(c.get("revenue", 0) / c.get("spend", 1) if c.get("spend", 0) > 0 else 0, 2),
                }
                for c in top_performers
            ],
            "bottom_performers": [
                {
                    "name": c.get("name"),
                    "spend": round(c.get("spend", 0), 2),
                    "conversions": c.get("conversions", 0),
                    "roas": round(c.get("revenue", 0) / c.get("spend", 1) if c.get("spend", 0) > 0 else 0, 2),
                }
                for c in bottom_performers
            ],
        }

    def suggest_budget_changes(
        self,
        campaigns: List[Dict[str, Any]],
        total_budget: float,
        min_budget: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """
        Suggest budget reallocation based on performance.

        Args:
            campaigns: List of campaign data with metrics
            total_budget: Total budget to allocate
            min_budget: Minimum budget per campaign

        Returns:
            List of budget change suggestions
        """
        suggestions = []

        if not campaigns:
            return suggestions

        # Calculate ROAS for each campaign
        campaign_performance = []
        for c in campaigns:
            spend = c.get("spend", 0)
            revenue = c.get("revenue", 0)
            roas = (revenue / spend) if spend > 0 else 0

            campaign_performance.append({
                "campaign": c,
                "roas": roas,
                "current_budget": c.get("daily_budget", 0),
            })

        # Sort by ROAS
        campaign_performance.sort(key=lambda x: x["roas"], reverse=True)

        # Allocate budget proportionally to ROAS
        total_roas = sum(cp["roas"] for cp in campaign_performance if cp["roas"] > 0)

        if total_roas == 0:
            # Equal distribution if no ROAS data
            per_campaign = total_budget / len(campaigns)
            for cp in campaign_performance:
                new_budget = max(per_campaign, min_budget)
                current = cp["current_budget"]
                if abs(new_budget - current) > 1:  # Only suggest if > $1 change
                    suggestions.append({
                        "campaign_name": cp["campaign"].get("name"),
                        "campaign_id": cp["campaign"].get("id"),
                        "current_budget": round(current, 2),
                        "suggested_budget": round(new_budget, 2),
                        "change": round(new_budget - current, 2),
                        "reason": "Equal distribution (no ROAS data)",
                    })
        else:
            # Allocate by ROAS performance
            for cp in campaign_performance:
                if cp["roas"] > 0:
                    allocation_pct = cp["roas"] / total_roas
                    new_budget = max(total_budget * allocation_pct, min_budget)
                else:
                    new_budget = min_budget

                current = cp["current_budget"]
                if abs(new_budget - current) > 1:
                    reason = "High ROAS performer" if cp["roas"] >= self.thresholds.roas_good else (
                        "Scale opportunity" if cp["roas"] >= self.thresholds.roas_min else "Reduce spend, low ROAS"
                    )
                    suggestions.append({
                        "campaign_name": cp["campaign"].get("name"),
                        "campaign_id": cp["campaign"].get("id"),
                        "current_budget": round(current, 2),
                        "suggested_budget": round(new_budget, 2),
                        "change": round(new_budget - current, 2),
                        "roas": round(cp["roas"], 2),
                        "reason": reason,
                    })

        return suggestions

    def get_creative_rotation_candidates(
        self,
        creatives: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Identify creatives that need rotation due to fatigue.

        Args:
            creatives: List of creative data with metrics

        Returns:
            List of creatives needing rotation with reasons
        """
        candidates = []

        for creative in creatives:
            reasons = []

            # Check CTR decline
            ctr = creative.get("ctr", 0)
            if ctr < self.thresholds.ctr_warning:
                reasons.append(f"Low CTR ({ctr:.2f}%)")

            # Check frequency
            frequency = creative.get("frequency", 0)
            if frequency > self.thresholds.frequency_max:
                reasons.append(f"High frequency ({frequency:.1f})")

            # Check performance trend (if available)
            ctr_trend = creative.get("ctr_trend", 0)
            if ctr_trend < -10:  # 10% decline
                reasons.append(f"CTR declining ({ctr_trend:.1f}%)")

            if reasons:
                candidates.append({
                    "creative_id": creative.get("id"),
                    "creative_name": creative.get("name"),
                    "ctr": round(ctr, 2),
                    "frequency": round(frequency, 1),
                    "reasons": reasons,
                    "urgency": "high" if len(reasons) > 1 else "medium",
                })

        return sorted(candidates, key=lambda x: len(x["reasons"]), reverse=True)
