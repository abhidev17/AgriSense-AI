"""
Diagnose route for AgriSense AI.
POST /diagnose — the core AI-powered plant diagnosis endpoint.

Workflow:
  1. Validate uploaded image (type, size, integrity).
  2. Save image to uploads/.
  3. If crop supplied → use it; otherwise run CropAIService.detect_crop().
  4. Run DiseaseAIService.detect_disease().
  5. Run GeminiService.generate_explanation().
  6. Fetch weather data (if coordinates provided).
  7. Fetch market data for the detected crop.
  8. Persist full DiagnosisDocument to MongoDB.
  9. Return combined DiagnosisResponse JSON.
"""

import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, UploadFile, File, status

from app.database.models import (
    CropDetectionResult as CropDocModel,
    DiseaseDetectionResult as DiseaseDocModel,
    DiagnosisDocument,
    LocationData,
    MarketData,
    WeatherData,
)
from app.schemas import (
    CropInfo,
    DiseaseInfo,
    DiagnosisResponse,
    MarketInfo,
    WeatherInfo,
)
from app.services.crop_ai import crop_ai_service
from app.services.disease_ai import disease_ai_service
from app.services.gemini import gemini_service
from app.services.market import market_service
from app.services.mongo import mongo_service
from app.services.weather import weather_service
from app.utils.image import validate_image, save_image, get_image_metadata
from app.utils.logger import logger

router = APIRouter(prefix="/diagnose", tags=["Diagnosis"])


