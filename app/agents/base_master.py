"""
Base Master Agent Class
Base class for all Master (Executive) Agents.
Masters own a domain and coordinate multiple specialists.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class MasterAgent(ABC):
    """
    Base class for all Master (Executive) Agents.
    Masters own a domain (e.g. marketing, finance) and coordinate multiple specialists.
    """

    id: str = "master.base"
    display_name: str = "Base Master"
    domain: str = "generic"
    specialist_ids: List[str] = []

    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        """
        Return a lightweight summary of the master agent (for dashboards, logs, etc.)
        """
        raise NotImplementedError

    @abstractmethod
    def plan(self, objective: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        High-level planning interface. Later phases will use LLMs here.
        """
        raise NotImplementedError

