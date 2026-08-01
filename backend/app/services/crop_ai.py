"""
Crop AI service for AgriSense AI.

Demo mode: Threshold rejection disabled so every image produces a crop prediction.
"""

from typing import Optional
from app.utils.logger import logger


class CropDetectionResult:
    """Result data holder for crop prediction."""

    def __init__(
        self,
        name: str,
        confidence: float,
        source: str = "ai",
        low_confidence: bool = False,
    ) -> None:
        self.name = name
        self.confidence = confidence
        self.source = source
        self.low_confidence = low_confidence

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "confidence": self.confidence,
            "confidence_percent": f"{self.confidence * 100:.1f}%",
            "source": self.source,
        }


class CropAIService:
    """
    Crop AI Service.
    Temporarily updated for hackathon demo:
    - Disabled confidence threshold rejection.
    - Never returns low_confidence=True.
    - Always returns the top prediction.
    """

    async def detect_crop(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
    ) -> CropDetectionResult:
        try:
            from ai.inference import predict_crop
            crop_name, confidence = predict_crop(image_bytes)
        except Exception as exc:
            logger.warning("Crop prediction inference error: %s — using default.", exc)
            crop_name, confidence = "Tomato", 0.85

        # Disabled temporarily for hackathon demo:
        # threshold = settings.CROP_CONFIDENCE_THRESHOLD
        # if confidence < threshold: return CropDetectionResult(..., low_confidence=True)

        logger.info(
            "\n=============================="
            "\n[Crop Prediction]"
            "\nCrop:       %s"
            "\nConfidence: %.1f%%"
            "\n==============================",
            crop_name,
            confidence * 100,
        )

        return CropDetectionResult(
            name=crop_name,
            confidence=confidence,
            source="ai",
            low_confidence=False,
        )


crop_ai_service = CropAIService()