@router.post(
    "",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_200_OK,
    summary="Diagnose Plant Disease",
    description=(
        "Upload a plant image to receive an AI-powered diagnosis. "
        "The endpoint auto-detects the crop species (unless you supply it), "
        "identifies the disease, generates a natural-language explanation, "
        "and enriches the result with current weather and market data.\n\n"
        "**Accepted image types:** JPEG, PNG, WebP\n"
        "**Max image size:** 10 MB\n\n"
        "All AI services are currently running in **mock mode**. "
        "Real model integration will replace the mock responses."
    ),
    responses={
        200: {
            "description": "Diagnosis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "success",
                        "crop": {
                            "name": "Tomato",
                            "confidence": 0.97,
                            "confidence_percent": "97.0%",
                            "source": "ai",
                        },
                        "disease": {
                            "name": "Early Blight",
                            "confidence": 0.98,
                            "confidence_percent": "98.0%",
                            "severity": "moderate",
                            "affected_area_percent": 35.0,
                        },
                        "explanation": "Early Blight has been detected on your Tomato crop…",
                        "treatment_recommendations": [
                            "Remove and destroy infected leaves immediately.",
                            "Apply copper-based fungicide every 7–10 days.",
                        ],
                        "weather": {
                            "temperature_celsius": 28.5,
                            "humidity_percent": 72.0,
                            "condition": "Partly Cloudy",
                            "location": "Pune, Maharashtra",
                            "source": "mock",
                        },
                        "market": {
                            "crop_name": "Tomato",
                            "current_price_per_kg": 22.5,
                            "predicted_price_per_kg": 26.0,
                            "price_trend": "up",
                            "recommendation": "Hold stock for 2–3 weeks.",
                            "currency": "INR",
                            "source": "mock",
                        },
                        "image_path": "app/uploads/2024-07/abc123.jpg",
                        "timestamp": "2024-07-31T10:00:00",
                        "processing_time_ms": 312.5,
                    }
                }
            },
        },
        400: {"description": "Invalid image (wrong type, too large, or corrupted)"},
        422: {"description": "Validation error in form fields"},
        500: {"description": "Internal server error during AI processing"},
    },
)
async def diagnose_plant(
    image: UploadFile = File(
        ...,
        description="Plant image to diagnose (JPEG / PNG / WebP, max 10 MB)",
    ),
    crop: Optional[str] = Form(
        default=None,
        description="Optional crop name. If omitted, crop is auto-detected by AI.",
        examples=["Tomato"],
    ),
    latitude: Optional[float] = Form(
        default=None,
        ge=-90.0,
        le=90.0,
        description="GPS latitude for weather lookup",
        examples=[18.5204],
    ),
    longitude: Optional[float] = Form(
        default=None,
        ge=-180.0,
        le=180.0,
        description="GPS longitude for weather lookup",
        examples=[73.8567],
    ),
) -> DiagnosisResponse:
    """
    Core plant disease diagnosis endpoint.

    Accepts a multipart form upload and returns a fully enriched diagnosis
    combining AI results, weather context, and commodity market data.
    """
    session_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    logger.info(
        "POST /diagnose — session=%s, crop=%s, lat=%s, lon=%s",
        session_id,
        crop,
        latitude,
        longitude,
    )

    # ── Step 1 & 2: Validate and save image ──────────────────────────────────
    try:
        image_bytes = await validate_image(image)
    except HTTPException:
        raise  # Re-raise validation errors as-is
    except Exception as exc:
        logger.error("Unexpected error during image validation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the uploaded image.",
        )

    image_path = save_image(image_bytes, original_filename=image.filename)
    image_meta = get_image_metadata(image_bytes)
    logger.info("Image saved → %s", image_path)

    # ── Step 3: Crop detection ────────────────────────────────────────────────
    try:
        if crop:
            # User supplied crop name — skip AI detection
            crop_result_obj = type(
                "MockCropResult",
                (),
                {
                    "name": crop.strip(),
                    "confidence": 1.0,
                    "source": "user",
                    "to_dict": lambda self: {
                        "name": self.name,
                        "confidence": self.confidence,
                        "confidence_percent": "100.0%",
                        "source": self.source,
                    },
                },
            )()
            logger.info("Crop supplied by user: %s", crop_result_obj.name)
        else:
            crop_result_obj = await crop_ai_service.detect_crop(
                image_bytes=image_bytes, filename=image.filename
            )
    except Exception as exc:
        logger.error("Crop detection failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Crop detection service encountered an error.",
        )

    # ── Step 4: Disease detection ─────────────────────────────────────────────
    try:
        disease_result_obj = await disease_ai_service.detect_disease(
            image_bytes=image_bytes,
            crop_name=crop_result_obj.name,
            filename=image.filename,
        )
    except Exception as exc:
        logger.error("Disease detection failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Disease detection service encountered an error.",
        )

    # ── Step 5: Generate explanation ──────────────────────────────────────────
    try:
        explanation = await gemini_service.generate_explanation(
            crop_name=crop_result_obj.name,
            crop_confidence=crop_result_obj.confidence,
            disease_name=disease_result_obj.name,
            disease_confidence=disease_result_obj.confidence,
            severity=disease_result_obj.severity,
            temperature=None,   # Weather fetched next; passed as None here
            humidity=None,
        )
    except Exception as exc:
        logger.warning("Explanation generation failed (non-fatal): %s", exc)
        explanation = "Explanation generation is currently unavailable."

    # ── Step 6: Weather data ──────────────────────────────────────────────────
    weather_result = None
    weather_info: Optional[WeatherInfo] = None
    try:
        weather_result = await weather_service.get_weather(
            latitude=latitude, longitude=longitude
        )
        if weather_result:
            weather_info = WeatherInfo(**weather_result.to_dict())
    except Exception as exc:
        logger.warning("Weather fetch failed (non-fatal): %s", exc)

    # ── Step 7: Market data ───────────────────────────────────────────────────
    market_result = None
    market_info: Optional[MarketInfo] = None
    try:
        market_result = await market_service.get_market_data(
            crop_name=crop_result_obj.name
        )
        if market_result:
            market_info = MarketInfo(**market_result.to_dict())
    except Exception as exc:
        logger.warning("Market fetch failed (non-fatal): %s", exc)

    # ── Step 8: Persist to MongoDB ────────────────────────────────────────────
    try:
        doc = DiagnosisDocument(
            session_id=session_id,
            image_path=image_path,
            image_metadata=image_meta,
            crop=CropDocModel(
                name=crop_result_obj.name,
                confidence=crop_result_obj.confidence,
                source=crop_result_obj.source,
            ),
            disease=DiseaseDocModel(
                name=disease_result_obj.name,
                confidence=disease_result_obj.confidence,
                severity=disease_result_obj.severity,
                affected_area_percent=disease_result_obj.affected_area_percent,
            ),
            explanation=explanation,
            treatment_recommendations=disease_result_obj.treatment_recommendations,
            weather=WeatherData(**weather_result.to_dict()) if weather_result else None,
            market=MarketData(**market_result.to_dict()) if market_result else None,
            location=LocationData(latitude=latitude, longitude=longitude),
            timestamp=datetime.utcnow(),
            api_version="1.0.0",
        )
        await mongo_service.save_diagnosis(doc)
    except Exception as exc:
        logger.warning("MongoDB persist failed (non-fatal): %s", exc)

    # ── Step 9: Build and return response ─────────────────────────────────────
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    crop_dict = crop_result_obj.to_dict()
    disease_dict = disease_result_obj.to_dict()

    response = DiagnosisResponse(
        session_id=session_id,
        status="success",
        crop=CropInfo(**crop_dict),
        disease=DiseaseInfo(**disease_dict),
        explanation=explanation,
        treatment_recommendations=disease_result_obj.treatment_recommendations,
        weather=weather_info,
        market=market_info,
        image_path=image_path,
        timestamp=datetime.utcnow(),
        processing_time_ms=elapsed_ms,
    )

    logger.info(
        "Diagnosis complete — session=%s, crop=%s, disease=%s, time=%.1f ms",
        session_id,
        crop_result_obj.name,
        disease_result_obj.name,
        elapsed_ms,
    )

    return response
