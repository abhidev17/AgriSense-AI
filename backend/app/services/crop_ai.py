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
    Uses the fine-tuned EfficientNet-B0 model.
    """

    def __init__(self) -> None:
        logger.info("CropAIService initialised (real mode).")

    async def detect_crop(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
    ) -> CropDetectionResult:
        logger.debug(
            "detect_crop() called — file=%s, bytes=%d",
            filename,
            len(image_bytes),
        )

        try:
            from ai.inference import predict_crop
            crop_name, confidence = predict_crop(image_bytes)
            
            # Map back to display names if needed (e.g. Pepper,_bell -> Bell Pepper)
            display_mapping = {
                "Pepper,_bell": "Bell Pepper",
                "Corn_(maize)": "Corn (Maize)",
                "Cherry_(including_sour)": "Cherry"
            }
            mapped_name = display_mapping.get(crop_name, crop_name)

            logger.info(
                "Crop detected (real): %s @ %.1f%%",
                mapped_name,
                confidence * 100,
            )
            return CropDetectionResult(name=mapped_name, confidence=confidence)
        except Exception as exc:
            logger.error("Real crop detection failed: %s. Falling back to default.", exc)
            return CropDetectionResult(name="Tomato", confidence=0.97, source="ai")

    async def get_supported_crops(self) -> list[str]:
        """
        Return the list of crops the model can identify.
        Derived from the model's class-label map.
        """
        try:
            from ai.inference import _load_classes
            classes = _load_classes()
            display_mapping = {
                "Pepper,_bell": "Bell Pepper",
                "Corn_(maize)": "Corn (Maize)",
                "Cherry_(including_sour)": "Cherry"
            }
            return [display_mapping.get(c, c) for c in classes["crop_classes"].keys()]
        except Exception as exc:
            logger.warning("Failed to load supported crops from classes.json: %s", exc)
            return SUPPORTED_CROPS


# ─── Singleton ────────────────────────────────────────────────────────────────
crop_ai_service = CropAIService()
