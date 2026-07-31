"""
Disease AI service for AgriSense AI.

PLACEHOLDER IMPLEMENTATION
──────────────────────────
This module defines the interface for plant disease detection from images.
The real model (e.g. PlantVillage-trained CNN or a Vertex AI endpoint)
will be integrated here once the model is ready.

Current behaviour: returns realistic mock data so the full pipeline can
be exercised without a live model.
"""

import random
from typing import Optional

from app.utils.logger import logger

# ─── Known diseases per crop ──────────────────────────────────────────────────
# Map used by mock to return crop-appropriate diseases.
DISEASE_MAP: dict[str, list[str]] = {
    "Tomato": [
        "Early Blight",
        "Late Blight",
        "Leaf Mold",
        "Septoria Leaf Spot",
        "Spider Mites",
        "Target Spot",
        "Yellow Leaf Curl Virus",
        "Bacterial Spot",
        "Healthy",
    ],
    "Potato": [
        "Early Blight",
        "Late Blight",
        "Healthy",
    ],
    "Corn (Maize)": [
        "Cercospora Leaf Spot",
        "Common Rust",
        "Northern Leaf Blight",
        "Healthy",
    ],
    "Apple": [
        "Apple Scab",
        "Black Rot",
        "Cedar Apple Rust",
        "Healthy",
    ],
    "Grape": [
        "Black Rot",
        "Esca (Black Measles)",
        "Leaf Blight",
        "Healthy",
    ],
}

# Default disease list when crop is unknown
DEFAULT_DISEASES: list[str] = [
    "Bacterial Leaf Spot",
    "Powdery Mildew",
    "Downy Mildew",
    "Fungal Blight",
    "Healthy",
]

SEVERITY_LEVELS = ["low", "moderate", "high", "critical"]

# Typical treatment recommendations per disease
TREATMENT_MAP: dict[str, list[str]] = {
    "Early Blight": [
        "Remove and destroy infected leaves immediately.",
        "Apply copper-based fungicide (e.g. Bordeaux mixture) every 7–10 days.",
        "Ensure adequate plant spacing for airflow.",
        "Avoid overhead irrigation; water at the base.",
        "Rotate crops next season to break the disease cycle.",
    ],
    "Late Blight": [
        "Remove and bag all infected plant material — do NOT compost.",
        "Apply mancozeb or chlorothalonil fungicide preventively.",
        "Destroy volunteer potato plants in the vicinity.",
        "Avoid working in wet fields to prevent mechanical spread.",
        "Consider resistant varieties for replanting.",
    ],
    "Bacterial Spot": [
        "Apply copper bactericide at first sign of infection.",
        "Avoid overhead irrigation.",
        "Remove and destroy heavily infected plants.",
        "Disinfect tools between plants with 10% bleach solution.",
    ],
    "Healthy": [
        "Plant appears healthy! Continue regular monitoring.",
        "Maintain balanced fertilisation schedule.",
        "Keep irrigation consistent and avoid waterlogging.",
    ],
}

DEFAULT_TREATMENTS: list[str] = [
    "Consult a local agronomist for precise recommendations.",
    "Apply broad-spectrum fungicide as a first response.",
    "Remove visibly infected foliage and dispose safely.",
    "Improve field drainage and air circulation.",
    "Monitor plant daily for 14 days and track progression.",
]


class DiseaseDetectionResult:
    """
    Data class holding the output of a disease detection inference call.

    Attributes:
        name:                 Detected disease name.
        confidence:           Detection confidence in [0, 1].
        severity:             'low' | 'moderate' | 'high' | 'critical'.
        affected_area_percent: Estimated % of leaf area affected.
        treatment_recommendations: Ordered list of recommended actions.
    """

    def __init__(
        self,
        name: str,
        confidence: float,
        severity: str = "moderate",
        affected_area_percent: Optional[float] = None,
        treatment_recommendations: Optional[list[str]] = None,
    ) -> None:
        self.name = name
        self.confidence = round(confidence, 4)
        self.severity = severity
        self.affected_area_percent = affected_area_percent
        self.treatment_recommendations = treatment_recommendations or []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "confidence": self.confidence,
            "confidence_percent": f"{round(self.confidence * 100, 1)}%",
            "severity": self.severity,
            "affected_area_percent": self.affected_area_percent,
        }


class DiseaseAIService:
    """
    Service responsible for detecting plant diseases from crop images.

    Integration points (TODO when model is ready):
      - Load model weights on startup.
      - Replace mock body of ``detect_disease`` with real inference.
      - Optionally run a multi-label classifier for co-occurring diseases.
    """

    def __init__(self) -> None:
        # TODO: Load model checkpoint here
        # self.model = load_model(settings.DISEASE_MODEL_PATH)
        logger.info("DiseaseAIService initialised (mock mode).")

    async def detect_disease(
        self,
        image_bytes: bytes,
        crop_name: str,
        filename: Optional[str] = None,
    ) -> DiseaseDetectionResult:
        """
        Detect the predominant disease visible in the plant image.

        Args:
            image_bytes: Raw bytes of the validated plant image.
            crop_name:   Crop species (output of CropAIService.detect_crop).
            filename:    Original filename (used for logging).

        Returns:
            DiseaseDetectionResult with name, confidence, severity, and treatments.

        TODO:
            Replace mock block with real inference:

            .. code-block:: python

                tensor = preprocess(image_bytes)
                logits = self.model(tensor, crop_class=crop_name)
                probs  = softmax(logits)
                top_idx = probs.argmax()
                return DiseaseDetectionResult(
                    name=DISEASE_LABELS[top_idx],
                    confidence=float(probs[top_idx]),
                    severity=calculate_severity(image_bytes),
                )
        """
        logger.debug(
            "detect_disease() called — crop=%s, file=%s (mock mode)",
            crop_name,
            filename,
        )

        # ── MOCK RESPONSE ─────────────────────────────────────────────────────
        diseases = DISEASE_MAP.get(crop_name, DEFAULT_DISEASES)
        mock_disease = "Early Blight"  # Deterministic default for demos
        mock_confidence = round(random.uniform(0.93, 0.99), 4)
        mock_severity = "moderate"
        mock_area = round(random.uniform(25.0, 55.0), 1)

        treatments = TREATMENT_MAP.get(mock_disease, DEFAULT_TREATMENTS)

        logger.info(
            "Disease detected (mock): %s @ %.1f%% | severity=%s",
            mock_disease,
            mock_confidence * 100,
            mock_severity,
        )
        return DiseaseDetectionResult(
            name=mock_disease,
            confidence=mock_confidence,
            severity=mock_severity,
            affected_area_percent=mock_area,
            treatment_recommendations=treatments,
        )

    async def get_known_diseases(self, crop_name: Optional[str] = None) -> list[str]:
        """
        Return known disease names for a given crop, or all diseases if crop is None.
        """
        if crop_name:
            return DISEASE_MAP.get(crop_name, DEFAULT_DISEASES)
        all_diseases: set[str] = set()
        for d in DISEASE_MAP.values():
            all_diseases.update(d)
        return sorted(all_diseases)


# ─── Singleton ────────────────────────────────────────────────────────────────
disease_ai_service = DiseaseAIService()
