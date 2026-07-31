"""
crop_ai.py — DEPRECATED SERVICE

The CropAIService (PyTorch CNN) has been removed.
Crop detection is now handled by Gemini Vision via app/services/gemini.py.

This file is kept only to avoid import errors in any legacy code.
CropDetectionResult is preserved as a passive data class.
"""

# ─── Data class preserved for backward compatibility ──────────────────────────


class CropDetectionResult:
    """Lightweight data holder. No longer produced by a CNN service."""

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
