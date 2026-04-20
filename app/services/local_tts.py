"""
Local TTS service using Piper TTS.
Provides free, local text-to-speech synthesis with personality tone markers.
"""

import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)

# Default model directory
PIPER_MODEL_DIR = Path(os.getenv("PIPER_MODEL_DIR", "data/piper_models"))
TTS_OUTPUT_DIR = Path(os.getenv("TTS_OUTPUT_DIR", "data/tts_output"))

# Default English voice - clear, calm, assistant-like
# Using en_US-amy-medium for better quality
DEFAULT_VOICE = "en_US-amy-medium"
DEFAULT_VOICE_URL = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/{DEFAULT_VOICE}.onnx"
DEFAULT_CONFIG_URL = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/{DEFAULT_VOICE}.onnx.json"

# Global model cache
_loaded_model = None
_model_path: Optional[Path] = None
_config_path: Optional[Path] = None


def _download_model() -> tuple[Optional[Path], Optional[Path]]:
    """Download Piper model files if they don't exist."""
    import requests
    
    PIPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    model_path = PIPER_MODEL_DIR / f"{DEFAULT_VOICE}.onnx"
    config_path = PIPER_MODEL_DIR / f"{DEFAULT_VOICE}.onnx.json"
    
    # Download model if needed
    if not model_path.exists():
        LOGGER.info(f"Downloading Piper model: {DEFAULT_VOICE}")
        try:
            response = requests.get(DEFAULT_VOICE_URL, timeout=300)
            response.raise_for_status()
            model_path.write_bytes(response.content)
            LOGGER.info(f"Downloaded model to: {model_path}")
        except Exception as e:
            LOGGER.error(f"Failed to download model: {e}")
            return None, None
    
    # Download config if needed
    if not config_path.exists():
        LOGGER.info(f"Downloading Piper config: {DEFAULT_VOICE}")
        try:
            response = requests.get(DEFAULT_CONFIG_URL, timeout=60)
            response.raise_for_status()
            config_path.write_bytes(response.content)
            LOGGER.info(f"Downloaded config to: {config_path}")
        except Exception as e:
            LOGGER.error(f"Failed to download config: {e}")
            return None, None
    
    return model_path, config_path


def _infer_tone_from_text(text: str) -> str:
    """
    Infer tone from text content for personality markers.
    Returns tone variant name or 'baseline'.
    """
    text_lower = text.lower()
    
    # Medical/clinical keywords
    if any(kw in text_lower for kw in ["patient", "appointment", "diagnosis", "clinical", "medical", "solopractice", "amion"]):
        return "clinical"
    
    # Analytical/strategic keywords
    if any(kw in text_lower for kw in ["analysis", "strategy", "data", "metrics", "forecast", "insight"]):
        return "analytical"
    
    # Creative keywords
    if any(kw in text_lower for kw in ["creative", "design", "story", "character", "world", "game", "brand"]):
        return "creative"
    
    # Urgent/busy context (executive mode)
    if any(kw in text_lower for kw in ["urgent", "asap", "immediately", "quick", "brief"]):
        return "focused"
    
    # Supportive context
    if any(kw in text_lower for kw in ["sorry", "apologize", "help", "support", "concern"]):
        return "supportive"
    
    return "baseline"


def _apply_personality_tone_markers(text: str, tone: Optional[str] = None) -> str:
    """
    Apply personality tone markers to text for TTS.
    Removes markers before synthesis (Piper doesn't support SSML),
    but logs them for future SSML-capable TTS engines.
    """
    if not tone:
        tone = _infer_tone_from_text(text)
    
    # Create tone marker
    tone_marker = f"<tone:{tone}>"
    
    # Log tone for debugging
    LOGGER.debug(f"Applying tone marker: {tone_marker} to text (length: {len(text)})")
    
    # For now, we prepend the marker but remove it before synthesis
    # In the future, if we switch to SSML-capable TTS, we can use these markers
    # For Piper, we just log and return clean text
    return text


def synthesize_to_wav(text: str, output_path: Optional[str] = None, tone: Optional[str] = None) -> str:
    """
    Synthesizes text to a WAV file using Piper TTS with personality tone markers.
    
    Args:
        text: Text to synthesize
        output_path: Optional output path. If not provided, generates a unique filename.
        tone: Optional tone variant (baseline, focused, supportive, clinical, analytical, creative)
    
    Returns:
        Absolute path to the generated WAV file.
    
    Raises:
        Exception on failure.
    """
    import subprocess
    import shutil
    
    global _model_path, _config_path
    
    # Apply personality tone markers (for logging/future SSML support)
    text_with_tone = _apply_personality_tone_markers(text, tone)
    
    # Remove any tone markers before synthesis (Piper doesn't support SSML)
    clean_text = re.sub(r"<tone:[^>]+>", "", text_with_tone).strip()
    
    # Ensure model is downloaded
    if not _model_path or not _model_path.exists():
        _model_path, _config_path = _download_model()
        if not _model_path or not _config_path:
            raise RuntimeError("Failed to download or locate Piper model")
    
    # Generate output path if not provided
    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not output_path:
        output_path = str(TTS_OUTPUT_DIR / f"jarvis-{uuid.uuid4().hex}.wav")
    else:
        output_path = str(Path(output_path).absolute())
    
    # Try to use piper-tts Python package first
    global _loaded_model
    try:
        import piper_tts
        # Try using the Python API
        if _loaded_model is None:
            LOGGER.info(f"Loading Piper model: {_model_path}")
            try:
                _loaded_model = piper_tts.PiperVoice.load(str(_model_path))
                LOGGER.info("Piper model loaded successfully")
            except Exception as e:
                LOGGER.warning(f"Failed to load model via Python API: {e}, trying CLI...")
                _loaded_model = None
        
        if _loaded_model:
            LOGGER.debug(f"Synthesizing text (length: {len(clean_text)}) to: {output_path}")
            with open(output_path, "wb") as f:
                _loaded_model.synthesize(clean_text, f)
            LOGGER.debug(f"Generated audio file: {output_path}")
            return output_path
    except ImportError:
        pass  # Fall through to CLI method
    except Exception as e:
        LOGGER.warning(f"Python API failed: {e}, trying CLI...")
    
    # Fallback to CLI method
    piper_binary = shutil.which("piper") or shutil.which("piper-tts")
    if not piper_binary:
        raise RuntimeError(
            "piper-tts not available. Install with: pip install piper-tts\n"
            "Or ensure 'piper' binary is in PATH."
        )
    
    # Use piper CLI
    cmd = [
        piper_binary,
        "--model", str(_model_path),
        "--output_file", output_path,
    ]
    if _config_path and _config_path.exists():
        cmd.extend(["--config", str(_config_path)])
    
    try:
        LOGGER.debug(f"Synthesizing via CLI: {output_path}")
        result = subprocess.run(
            cmd,
            input=clean_text.encode("utf-8"),
            check=True,
            capture_output=True,
            timeout=30
        )
        LOGGER.debug(f"Generated audio file: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        LOGGER.error(f"Piper CLI failed: {e.stderr.decode() if e.stderr else str(e)}")
        if os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except:
                pass
        raise RuntimeError(f"Piper synthesis failed: {e}")
    except Exception as e:
        LOGGER.error(f"Piper synthesis error: {e}")
        if os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except:
                pass
        raise

