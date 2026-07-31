"""
Crop AI service for AgriSense AI.

PLACEHOLDER IMPLEMENTATION
──────────────────────────
This module defines the interface for crop detection from plant images.
The actual AI model integration (e.g. a fine-tuned vision model or
Google Cloud Vision) will be added here later.

Current behaviour: returns realistic mock data so the full API pipeline
can be exercised end-to-end without a real model.
"""

import random
from typing import Optional

from app.utils.logger import logger

# ─── Supported crops (will be the model's class labels) ───────────────────────
SUPPORTED_CROPS: list[str] = [
    "Tomato",
    "Potato",
    "Corn (Maize)",
    "Wheat",
    "Rice",
    "Bell Pepper",
    "Apple",
    "Grape",
    "Strawberry",
    "Peach",
    "Cherry",
    "Soybean",
    "Squash",
    "Blueberry",
    "Raspberry",
    "Orange",
]


class CropDetectionResult:
    """
    Data class holding the output of a crop detection inference call.

    Attributes:
        name:       Detected crop name.
        confidence: Detection confidence in [0, 1].
        source:     'ai' when auto-detected; 'user' when supplied by the caller.
    """

    def __init__(self, name: str, confidence: float, source: str = "ai") -> None:
        self.name = name
        self.confidence = round(confidence, 4)
        self.source = source

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "confidence": self.confidence,
            "confidence_percent": f"{round(self.confidence * 100, 1)}%",
            "source": self.source,
        }


class CropAIService:
    """
    Service responsible for identifying the crop species in a plant image.

    Integration points (TODO when model is ready):
      - Load model weights from a GCS bucket / local path on startup.
      - Replace the mock body of ``detect_crop`` with real inference.
      - Return top-k predictions with per-class confidence scores.
    """

    def __init__(self) -> None:
        # TODO: Load model checkpoint here
        # self.model = load_model(settings.CROP_MODEL_PATH)
        logger.info("CropAIService initialised (mock mode).")

    async def detect_crop(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
    ) -> CropDetectionResult:
        """
        Identify the crop species in the given image.

        Args:
            image_bytes: Raw bytes of the validated plant image.
            filename:    Original filename (optional; used for logging).

        Returns:
            CropDetectionResult with name, confidence, and source='ai'.

        TODO:
            Replace the mock block below with real model inference:

            .. code-block:: python

                tensor = preprocess(image_bytes)
                logits = self.model(tensor)
                probs  = softmax(logits)
                top_idx = probs.argmax()
                return CropDetectionResult(
                    name=LABEL_MAP[top_idx],
                    confidence=float(probs[top_idx]),
                )
        """
        logger.debug(
            "detect_crop() called — file=%s, bytes=%d (mock mode)",
            filename,
            len(image_bytes),
        )

        # ── MOCK RESPONSE ─────────────────────────────────────────────────────
        # Simulates a confident Tomato detection (the most common demo crop).
        # Confidence is randomised slightly to feel realistic.
        mock_name = "Tomato"
        mock_confidence = round(random.uniform(0.94, 0.99), 4)

        logger.info(
            "Crop detected (mock): %s @ %.1f%%",
            mock_name,
            mock_confidence * 100,
        )
        return CropDetectionResult(name=mock_name, confidence=mock_confidence)

    async def get_supported_crops(self) -> list[str]:
        """
        Return the list of crops the model can identify.
        In production this will be derived from the model's class-label map.
        """
        return SUPPORTED_CROPS


# ─── Singleton ────────────────────────────────────────────────────────────────
crop_ai_service = CropAIService()
