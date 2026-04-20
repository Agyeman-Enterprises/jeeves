"""
Agent Orchestrator
Routes tasks between Master and Specialist agents.
Production-ready implementation with complete agent registry.
"""

from __future__ import annotations

from typing import Dict, Any, Type

# Master agents
from app.agents.masters.strategy_master import StrategyMaster
from app.agents.masters.finance_master import FinanceMaster
from app.agents.masters.operations_master import OperationsMaster
from app.agents.masters.risk_master import RiskMaster
from app.agents.masters.hr_master import HRMaster
from app.agents.masters.marketing_master import MarketingMaster
from app.agents.masters.seo_master import SEOMaster
from app.agents.masters.creative_master import CreativeMaster
from app.agents.masters.competitive_intel_master import CompetitiveIntelMaster
from app.agents.masters.personal_dev_master import PersonalDevelopmentMaster
from app.agents.masters.engineering_master import EngineeringMaster
from app.agents.masters.ad_master import AdMaster

from app.agents.base_master import MasterAgent
from app.agents.base_specialist import SpecialistAgent

# Advertising specialists
from app.agents.specialists.advertising.analytics import AdAnalyticsSpecialist
from app.agents.specialists.advertising.budget_governor import BudgetGovernorSpecialist
from app.agents.specialists.advertising.experiments import AdExperimentsSpecialist
from app.agents.specialists.advertising.meta_campaigns import MetaCampaignsSpecialist
from app.agents.specialists.advertising.meta_creatives import MetaCreativesSpecialist

# Competitive specialists
from app.agents.specialists.competitive.pricing_positioning import PricingPositioning
from app.agents.specialists.competitive.research_agent import ResearchAgent

# Creative specialists
from app.agents.specialists.creative.animation_agent import AnimationAgent
from app.agents.specialists.creative.creative_music import CreativeMusic
from app.agents.specialists.creative.creative_scriptwriter import CreativeScriptwriter
from app.agents.specialists.creative.creative_voice import CreativeVoice

# Engineering specialists
from app.agents.specialists.engineering.app_builder import AppBuilder
from app.agents.specialists.engineering.code_generator import CodeGenerator
from app.agents.specialists.engineering.ui_ux import UIUX
from app.agents.specialists.engineering.web_dev import WebDev

# HR specialists
from app.agents.specialists.hr.onboarding import Onboarding
from app.agents.specialists.hr.recruiter import Recruiter
from app.agents.specialists.hr.task_assignment import TaskAssignment

# Marketing specialists
from app.agents.specialists.marketing.ad_creative import AdCreative
from app.agents.specialists.marketing.brand_consistency import BrandConsistency
from app.agents.specialists.marketing.content_automation import ContentAutomation
from app.agents.specialists.marketing.copywriter import Copywriter
from app.agents.specialists.marketing.ecom_specialist import EcomSpecialist
from app.agents.specialists.marketing.email_marketer import EmailMarketer
from app.agents.specialists.marketing.sales_strategist import SalesStrategist
from app.agents.specialists.marketing.social_media_manager import SocialMediaManager
from app.agents.specialists.marketing.video_script import VideoScript

# Operations specialists
from app.agents.specialists.operations.customer_support import CustomerSupport
from app.agents.specialists.operations.project_executor import ProjectExecutor
from app.agents.specialists.operations.sop_builder import SOPBuilder
from app.agents.specialists.operations.task_automator import TaskAutomator
from app.agents.specialists.operations.virtual_assistant import VirtualAssistant

# SEO specialists
from app.agents.specialists.seo.competitor_keywords import CompetitorKeywords
from app.agents.specialists.seo.content_gap import ContentGap
from app.agents.specialists.seo.seo_mastermind import SEOMastermind
from app.agents.specialists.seo.web_optimization import WebOptimization

# Strategy specialists
from app.agents.specialists.strategy.business_strategist import BusinessStrategist
from app.agents.specialists.strategy.data_analyst import DataAnalyst
from app.agents.specialists.strategy.research_analyst import ResearchAnalyst
from app.agents.specialists.strategy.scenario_forecaster import ScenarioForecaster

