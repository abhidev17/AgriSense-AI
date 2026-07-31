"""
disease_ai.py — DEPRECATED SERVICE

The DiseaseAIService (PyTorch CNN) has been removed.
Disease detection is now handled by Gemini Vision via app/services/gemini.py.

This file is kept to provide:
  - DiseaseDetectionResult (data class, backward compat)
  - TREATMENT_MAP / DEFAULT_DISEASES / VALID_DISEASES (static reference data)

These are NOT imported by the main pipeline anymore.
"""

from typing import Optional

# ─── Crop–Disease compatibility reference (static data, still useful) ─────────

VALID_DISEASES: dict[str, list[str]] = {
    "Tomato": [
        "Early Blight", "Late Blight", "Leaf Mold", "Septoria Leaf Spot",
        "Spider Mites", "Target Spot", "Yellow Leaf Curl Virus",
        "Bacterial Spot", "Healthy",
    ],
    "Potato": ["Early Blight", "Late Blight", "Healthy"],
    "Apple": ["Apple Scab", "Black Rot", "Cedar Apple Rust", "Healthy"],
    "Corn (Maize)": ["Common Rust", "Northern Leaf Blight", "Cercospora Leaf Spot", "Healthy"],
    "Grape": ["Black Rot", "Esca (Black Measles)", "Leaf Blight", "Healthy"],
    "Bell Pepper": ["Bacterial Spot", "Healthy"],
    "Cherry": ["Powdery Mildew", "Healthy"],
    "Peach": ["Bacterial Spot", "Healthy"],
    "Strawberry": ["Leaf Scorch", "Healthy"],
    "Soybean": ["Healthy"],
    "Blueberry": ["Healthy"],
    "Raspberry": ["Healthy"],
    "Squash": ["Powdery Mildew", "Healthy"],
}

# ─── Data class preserved for backward compatibility ──────────────────────────


class DiseaseDetectionResult:
    """Lightweight data holder. No longer produced by a CNN service."""

    def __init__(
        self,
        name: str,
        confidence: float,
        severity: str = "unknown",
        affected_area_percent: float = 0.0,
        treatment_recommendations: Optional[list[str]] = None,
    ) -> None:
        self.name = name
        self.confidence = confidence
        self.severity = severity
        self.affected_area_percent = affected_area_percent
        self.treatment_recommendations = treatment_recommendations or []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "confidence": self.confidence,
            "confidence_percent": f"{self.confidence * 100:.1f}%",
            "severity": self.severity,
            "affected_area_percent": self.affected_area_percent,
        }
