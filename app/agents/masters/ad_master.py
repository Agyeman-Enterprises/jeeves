"""
Advertising Master Agent (AdAI)
Coordinates advertising specialists for campaign management, optimization, and analytics.
Replaces PredisAI with automated ad creation, spend optimization, and creative rotation.

Priority companies: MedRx, Bookadoc2u, MyHealthAlly, InkwellPublishing, AccessMD
Monthly spend alert threshold: $150
"""

from app.agents.base_master import MasterAgent
from app.ai.local_llm import run_llm
from typing import Dict, Any, List, Optional


# Priority companies for ad spend allocation
PRIORITY_COMPANIES = [
    'medrx',
    'bookadoc2u',
    'myhealthally',
    'inkwellpublishing',
    'accessmd',
]

# Monthly spend alert threshold (USD)
MONTHLY_SPEND_ALERT_THRESHOLD = 150


class AdMaster(MasterAgent):
    """
    Advertising Master - coordinates ad campaign management across 31 companies.

    Capabilities:
    - Campaign creation from launch specs
    - A/B testing and creative rotation
    - Budget optimization and scaling
    - Performance reporting and analytics
    - Spend anomaly detection
    - Multi-platform support (Meta, Google, TikTok)
    """

    id = "master.advertising"
    display_name = "Advertising Master (AdAI)"
    domain = "advertising"
    specialist_ids = [
        "spec.ads.meta.campaigns",      # Meta campaign management
        "spec.ads.meta.creatives",      # Creative asset management
        "spec.ads.budget",              # Budget governor
        "spec.ads.analytics",           # Performance analytics
        "spec.ads.experiments",         # A/B testing
    ]

    def __init__(self) -> None:
        super().__init__()
        self.priority_companies = PRIORITY_COMPANIES
        self.monthly_spend_threshold = MONTHLY_SPEND_ALERT_THRESHOLD

    def get_summary(self) -> Dict[str, Any]:
        """Return lightweight summary for dashboards."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "domain": self.domain,
            "specialist_count": len(self.specialist_ids),
            "priority_companies": self.priority_companies,
            "monthly_spend_threshold": self.monthly_spend_threshold,
        }

    def plan(self, objective: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        High-level advertising strategy planner.

        Args:
            objective: The advertising goal (e.g., "increase conversions for MedRx")
            context: Additional context (business info, constraints, budget)

        Returns:
            Strategic plan with campaign recommendations
        """
        ctx = context or {}
        business_name = ctx.get('business_name', 'Unknown Business')
        budget = ctx.get('budget', 'not specified')
        platform = ctx.get('platform', 'Meta')

        system_prompt = (
            "You are AdAI, the Advertising Master for Agyeman Enterprises. "
            "You manage ad campaigns across 31 companies with a focus on ROI and efficiency. "
            "Priority companies: MedRx, Bookadoc2u, MyHealthAlly, InkwellPublishing, AccessMD. "
            "Generate strategic, actionable advertising plans."
        )

        user_prompt = f"""
Business: {business_name}
Platform: {platform}
Budget: {budget}
Objective: {objective}

Generate a strategic advertising plan with:
1. Campaign structure (awareness → consideration → conversion)
2. Targeting recommendations
3. Creative direction
4. Budget allocation strategy
5. KPIs and success metrics
6. A/B testing recommendations

Keep recommendations practical and focused on ROI.
"""

        plan_text = run_llm(user_prompt, system_prompt)

        return {
            "master": self.id,
            "objective": objective,
            "business": business_name,
            "platform": platform,
            "strategy": plan_text,
        }

    def is_priority_company(self, company_slug: str) -> bool:
        """Check if a company is in the priority list."""
        normalized = company_slug.lower().replace(' ', '').replace('-', '').replace('_', '')
        return normalized in [c.lower() for c in self.priority_companies]

    def get_recommended_platforms(self, business_vertical: str) -> List[str]:
        """
        Get recommended ad platforms based on business vertical.

        Args:
            business_vertical: Type of business (healthcare, publishing, etc.)

        Returns:
            Ordered list of recommended platforms
        """
        platform_recommendations = {
            'healthcare': ['meta', 'google'],  # Meta for awareness, Google for intent
            'publishing': ['meta', 'tiktok'],  # Social for discovery
            'crypto': ['google'],              # Search intent focus
            'ecommerce': ['meta', 'google', 'tiktok'],  # Multi-platform
            'services': ['google', 'meta'],    # Intent + retargeting
            'default': ['meta', 'google'],
        }

        vertical_key = business_vertical.lower() if business_vertical else 'default'
        return platform_recommendations.get(vertical_key, platform_recommendations['default'])

    def calculate_budget_allocation(
        self,
        total_budget: float,
        companies: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate budget allocation across companies.
        Priority companies get 60% of budget, others split the remaining 40%.

        Args:
            total_budget: Total available ad spend
            companies: List of company dicts with 'slug' and optional 'performance_score'

        Returns:
            Dict mapping company slug to allocated budget
        """
        priority = []
        non_priority = []

        for company in companies:
            slug = company.get('slug', '').lower()
            if self.is_priority_company(slug):
                priority.append(company)
            else:
                non_priority.append(company)

        allocation = {}

        # Priority companies get 60% of budget
        if priority:
            priority_budget = total_budget * 0.6
            per_priority = priority_budget / len(priority)
            for company in priority:
                allocation[company['slug']] = round(per_priority, 2)

        # Non-priority companies split remaining 40%
        if non_priority:
            non_priority_budget = total_budget * 0.4
            per_non_priority = non_priority_budget / len(non_priority)
            for company in non_priority:
                allocation[company['slug']] = round(per_non_priority, 2)

        return allocation