# Wellness specialists
from app.agents.specialists.wellness.dr_a_content_coach import DrAContentCoach
from app.agents.specialists.wellness.furfubu_content_agent import FurfubuContentAgent
from app.agents.specialists.wellness.lifestyle_coach import LifestyleCoach
from app.agents.specialists.wellness.meditation_script import MeditationScript
from app.agents.specialists.wellness.nutrition_coach import NutritionCoach
from app.agents.specialists.wellness.personal_growth_coach import PersonalGrowthCoach
from app.agents.specialists.wellness.soundscape_music import SoundscapeMusic
from app.agents.specialists.wellness.wellness_voice import WellnessVoice


MASTER_REGISTRY: Dict[str, Type[MasterAgent]] = {
    "master.strategy": StrategyMaster,
    "master.finance": FinanceMaster,
    "master.operations": OperationsMaster,
    "master.risk": RiskMaster,
    "master.hr": HRMaster,
    "master.marketing": MarketingMaster,
    "master.seo": SEOMaster,
    "master.creative": CreativeMaster,
    "master.competitive_intel": CompetitiveIntelMaster,
    "master.personal_dev": PersonalDevelopmentMaster,
    "master.engineering": EngineeringMaster,
    "master.advertising": AdMaster,
}

SPECIALIST_REGISTRY: Dict[str, Type[SpecialistAgent]] = {
    # Advertising specialists (AdAI)
    "spec.ads.analytics": AdAnalyticsSpecialist,
    "spec.ads.budget": BudgetGovernorSpecialist,
    "spec.ads.experiments": AdExperimentsSpecialist,
    "spec.ads.meta.campaigns": MetaCampaignsSpecialist,
    "spec.ads.meta.creatives": MetaCreativesSpecialist,

    # Competitive specialists
    "spec.competitive.pricing_positioning": PricingPositioning,
    "spec.competitive.research": ResearchAgent,

    # Creative specialists
    "spec.creative.animation": AnimationAgent,
    "spec.creative.music": CreativeMusic,
    "spec.creative.scriptwriter": CreativeScriptwriter,
    "spec.creative.voice": CreativeVoice,

    # Engineering specialists
    "spec.engineering.app_builder": AppBuilder,
    "spec.engineering.code_generator": CodeGenerator,
    "spec.engineering.ui_ux": UIUX,
    "spec.engineering.web_dev": WebDev,

    # HR specialists
    "spec.hr.onboarding": Onboarding,
    "spec.hr.recruiter": Recruiter,
    "spec.hr.task_assignment": TaskAssignment,

    # Marketing specialists
    "spec.marketing.ad_creative": AdCreative,
    "spec.marketing.brand_consistency": BrandConsistency,
    "spec.marketing.content_automation": ContentAutomation,
    "spec.marketing.penn": Copywriter,
    "spec.marketing.commet": EcomSpecialist,
    "spec.marketing.emmie": EmailMarketer,
    "spec.marketing.milli": SalesStrategist,
    "spec.marketing.soshie": SocialMediaManager,
    "spec.marketing.video_script": VideoScript,

    # Operations specialists
    "spec.operations.customer_support": CustomerSupport,
    "spec.operations.project_executor": ProjectExecutor,
    "spec.operations.sop_builder": SOPBuilder,
    "spec.operations.task_automator": TaskAutomator,
    "spec.operations.virtual_assistant": VirtualAssistant,

    # SEO specialists
    "spec.seo.competitor_keywords": CompetitorKeywords,
    "spec.seo.content_gap": ContentGap,
    "spec.seo.seomi": SEOMastermind,
    "spec.seo.web_optimization": WebOptimization,

    # Strategy specialists
    "spec.strategy.business_strategist": BusinessStrategist,
    "spec.strategy.data_analyst": DataAnalyst,
    "spec.strategy.research_analyst": ResearchAnalyst,
    "spec.strategy.scenario_forecaster": ScenarioForecaster,

    # Wellness specialists
    "spec.wellness.dr_a_content": DrAContentCoach,
    "spec.wellness.furfubu_content": FurfubuContentAgent,
    "spec.wellness.lifestyle_coach": LifestyleCoach,
    "spec.wellness.meditation_script": MeditationScript,
    "spec.wellness.nutrition_coach": NutritionCoach,
    "spec.wellness.personal_growth": PersonalGrowthCoach,
    "spec.wellness.soundscape": SoundscapeMusic,
    "spec.wellness.voice": WellnessVoice,
}


