"""
Base Specialist Agent Class
Base class for Specialist (worker) agents.
Specialists run concrete tasks within a domain, under a MasterAgent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any


class SpecialistAgent(ABC):
    """
    Base class for Specialist (worker) agents.
    Specialists run concrete tasks within a domain, under a MasterAgent.
    """

    id: str = "spec.base"
    display_name: str = "Base Specialist"
    master_id: str = "master.base"
    role: str = "generic"

    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def run_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a domain-specific task. Later phases will attach tools & LLMs.
        """
        raise NotImplementedError

