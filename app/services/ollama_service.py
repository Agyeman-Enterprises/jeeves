from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, Generator, Optional

import requests
from requests import Response

LOGGER = logging.getLogger(__name__)


class OllamaServiceError(RuntimeError):
    """Raised when the Ollama service cannot fulfill a request."""


class OllamaService:
    """Thin HTTP client around the local Ollama instance."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.default_model = default_model or os.getenv("OLLAMA_MODEL", "qwen2.5:32b")
        # Disabled in cloud environments (Railway/Render/Fly) — Claude handles all inference.
        # Set OLLAMA_ENABLED=true explicitly to force-enable even in cloud.
        _is_cloud = bool(
            os.getenv("RAILWAY_ENVIRONMENT")
            or os.getenv("RENDER")
            or os.getenv("FLY_APP_NAME")
        )
        self._enabled = os.getenv("OLLAMA_ENABLED", "false" if _is_cloud else "true").lower() == "true"
        if not self._enabled:
            LOGGER.info("OllamaService disabled (cloud environment or OLLAMA_ENABLED=false)")
        self.timeout = timeout
        self.max_retries = max(1, max_retries)

    # Public API -----------------------------------------------------------------
    def health(self) -> bool:
        """Quick check to confirm Ollama is reachable."""
        if not self._enabled:
            return False
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=3)
            response.raise_for_status()
            return True
        except Exception as exc:
            LOGGER.warning("Ollama health check failed: %s", exc)
            return False

    def has_models(self) -> bool:
        """Return True when at least one model is available in Ollama."""
        if not self._enabled:
            return False
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return bool(response.json().get("models"))
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> str | Generator[str, None, None]:
        """
        Generate text from Ollama.

        Args:
            prompt: User prompt to send to the model.
            system_prompt: Optional system instructions to prepend.
            model: Override the default model name.
            options: Extra parameters (e.g., temperature, top_p).
            stream: When True, yields chunks instead of a single string.
        """
        if not self._enabled:
            raise OllamaServiceError("OllamaService is disabled in this environment")
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "model": model or self.default_model,
            "stream": stream,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if options:
            payload["options"] = options

        if stream:
            return self._streaming_request(payload)
        return self._standard_request(payload)

    # Internal helpers -----------------------------------------------------------
    def _standard_request(self, payload: Dict[str, Any]) -> str:
        response = self._post_with_retry("/api/generate", payload, stream=False)
        data = response.json()
        if "response" not in data:
            raise OllamaServiceError(f"Unexpected response: {data}")
        return data["response"]

    def _streaming_request(self, payload: Dict[str, Any]) -> Generator[str, None, None]:
        response = self._post_with_retry("/api/generate", payload, stream=True)
        for line in response.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode("utf-8"))
                if "response" in chunk:
                    yield chunk["response"]
            except json.JSONDecodeError:  # pragma: no cover - defensive
                LOGGER.debug("Skipping malformed chunk from Ollama: %s", line)

    def _post_with_retry(
        self, endpoint: str, payload: Dict[str, Any], stream: bool
    ) -> Response:
        url = f"{self.base_url}{endpoint}"
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    stream=stream,
                )
                response.raise_for_status()
                return response
            except Exception as exc:
                last_exc = exc
                LOGGER.warning(
                    "Ollama request failed (attempt %s/%s): %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(2 ** (attempt - 1))

        raise OllamaServiceError(
            f"Ollama request failed after {self.max_retries} attempts: {last_exc}"
        )


