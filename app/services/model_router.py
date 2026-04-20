"""
JARVIS Model Router - Routes tasks to optimal local models
Privacy-first: ALL inference stays local on Ollama
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Optional

from .ollama_service import OllamaService

LOGGER = logging.getLogger(__name__)


class TaskType(Enum):
    """Task categories for model routing"""
    MEDICAL = "medical"          # PHI, clinical reasoning
    CODE = "code"                # Development, debugging
    REASONING = "reasoning"      # Complex analysis, chain-of-thought
    GENERAL = "general"          # Quick queries, chat
    BUSINESS = "business"        # Financial, enterprise data


# Model assignments optimized for 16GB VRAM
MODEL_MAP = {
    TaskType.MEDICAL: os.getenv("OLLAMA_MODEL_MEDICAL", "deepseek-r1:14b"),
    TaskType.CODE: os.getenv("OLLAMA_MODEL_CODE", "codestral:22b"),
    TaskType.REASONING: os.getenv("OLLAMA_MODEL_REASONING", "deepseek-r1:14b"),
    TaskType.GENERAL: os.getenv("OLLAMA_MODEL_GENERAL", "phi-4:14b"),
    TaskType.BUSINESS: os.getenv("OLLAMA_MODEL_BUSINESS", "qwen2.5:14b"),
}

# Fallback if primary model unavailable
FALLBACK_MODEL = os.getenv("OLLAMA_MODEL_FALLBACK", "qwen2.5:14b")


class ModelRouter:
    """Routes requests to optimal local model based on task type"""

    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service or OllamaService()
        self._available_models: set[str] = set()
        self._refresh_available_models()

    def _refresh_available_models(self) -> None:
        """Check which models are actually installed"""
        try:
            import requests
            url = f"{self.ollama.base_url}/api/tags"
            response = requests.get(url, timeout=10)
            if response.ok:
                data = response.json()
                self._available_models = {
                    m["name"] for m in data.get("models", [])
                }
                LOGGER.info(f"Available models: {self._available_models}")
        except Exception as e:
            LOGGER.warning(f"Could not fetch model list: {e}")

    def classify_task(self, prompt: str, context: Optional[str] = None) -> TaskType:
        """Classify task type based on prompt content"""
        prompt_lower = prompt.lower()
        context_lower = (context or "").lower()
        combined = f"{prompt_lower} {context_lower}"

        # Medical/PHI indicators
        medical_keywords = [
            "patient", "diagnosis", "symptom", "medication", "prescription",
            "icd-10", "cpt", "hipaa", "phi", "medical", "clinical", "lab result",
            "vital", "treatment", "prognosis", "chief complaint", "hpi"
        ]
        if any(kw in combined for kw in medical_keywords):
            return TaskType.MEDICAL

        # Code indicators
        code_keywords = [
            "code", "function", "debug", "error", "python", "javascript",
            "typescript", "react", "api", "database", "sql", "git", "deploy",
            "refactor", "implement", "class", "module", "import", "def ", "const "
        ]
        if any(kw in combined for kw in code_keywords):
            return TaskType.CODE

        # Business/finance indicators
        business_keywords = [
            "revenue", "profit", "invoice", "contract", "entity", "llc",
            "budget", "expense", "payroll", "tax", "quarterly", "kpi",
            "subscription", "client", "vendor", "roi"
        ]
        if any(kw in combined for kw in business_keywords):
            return TaskType.BUSINESS

        # Complex reasoning indicators
        reasoning_keywords = [
            "analyze", "compare", "evaluate", "strategy", "plan",
            "pros and cons", "decision", "recommend", "why", "explain how",
            "step by step", "think through"
        ]
        if any(kw in combined for kw in reasoning_keywords):
            return TaskType.REASONING

        return TaskType.GENERAL

    def get_model(self, task_type: TaskType) -> str:
        """Get best available model for task type"""
        preferred = MODEL_MAP.get(task_type, FALLBACK_MODEL)
        
        # Check if preferred model is available
        if preferred in self._available_models:
            return preferred
        
        # Try base name without tag
        base_name = preferred.split(":")[0]
        for model in self._available_models:
            if model.startswith(base_name):
                LOGGER.info(f"Using {model} instead of {preferred}")
                return model
        
        # Last resort: use fallback
        if FALLBACK_MODEL in self._available_models:
            LOGGER.warning(f"Falling back to {FALLBACK_MODEL} for {task_type}")
            return FALLBACK_MODEL
        
        # If nothing matches, return first available
        if self._available_models:
            fallback = next(iter(self._available_models))
            LOGGER.warning(f"Using {fallback} as last resort")
            return fallback
        
        raise RuntimeError("No Ollama models available!")

    def generate(
        self,
        prompt: str,
        *,
        task_type: Optional[TaskType] = None,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        stream: bool = False,
    ):
        """
        Generate response using optimal model for task
        
        Args:
            prompt: User prompt
            task_type: Override auto-classification
            system_prompt: System instructions
            context: Additional context for classification
            stream: Stream response chunks
        """
        # Auto-classify if not specified
        if task_type is None:
            task_type = self.classify_task(prompt, context)
        
        model = self.get_model(task_type)
        LOGGER.info(f"Routing {task_type.value} task to {model}")
        
        return self.ollama.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            stream=stream,
        )


# Singleton instance
_router: Optional[ModelRouter] = None


def get_router() -> ModelRouter:
    """Get or create router singleton"""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
