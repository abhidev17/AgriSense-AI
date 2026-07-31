"""
Diagnose route for AgriSense AI.
POST /diagnose — core AI-powered plant diagnosis endpoint.

Phase 2 workflow (10 steps):
  1.  Validate uploaded image.
  2.  Save image to uploads/.
  3.  If crop supplied use it; otherwise call CropAIService.detect_crop().
  4.  Call DiseaseAIService.detect_disease().
  5.  Call GeminiService.generate_explanation() (uses weather context).
  6.  Fetch weather data (if coordinates provided).
  7.  Fetch market data for the detected crop.
  8.  Generate ActionPlan from disease + weather + market.
  9.  Persist complete DiagnosisDocument (with action_plan) to MongoDB.
  10. Return combined DiagnosisResponse JSON.
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
    ActionPlanData,
    ActionPlanTimelineItemData,
)
from app.schemas import (
    CropInfo,
    DiseaseInfo,
    DiagnosisResponse,
    MarketInfo,
    WeatherInfo,
    ActionPlanResponse,
    ActionPlanTimelineItem,
)
from app.services.action_plan import action_plan_service
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
        "Upload a plant image to receive an AI-powered diagnosis.\n\n"
        "The endpoint auto-detects the crop species (unless supplied), "
        "identifies the disease, generates a Gemini-powered explanation, "
        "enriches with weather and market data, and computes a structured "
        "**Action Plan** with risk score and recovery timeline.\n\n"
        "**Accepted image types:** JPEG, PNG, WebP  \n"
        "**Max image size:** 10 MB"
    ),
    responses={
        200: {
            "description": "Diagnosis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "success",
                        "crop": {"name": "Tomato", "confidence": 0.97, "confidence_percent": "97.0%", "source": "ai"},
                        "disease": {"name": "Early Blight", "confidence": 0.98, "confidence_percent": "98.0%", "severity": "moderate", "affected_area_percent": 35.0},
                        "explanation": "Early Blight has been detected on your Tomato crop...",
                        "treatment_recommendations": ["Remove infected leaves immediately.", "Apply copper fungicide every 7-10 days."],
                        "weather": {"temperature_celsius": 28.5, "humidity_percent": 72.0, "condition": "Partly Cloudy", "location": "Pune, Maharashtra", "source": "mock"},
                        "market": {"crop_name": "Tomato", "current_price_per_kg": 22.5, "predicted_price_per_kg": 26.0, "price_trend": "up", "recommendation": "Hold stock for 2-3 weeks.", "currency": "INR", "source": "mock"},
                        "action_plan": {
                            "overall_risk": "Medium",
                            "risk_score": 62,
                            "estimated_recovery": "90-95%",
                            "timeline": [
                                {"day": "Day 1-2", "action": "Remove infected foliage", "priority": "high"},
                                {"day": "Day 2-3", "action": "Apply fungicide", "priority": "medium"},
                            ],
                            "immediate_actions": ["Document and photograph infected plants."],
                            "prevention_tips": ["Plant disease-resistant varieties next season."],
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
        description="Optional crop name. If omitted, auto-detected by AI.",
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
    Returns a fully enriched diagnosis with AI results, weather, market, and action plan.
    """
    session_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    logger.info(
        "POST /diagnose — session=%s, crop=%s, lat=%s, lon=%s",
        session_id, crop, latitude, longitude,
    )

    # ── Step 1 & 2: Validate and save image ───────────────────────────────────
    try:
        image_bytes = await validate_image(image)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error during image validation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the uploaded image.",
        )

    image_path = save_image(image_bytes, original_filename=image.filename)
    image_meta = get_image_metadata(image_bytes)
    logger.info("Image saved — %s", image_path)

    # ── Step 3: Crop detection ─────────────────────────────────────────────────
    try:
        if crop:
            crop_result_obj = _make_user_crop_result(crop)
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

    # ── Step 4: Disease detection ──────────────────────────────────────────────
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

    # ── Step 6: Weather data (before explanation so we can pass to Gemini) ────
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

    # ── Step 5: Generate explanation (with weather context now available) ──────
    try:
        explanation = await gemini_service.generate_explanation(
            crop_name=crop_result_obj.name,
            crop_confidence=crop_result_obj.confidence,
            disease_name=disease_result_obj.name,
            disease_confidence=disease_result_obj.confidence,
            severity=disease_result_obj.severity,
            temperature=weather_result.temperature_celsius if weather_result else None,
            humidity=weather_result.humidity_percent if weather_result else None,
            affected_area=disease_result_obj.affected_area_percent,
            condition=weather_result.condition if weather_result else None,
        )
    except Exception as exc:
        logger.warning("Explanation generation failed (non-fatal): %s", exc)
        explanation = "Explanation generation is currently unavailable."

    # ── Step 7: Market data ────────────────────────────────────────────────────
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

    # ── Step 8: Generate Action Plan ───────────────────────────────────────────
    try:
        action_plan_result = action_plan_service.generate(
            crop_name=crop_result_obj.name,
            disease_name=disease_result_obj.name,
            severity=disease_result_obj.severity,
            confidence=disease_result_obj.confidence,
            temperature=weather_result.temperature_celsius if weather_result else None,
            humidity=weather_result.humidity_percent if weather_result else None,
            current_price=(
                market_result.current_price_per_kg if market_result else None
            ),
            price_trend=market_result.price_trend if market_result else None,
        )
    except Exception as exc:
        logger.warning("Action plan generation failed (non-fatal): %s", exc)
        # Minimal fallback
        from app.services.action_plan import ActionPlanResult
        action_plan_result = ActionPlanResult(
            overall_risk="Unknown",
            risk_score=50,
            estimated_recovery="Unknown",
            timeline=[],
            immediate_actions=["Consult a local agronomist."],
            prevention_tips=[],
        )

    # ── Step 9: Persist to MongoDB ─────────────────────────────────────────────
    elapsed_so_far = round((time.perf_counter() - start_time) * 1000, 2)
    try:
        ap = action_plan_result
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
            action_plan=ActionPlanData(
                overall_risk=ap.overall_risk,
                risk_score=ap.risk_score,
                estimated_recovery=ap.estimated_recovery,
                timeline=[
                    ActionPlanTimelineItemData(**t) for t in ap.timeline
                ],
                immediate_actions=ap.immediate_actions,
                prevention_tips=ap.prevention_tips,
            ),
            weather=WeatherData(**weather_result.to_dict()) if weather_result else None,
            market=MarketData(**market_result.to_dict()) if market_result else None,
            location=LocationData(latitude=latitude, longitude=longitude),
            timestamp=datetime.utcnow(),
            processing_time_ms=elapsed_so_far,
            api_version="1.1.0",
        )
        await mongo_service.save_diagnosis(doc)
    except Exception as exc:
        logger.warning("MongoDB persist failed (non-fatal): %s", exc)

    # ── Step 10: Build and return response ─────────────────────────────────────
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    ap_timeline = [
        ActionPlanTimelineItem(**t) if isinstance(t, dict) else ActionPlanTimelineItem(**t.__dict__)
        for t in action_plan_result.timeline
    ]

    response = DiagnosisResponse(
        session_id=session_id,
        status="success",
        crop=CropInfo(**crop_result_obj.to_dict()),
        disease=DiseaseInfo(**disease_result_obj.to_dict()),
        explanation=explanation,
        treatment_recommendations=disease_result_obj.treatment_recommendations,
        treatment=disease_result_obj.treatment_recommendations,
        weather=weather_info,
        market=market_info,
        action_plan=ActionPlanResponse(
            overall_risk=action_plan_result.overall_risk,
            risk_score=action_plan_result.risk_score,
            estimated_recovery=action_plan_result.estimated_recovery,
            timeline=ap_timeline,
            immediate_actions=action_plan_result.immediate_actions,
            prevention_tips=action_plan_result.prevention_tips,
        ),
        image_path=image_path,
        timestamp=datetime.utcnow(),
        processing_time_ms=elapsed_ms,
    )

    logger.info(
        "Diagnosis complete — session=%s, crop=%s, disease=%s, risk=%s/%d, time=%.1f ms",
        session_id,
        crop_result_obj.name,
        disease_result_obj.name,
        action_plan_result.overall_risk,
        action_plan_result.risk_score,
        elapsed_ms,
    )

    return response


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_user_crop_result(crop_name: str):
    """
    Build a lightweight crop result object from a user-supplied crop name.
    Avoids anonymous class creation for cleaner code.
    """
    class _UserCropResult:
        name = crop_name.strip()
        confidence = 1.0
        source = "user"

        def to_dict(self):
            return {
                "name": self.name,
                "confidence": self.confidence,
                "confidence_percent": "100.0%",
                "source": self.source,
            }

    return _UserCropResult()
