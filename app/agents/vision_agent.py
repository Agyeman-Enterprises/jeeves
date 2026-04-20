"""
VisionAgent — JARVIS's eyes.
Can analyze screenshots, images, documents, and live screen captures.
Uses Claude Vision API (claude-opus-4-6) or the existing VisionService as fallback.
"""
from __future__ import annotations

import base64
import logging
import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from app.agents.base import AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)

# ── Optional heavy imports (graceful degradation) ─────────────────────────────
try:
    import anthropic as _anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _anthropic = None  # type: ignore[assignment]
    _ANTHROPIC_AVAILABLE = False

try:
    from PIL import ImageGrab, Image as _PILImage
    _PIL_AVAILABLE = True
except ImportError:
    ImageGrab = None  # type: ignore[assignment]
    _PILImage = None  # type: ignore[assignment]
    _PIL_AVAILABLE = False

try:
    import mss as _mss
    _MSS_AVAILABLE = True
except ImportError:
    _mss = None  # type: ignore[assignment]
    _MSS_AVAILABLE = False


class VisionAgent(BaseAgent):
    """JARVIS vision capabilities — screen capture, OCR, image analysis."""

    name = "VisionAgent"
    description = (
        "Gives JARVIS eyes — analyzes screenshots, images, and documents using "
        "Claude Vision AI. Can capture the current screen and describe what it sees."
    )
    capabilities = [
        "Analyze any image or screenshot",
        "Capture the current screen and describe it",
        "Extract text from document photos (OCR)",
        "Answer questions about images",
        "Read all visible text on screen",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._claude: Optional[Any] = None
        if _ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self._claude = _anthropic.Anthropic(api_key=api_key)
            else:
                LOGGER.warning("VisionAgent: ANTHROPIC_API_KEY not set — Claude Vision disabled")
        else:
            LOGGER.warning("VisionAgent: anthropic package not installed — Claude Vision disabled")

    # ── Public agent interface ──────────────────────────────────────────────

    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Route vision queries to the correct sub-handler."""
        context = context or {}
        q = query.lower()

        # Determine intent from query
        if any(kw in q for kw in ["screen", "display", "monitor", "looking at", "what am i"]):
            result = self.capture_and_analyze(query)
        elif any(kw in q for kw in ["read text", "extract text", "ocr", "text on screen"]):
            result = self.read_screen_text()
        elif any(kw in q for kw in ["document", "paper", "page", "pdf"]):
            image_path = context.get("image_path") or context.get("image_url")
            if image_path:
                result = self.read_document_image(image_path)
            else:
                result = self.capture_and_analyze("Extract all text from this document or screen.")
        else:
            # Generic image analysis — try to use context-provided image
            image_path = context.get("image_path") or context.get("image_url")
            if image_path:
                result = self.analyze_image(image_path, query)
            else:
                result = self.capture_and_analyze(query)

        if isinstance(result, dict) and "error" in result:
            return AgentResponse(
                agent=self.name,
                content=result["error"],
                status="error",
            )

        content = result.get("description") or result.get("text") or str(result)
        return AgentResponse(
            agent=self.name,
            content=content,
            data=result,
            status="success",
        )

    # ── Core vision methods ─────────────────────────────────────────────────

    def analyze_screenshot(self, image_path_or_url: str) -> Dict[str, Any]:
        """Describe what's visible in a screenshot file or URL."""
        try:
            image_bytes = self._load_image_bytes(image_path_or_url)
            if image_bytes is None:
                return {"error": f"Could not load image from: {image_path_or_url}"}
            description = self._analyze_with_claude(
                image_bytes, "Describe in detail what you see in this screenshot."
            )
            return {
                "description": description,
                "source": image_path_or_url,
                "type": "screenshot_analysis",
            }
        except Exception as exc:
            LOGGER.exception("analyze_screenshot failed: %s", exc)
            return {"error": f"Screenshot analysis failed: {exc}"}

    def read_document_image(self, image_path: str) -> Dict[str, Any]:
        """OCR — extract all text and data from a document photo."""
        try:
            image_bytes = self._load_image_bytes(image_path)
            if image_bytes is None:
                return {"error": f"Could not load document image from: {image_path}"}
            text = self._analyze_with_claude(
                image_bytes,
                (
                    "Extract ALL text from this document image. Return the text exactly as it "
                    "appears, preserving layout where possible. Include all headings, body text, "
                    "table data, dates, numbers, and signatures."
                ),
            )
            return {
                "text": text,
                "description": text,
                "source": image_path,
                "type": "document_ocr",
            }
        except Exception as exc:
            LOGGER.exception("read_document_image failed: %s", exc)
            return {"error": f"Document OCR failed: {exc}"}

    def analyze_image(self, image_path_or_url: str, question: str) -> Dict[str, Any]:
        """Answer a specific question about an image."""
        try:
            image_bytes = self._load_image_bytes(image_path_or_url)
            if image_bytes is None:
                return {"error": f"Could not load image from: {image_path_or_url}"}
            answer = self._analyze_with_claude(image_bytes, question)
            return {
                "description": answer,
                "question": question,
                "source": image_path_or_url,
                "type": "image_qa",
            }
        except Exception as exc:
            LOGGER.exception("analyze_image failed: %s", exc)
            return {"error": f"Image analysis failed: {exc}"}

    def capture_and_analyze(self, question: str = "What do you see on screen?", url: Optional[str] = None) -> Dict[str, Any]:
        """Capture a webpage (or screen) then analyze it with the given question."""
        try:
            screenshot_path = self._capture_screen(url=url)
            if screenshot_path is None:
                return {"error": "Screen capture requires a URL in cloud mode. Example: 'screenshot https://example.com'"}
            image_bytes = Path(screenshot_path).read_bytes()
            description = self._analyze_with_claude(image_bytes, question)
            # Clean up temp file
            try:
                Path(screenshot_path).unlink(missing_ok=True)
            except Exception:
                pass
            return {
                "description": description,
                "question": question,
                "type": "screen_capture_analysis",
            }
        except Exception as exc:
            LOGGER.exception("capture_and_analyze failed: %s", exc)
            return {"error": f"Screen capture and analysis failed: {exc}"}

    def read_screen_text(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Extract all readable text from the current screen or a given URL."""
        try:
            screenshot_path = self._capture_screen(url=url)
            if screenshot_path is None:
                return {"error": "Screen capture requires a URL in cloud mode. Example: 'read text from https://example.com'"}
            image_bytes = Path(screenshot_path).read_bytes()
            text = self._analyze_with_claude(
                image_bytes,
                (
                    "Extract ALL readable text from this screenshot. Include every word, "
                    "number, label, button text, menu item, URL, and status message visible. "
                    "Organize by region if helpful (top navigation, main content, sidebar, etc.)."
                ),
            )
            try:
                Path(screenshot_path).unlink(missing_ok=True)
            except Exception:
                pass
            return {
                "text": text,
                "description": text,
                "type": "screen_text_extraction",
            }
        except Exception as exc:
            LOGGER.exception("read_screen_text failed: %s", exc)
            return {"error": f"Screen text extraction failed: {exc}"}

    # ── Internal helpers ────────────────────────────────────────────────────

    def _capture_screen(self, url: Optional[str] = None) -> Optional[str]:
        """Capture a webpage screenshot using Playwright. Returns path to a temp PNG file.
        Falls back to mss/PIL for local screen capture when running on a desktop."""
        # Attempt 1: Playwright (headless browser — works in Docker/cloud)
        if url:
            try:
                from playwright.sync_api import sync_playwright
                tmp = tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False, prefix="jarvis_screen_"
                )
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": 1440, "height": 900})
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    page.screenshot(path=tmp.name, full_page=False)
                    browser.close()
                return tmp.name
            except Exception as exc:
                LOGGER.warning("Playwright URL capture failed: %s", exc)

        # Attempt 2: mss (needs a real display — works on desktop)
        if _MSS_AVAILABLE and _mss is not None:
            try:
                with _mss.mss() as sct:
                    monitor = sct.monitors[0]
                    screenshot = sct.grab(monitor)
                    tmp = tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False, prefix="jarvis_screen_"
                    )
                    _mss.tools.to_png(screenshot.rgb, screenshot.size, output=tmp.name)
                    return tmp.name
            except Exception as exc:
                LOGGER.warning("mss screen capture failed: %s", exc)

        # Attempt 3: PIL ImageGrab (Windows / macOS desktop)
        if _PIL_AVAILABLE and ImageGrab is not None:
            try:
                img = ImageGrab.grab()
                tmp = tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False, prefix="jarvis_screen_"
                )
                img.save(tmp.name, format="PNG")
                return tmp.name
            except Exception as exc:
                LOGGER.warning("PIL ImageGrab capture failed: %s", exc)

        return None

    def _load_image_bytes(self, source: str) -> Optional[bytes]:
        """Load image bytes from a file path or URL."""
        if source.startswith("http://") or source.startswith("https://"):
            try:
                import requests
                resp = requests.get(source, timeout=15)
                resp.raise_for_status()
                return resp.content
            except Exception as exc:
                LOGGER.error("Failed to download image from %s: %s", source, exc)
                return None
        else:
            p = Path(source)
            if p.exists():
                return p.read_bytes()
            LOGGER.error("Image file not found: %s", source)
            return None

    def _analyze_with_claude(self, image_bytes: bytes, question: str) -> str:
        """Send image + question to Claude Vision API and return the text response."""
        if self._claude is None:
            # Fallback to VisionService (CLIP)
            return self._fallback_vision(image_bytes, question)

        try:
            image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
            # Detect media type from magic bytes
            media_type = _detect_media_type(image_bytes)
            message = self._claude.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
                                },
                            },
                            {"type": "text", "text": question},
                        ],
                    }
                ],
            )
            return message.content[0].text
        except Exception as exc:
            LOGGER.exception("Claude Vision API call failed: %s", exc)
            return self._fallback_vision(image_bytes, question)

    def _fallback_vision(self, image_bytes: bytes, question: str) -> str:
        """Fallback to local VisionService (CLIP) when Claude is unavailable."""
        try:
            from app.services.vision_service import vision_service
            return vision_service.process_image(image_bytes, question)
        except Exception as exc:
            LOGGER.error("Fallback vision also failed: %s", exc)
            return (
                "Vision analysis is unavailable. "
                "Set ANTHROPIC_API_KEY to enable Claude Vision, "
                "or install transformers+torch for local vision."
            )


def _detect_media_type(image_bytes: bytes) -> str:
    """Detect image media type from magic bytes."""
    if image_bytes[:4] == b"\x89PNG":
        return "image/png"
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:4] in (b"GIF8", b"GIF9"):
        return "image/gif"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"  # default
