from __future__ import annotations

import base64
import logging
import os
from io import BytesIO
from typing import Optional

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment, misc]

try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
except ImportError:
    torch = None  # type: ignore[assignment, misc]
    CLIPProcessor = None  # type: ignore[assignment, misc]
    CLIPModel = None  # type: ignore[assignment, misc]

LOGGER = logging.getLogger(__name__)

VISION_MODEL_NAME = os.getenv("VISION_MODEL", "openai/clip-vit-base-patch32")


class VisionService:
    """
    Local vision model for image understanding using CLIP or LLaVA-lite.
    """

    def __init__(self, model_name: str = VISION_MODEL_NAME) -> None:
        self.model_name = model_name
        self.model = None
        self.processor = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the vision model (CLIP by default)."""
        if not CLIPModel or not CLIPProcessor:
            LOGGER.warning(
                "transformers or CLIP not installed. Vision service disabled. "
                "Install with: pip install transformers torch pillow"
            )
            return

        if not Image:
            LOGGER.warning("PIL/Pillow not installed. Vision service disabled.")
            return

        try:
            use_cuda = torch and torch.cuda.is_available()
            device = "cuda" if use_cuda else "cpu"
            LOGGER.info("Loading vision model: %s (device=%s)", self.model_name, device)

            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.model.to(device)
            self.model.eval()

            LOGGER.info("Vision model loaded successfully")
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to load vision model: %s", exc)
            self.model = None
            self.processor = None

    def process_image(self, image_bytes: bytes, query: Optional[str] = None) -> str:
        """
        Process an image and return a description or answer to a query.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)
            query: Optional text query about the image

        Returns:
            Description or answer about the image
        """
        if not self.model or not self.processor or not Image:
            return "Vision model not available. Install transformers, torch, and pillow."

        try:
            # Load image
            image = Image.open(BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")

            if query:
                # Use CLIP for image-text matching
                inputs = self.processor(text=[query], images=image, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits_per_image = outputs.logits_per_image
                    probs = logits_per_image.softmax(dim=1)
                    score = probs[0][0].item()

                if score > 0.5:
                    return f"Yes, the image shows: {query} (confidence: {score:.2%})"
                else:
                    return f"No, the image does not clearly show: {query} (confidence: {1-score:.2%})"
            else:
                # Generate a general description
                # For now, return a simple description
                # TODO: Integrate LLaVA-lite for detailed descriptions
                return "Image processed successfully. For detailed descriptions, use a query like 'What is in this image?'"

        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Vision processing failed: %s", exc)
            return f"Error processing image: {exc}"

    def process_base64_image(self, base64_data: str, query: Optional[str] = None) -> str:
        """Process a base64-encoded image."""
        try:
            # Remove data URL prefix if present
            if "," in base64_data:
                base64_data = base64_data.split(",", 1)[1]

            image_bytes = base64.b64decode(base64_data)
            return self.process_image(image_bytes, query)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to decode base64 image: %s", exc)
            return f"Error decoding image: {exc}"


# Global instance
vision_service = VisionService()

