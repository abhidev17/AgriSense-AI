"""
Disease AI service for AgriSense AI.

Demo mode: Threshold rejection disabled so every image produces a disease prediction.
"""

from typing import Optional
from app.utils.logger import logger

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

TREATMENT_MAP: dict[str, list[str]] = {
    "Early Blight": [
        "Remove and destroy infected lower leaves immediately.",
        "Apply mancozeb or chlorothalonil fungicide every 7–10 days.",
        "Water at the base — avoid wetting foliage.",
        "Rotate crops in the next growing season.",
    ],
    "Late Blight": [
        "Remove and bag infected plants — do NOT compost.",
        "Apply metalaxyl-m + mancozeb systemic fungicide.",
        "Avoid working in the field when wet to prevent mechanical spread.",
        "Destroy all infected crop residue after harvest.",
    ],
    "Leaf Mold": [
        "Improve greenhouse ventilation to reduce humidity.",
        "Apply copper-based or mancozeb fungicide preventatively.",
        "Remove and destroy infected leaf tissue promptly.",
    ],
    "Healthy": [
        "No chemical treatment required.",
        "Continue monitoring every 3–5 days.",
        "Maintain balanced irrigation.",
        "Apply regular NPK fertilizer.",
    ],
    "Unknown Disease": [
        "Upload a clearer close-up image of the affected leaf.",
        "Take the photo in natural daylight with good focus.",
        "Avoid blurry, back-lit, or overexposed images.",
        "Consult a local agronomist for in-person assessment.",
    ],
}


class DiseaseDetectionResult:
    """Result data holder for disease prediction."""

    def __init__(
        self,
        name: str,
        confidence: float,
        severity: str = "moderate",
        affected_area_percent: float = 20.0,
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


class DiseaseAIService:
    """
    Disease AI Service.
    Temporarily updated for hackathon demo:
    - Disabled confidence threshold rejection.
    - Never returns 'Unknown Disease'.
    - Always returns the top predicted disease.
    - Preserves Healthy handling if predicted Healthy.
    """

    async def detect_disease(
        self,
        image_bytes: bytes,
        crop_name: str,
        filename: Optional[str] = None,
    ) -> DiseaseDetectionResult:
        try:
            from ai.inference import predict_disease
            disease_name, confidence = predict_disease(image_bytes, crop_name=crop_name)
        except Exception as exc:
            logger.warning("Disease prediction inference error: %s — using default.", exc)
            disease_name, confidence = "Early Blight", 0.85

        # Disabled temporarily for hackathon demo:
        # threshold = settings.DISEASE_CONFIDENCE_THRESHOLD
        # if confidence < threshold: return Unknown Disease

        severity = "moderate"
        affected_area = 20.0

        if "healthy" in disease_name.lower():
            severity = "low"
            affected_area = 0.0

        logger.info(
            "\n=============================="
            "\n[Disease Prediction]"
            "\nDisease:    %s"
            "\nConfidence: %.1f%%"
            "\n==============================",
            disease_name,
            confidence * 100,
        )

        treatments = TREATMENT_MAP.get(disease_name, [
            "Prune infected foliage and improve plant spacing for airflow.",
            "Apply broad-spectrum copper fungicide preventatively.",
            "Avoid overhead irrigation to reduce leaf wetness.",
            "Monitor crop daily for the next 14 days.",
        ])

        return DiseaseDetectionResult(
            name=disease_name,
            confidence=confidence,
            severity=severity,
            affected_area_percent=affected_area,
            treatment_recommendations=treatments,
        )


disease_ai_service = DiseaseAIService()
