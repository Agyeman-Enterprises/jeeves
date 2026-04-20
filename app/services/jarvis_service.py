from typing import Dict, Any, Optional
import logging
import re

from app.core.orchestrator import Orchestrator
from app.services.voice_service import VoiceService

LOGGER = logging.getLogger(__name__)


class JarvisService:
    """
    High-level service that orchestrates voice interactions, portfolio queries, and alerts.
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        voice_service: Optional[VoiceService] = None,
    ):
        self.orchestrator = orchestrator
        self.voice = voice_service or VoiceService()

    async def handle_text_query(self, text: str, user_id: str = "default") -> str:
        """
        Main Jarvis brain.
        Routes queries through orchestrator, which will delegate to appropriate agents.
        Business intelligence queries go to NexusAgent (which calls NEXUS APIs).
        """
        # Route through orchestrator - it will handle NexusAgent routing
        response = self.orchestrator.route_query(text, context={})
        if hasattr(response, 'content'):
            return response.content
        return str(response)

    async def handle_voice_interaction(self, audio_bytes: bytes, user_id: str = "default") -> Dict[str, Any]:
        """
        Complete voice interaction: STT → Jarvis → TTS
        """
        # 1. STT
        text = await self.voice.transcribe(audio_bytes)

        # 2. Route through existing Jarvis logic
        response_text = await self.handle_text_query(text=text, user_id=user_id)

        # 3. TTS
        audio_bytes_out = await self.voice.synthesize(response_text)

        return {
            "input_text": text,
            "response_text": response_text,
            "audio_bytes": audio_bytes_out,
        }

