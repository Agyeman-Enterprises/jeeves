from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

AgentContext = Dict[str, Any]


@dataclass
class AgentResponse:
    """Standard response envelope returned by every agent."""

    agent: str
    content: str
    data: Dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    warnings: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Base class that all domain agents must implement."""

    name: str
    description: str
    capabilities: List[str]

    def __init__(
        self,
        *,
        personality: Optional[Dict[str, Any]] = None,
        behavior: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = getattr(self, "name", self.__class__.__name__)
        self.personality: Dict[str, Any] = personality or {}
        self.behavior: Dict[str, Any] = behavior or {}

    @abstractmethod
    def handle(self, query: str, context: Optional[AgentContext] = None) -> AgentResponse:
        """Process an incoming query and return a structured response."""

    def supports(self, query: str) -> bool:
        """Optional heuristic for matching queries to this agent."""
        return False

    def configure_persona(
        self,
        personality: Optional[Dict[str, Any]] = None,
        behavior: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inject global personality + behavior settings."""
        if personality:
            self.personality = personality
        if behavior:
            self.behavior = behavior

    def format_personality(self, content: str, tone: Optional[str] = None) -> str:
        """
        Apply personality tone rules to content.
        
        Args:
            content: The response content to format
            tone: Optional specific tone variant (focused, supportive, clinical, etc.)
        
        Returns:
            Formatted content with personality applied
        """
        if not content:
            return content
        
        # Get tone variant if specified
        tone_variant = None
        if tone and self.personality:
            voice_tone = self.personality.get("voice_tone", {})
            variants = voice_tone.get("variants", {})
            tone_variant = variants.get(tone)
        
        # Apply behavioral rules from behavior profile
        if self.behavior:
            behavioral_rules = self.behavior.get("behavioral_rules", [])
            communication = self.behavior.get("communication", {})
            
            # Remove unwanted phrases
            unwanted_phrases = [
                "Shall I proceed",
                "Would you like me to",
                "As an AI",
                "I am here to assist",
            ]
            
            for phrase in unwanted_phrases:
                content = content.replace(phrase, "")
            
            # Ensure no filler
            if communication.get("avoid_filler", True):
                content = content.replace("  ", " ").strip()
        
        return content.strip()


