import os
import tempfile
from typing import Optional

try:
    import edge_tts
    _EDGE_TTS_AVAILABLE = True
except ImportError:
    edge_tts = None  # type: ignore[assignment]
    _EDGE_TTS_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    _WHISPER_AVAILABLE = True
except ImportError:
    WhisperModel = None  # type: ignore[assignment,misc]
    _WHISPER_AVAILABLE = False


class VoiceService:
    """
    Handles Speech-to-Text (STT) and Text-to-Speech (TTS) for Jarvis.
    """

    def __init__(self):
        self.use_local_stt = os.getenv("USE_LOCAL_STT", "True") == "True"
        self.use_local_tts = os.getenv("USE_LOCAL_TTS", "False") == "True"

        self.whisper_model: Optional[WhisperModel] = None
        if self.use_local_stt and _WHISPER_AVAILABLE:
            model_size = os.getenv("LOCAL_STT_MODEL", "medium")
            device = "cuda" if os.getenv("CUDA_AVAILABLE", "False") == "True" else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            self.whisper_model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )

        # default TTS voice (Edge)
        self.edge_voice = os.getenv("EDGE_TTS_VOICE", "en-US-JennyNeural")

    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Speech → Text
        """
        # Local faster-whisper
        if self.use_local_stt and self.whisper_model is not None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name

            try:
                segments, _ = self.whisper_model.transcribe(temp_path)
                return " ".join(seg.text.strip() for seg in segments)
            finally:
                os.unlink(temp_path)

        # Fallback: OpenAI Whisper API
        from openai import OpenAI
        client = OpenAI()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    file=("audio.wav", audio_file),
                    model="whisper-1",
                )
            return result.text
        finally:
            os.unlink(temp_path)

    async def synthesize(self, text: str) -> bytes:
        """
        Text → Speech
        Currently uses Edge TTS by default.
        """
        # TODO: plug in local TTS (Coqui XTTS) when ready
        if self.use_local_tts:
            # placeholder for Coqui XTTS
            # TODO: Implement local TTS with Coqui XTTS
            pass

        communicate = edge_tts.Communicate(text, self.edge_voice)

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
            
            # Read the file after writing is complete
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            return audio_data
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