def get_master(master_id: str) -> MasterAgent:
    """
    Get a master agent instance by ID.

    Args:
        master_id: The master agent identifier (e.g., 'master.advertising')

    Returns:
        Instantiated master agent

    Raises:
        KeyError: If master_id is not found in registry
    """
    cls = MASTER_REGISTRY.get(master_id)
    if not cls:
        available = ", ".join(sorted(MASTER_REGISTRY.keys()))
        raise KeyError(f"Unknown master_id: {master_id}. Available: {available}")
    return cls()


def get_specialist(spec_id: str) -> SpecialistAgent:
    """
    Get a specialist agent instance by ID.

    Args:
        spec_id: The specialist agent identifier (e.g., 'spec.ads.analytics')

    Returns:
        Instantiated specialist agent

    Raises:
        KeyError: If spec_id is not found in registry
    """
    cls = SPECIALIST_REGISTRY.get(spec_id)
    if not cls:
        available = ", ".join(sorted(SPECIALIST_REGISTRY.keys()))
        raise KeyError(f"Unknown specialist_id: {spec_id}. Available: {available}")
    return cls()


def list_masters() -> Dict[str, Dict[str, Any]]:
    """
    List all registered master agents with their summaries.

    Returns:
        Dict mapping master_id to agent summary
    """
    result = {}
    for master_id, cls in MASTER_REGISTRY.items():
        instance = cls()
        result[master_id] = instance.get_summary()
    return result


def list_specialists() -> Dict[str, Dict[str, Any]]:
    """
    List all registered specialist agents with their summaries.

    Returns:
        Dict mapping specialist_id to agent summary
    """
    result = {}
    for spec_id, cls in SPECIALIST_REGISTRY.items():
        instance = cls()
        result[spec_id] = instance.get_summary()
    return result


def get_specialists_for_master(master_id: str) -> Dict[str, Type[SpecialistAgent]]:
    """
    Get all specialists that belong to a specific master.

    Args:
        master_id: The master agent identifier

    Returns:
        Dict of specialist_id to specialist class for the given master
    """
    master = get_master(master_id)
    specialist_ids = getattr(master, 'specialist_ids', [])

    return {
        spec_id: SPECIALIST_REGISTRY[spec_id]
        for spec_id in specialist_ids
        if spec_id in SPECIALIST_REGISTRY
    }


def route_to_specialist(
    master_id: str,
    specialist_id: str,
    task_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Core routing entry point: Nexus/Jarvis can call this to send work
    from a master to a specialist.

    Args:
        master_id: The master agent to coordinate the task
        specialist_id: The specialist agent to execute the task
        task_type: Type of task to execute
        payload: Task parameters

    Returns:
        Result dict with master, specialist, task_type, and result
    """
    master = get_master(master_id)
    specialist = get_specialist(specialist_id)

    result = specialist.run_task(task_type, payload)
    return {
        "master": master_id,
        "specialist": specialist_id,
        "task_type": task_type,
        "result": result,
    }


def get_registry_stats() -> Dict[str, Any]:
    """
    Get statistics about the agent registry.

    Returns:
        Dict with master_count, specialist_count, and breakdown by domain
    """
    domains: Dict[str, int] = {}
    for spec_id in SPECIALIST_REGISTRY:
        # Extract domain from spec.domain.name format
        parts = spec_id.split('.')
        if len(parts) >= 2:
            domain = parts[1]
            domains[domain] = domains.get(domain, 0) + 1

    return {
        "master_count": len(MASTER_REGISTRY),
        "specialist_count": len(SPECIALIST_REGISTRY),
        "domains": domains,
    }
