"""
Enhanced Wake-Word Listener
Listens for "Hey Jarvis" or "Hey Jarv", then captures speech and processes it.
"""

import io
import logging
import os
import time
import wave
from pathlib import Path
from typing import Optional

import pyaudio
import requests

LOGGER = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.getenv("JARVIS_BACKEND_URL", "http://localhost:8000")
WAKE_WORDS = ["hey jarvis", "hey jarv"]
LISTEN_DURATION = 10  # seconds to listen after wake-word
SILENCE_THRESHOLD = 500  # Adjust based on mic sensitivity
SILENCE_DURATION = 2.0  # seconds of silence before stopping


class WakeWordListener:
    """Enhanced wake-word listener with speech capture."""
    
    def __init__(self):
        self.is_listening = False
        self.mic: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.oww_model = None
        self._setup_openwakeword()
    
    def _setup_openwakeword(self):
        """Initialize OpenWakeWord model."""
        try:
            from openwakeword.model import Model
            self.oww_model = Model(inference_framework="onnx")
            LOGGER.info(f"OpenWakeWord loaded. Available models: {list(self.oww_model.models.keys())}")
        except ImportError:
            LOGGER.error("openwakeword not installed. Install with: pip install openwakeword")
            raise
        except Exception as e:
            LOGGER.error(f"Failed to load OpenWakeWord: {e}")
            raise
    
    def _setup_audio(self):
        """Initialize audio capture."""
        try:
            self.mic = pyaudio.PyAudio()
            self.stream = self.mic.open(
                rate=16000,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=1280
            )
            LOGGER.info("Audio stream initialized (16kHz, mono, 16-bit)")
        except Exception as e:
            LOGGER.error(f"Failed to initialize audio: {e}")
            raise
    
    def _detect_wake_word(self, audio_data: bytes) -> bool:
        """Check if wake-word is detected in audio chunk."""
        if not self.oww_model:
            return False
        
        try:
            prediction = self.oww_model.predict(audio_data)
            for model_name in self.oww_model.models.keys():
                if "jarvis" in model_name.lower() or "jarv" in model_name.lower():
                    if prediction[model_name] >= 0.5:
                        LOGGER.info(f"Wake-word detected! ({model_name}, confidence: {prediction[model_name]:.2f})")
                        return True
        except Exception as e:
            LOGGER.debug(f"Wake-word detection error: {e}")
        
        return False
    
    def _capture_speech(self) -> Optional[bytes]:
        """Capture speech after wake-word detection."""
        if not self.stream:
            return None
        
        LOGGER.info("Listening for speech...")
        frames = []
        silence_start = None
        start_time = time.time()
        
        while time.time() - start_time < LISTEN_DURATION:
            try:
                chunk = self.stream.read(1280, exception_on_overflow=False)
                frames.append(chunk)
                
                # Check for silence
                import struct
                audio_data = struct.unpack(f"{len(chunk)//2}h", chunk)
                max_amplitude = max(abs(sample) for sample in audio_data)
                
                if max_amplitude < SILENCE_THRESHOLD:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= SILENCE_DURATION:
                        LOGGER.info("Silence detected, stopping capture")
                        break
                else:
                    silence_start = None
                
            except Exception as e:
                LOGGER.error(f"Error capturing audio: {e}")
                break
        
        if not frames:
            return None
        
        # Convert to WAV format
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)
            wav_file.writeframes(b''.join(frames))
        
        return wav_buffer.getvalue()
    
    def _process_speech(self, audio_data: bytes) -> Optional[str]:
        """Send audio to backend for transcription and processing."""
        try:
            # Transcribe
            files = {'file': ('audio.wav', audio_data, 'audio/wav')}
            response = requests.post(
                f"{BACKEND_URL}/api/voice/transcribe",
                files=files,
                timeout=30
            )
            response.raise_for_status()
            transcription = response.json().get("text", "")
            
            if not transcription:
                LOGGER.warning("No transcription returned")
                return None
            
            LOGGER.info(f"Transcribed: {transcription}")
            
            # Send to query endpoint
            query_response = requests.post(
                f"{BACKEND_URL}/query",
                json={"query": transcription},
                timeout=60
            )
            query_response.raise_for_status()
            result = query_response.json()
            
            reply_text = result.get("content", "")
            if not reply_text:
                reply_text = result.get("reply", "")
            
            LOGGER.info(f"Jarvis reply: {reply_text[:100]}...")
            
            # Get TTS audio
            tts_response = requests.post(
                f"{BACKEND_URL}/api/voice/speak",
                json={"text": reply_text},
                timeout=30
            )
            tts_response.raise_for_status()
            
            # Save audio to temp file and play
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(tts_response.content)
                tmp_path = tmp.name
            
            # Play audio (platform-specific)
            self._play_audio(tmp_path)
            
            # Cleanup
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            return reply_text
            
        except Exception as e:
            LOGGER.error(f"Error processing speech: {e}")
            return None
    
    def _play_audio(self, audio_path: str):
        """Play audio file (platform-specific)."""
        try:
            import platform
            system = platform.system()
            
            if system == "Windows":
                import winsound
                winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            elif system == "Darwin":  # macOS
                import subprocess
                subprocess.run(["afplay", audio_path], check=True)
            else:  # Linux
                import subprocess
                subprocess.run(["aplay", audio_path], check=True)
        except Exception as e:
            LOGGER.warning(f"Could not play audio: {e}")
    
    def start(self):
        """Start listening for wake-words."""
        if self.is_listening:
            LOGGER.warning("Already listening")
            return
        
        self._setup_audio()
        self.is_listening = True
        
        LOGGER.info("=" * 60)
        LOGGER.info("Wake-Word Listener Started")
        LOGGER.info(f"Listening for: {', '.join(WAKE_WORDS)}")
        LOGGER.info("=" * 60)
        
        try:
            while self.is_listening:
                # Read audio chunk
                audio_chunk = self.stream.read(1280, exception_on_overflow=False)
                
                # Check for wake-word
                if self._detect_wake_word(audio_chunk):
                    # Capture speech
                    speech_audio = self._capture_speech()
                    if speech_audio:
                        # Process in a separate thread to avoid blocking
                        import threading
                        thread = threading.Thread(
                            target=self._process_speech,
                            args=(speech_audio,),
                            daemon=True
                        )
                        thread.start()
                    
                    # Brief pause to avoid re-triggering
                    time.sleep(1.0)
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            LOGGER.info("Shutting down...")
        except Exception as e:
            LOGGER.exception(f"Error in wake-word loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop listening."""
        self.is_listening = False
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        if self.mic:
            try:
                self.mic.terminate()
            except:
                pass
            self.mic = None
        
        LOGGER.info("Wake-word listener stopped")


def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    listener = WakeWordListener()
    try:
        listener.start()
    except Exception as e:
        LOGGER.error(f"Failed to start listener: {e}")
        raise


if __name__ == "__main__":
    main()

