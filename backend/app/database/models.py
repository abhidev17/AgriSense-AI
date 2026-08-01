"""
Pydantic database models (documents) for AgriSense AI.
These models define the schema stored in MongoDB collections.

BACKWARD COMPATIBLE — existing fields preserved.
Added: ActionPlanData embedded document in DiagnosisDocument.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ─── Embedded Sub-documents ───────────────────────────────────────────────────


class CropDetectionResult(BaseModel):
    """Result from the crop detection AI service."""

    name: str = Field(..., description="Detected crop name, e.g. 'Tomato'")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Detection confidence (0-1)"
    )
    source: str = Field(
        default="ai",
        description="'ai' when auto-detected, 'user' when manually supplied",
    )


class DiseaseDetectionResult(BaseModel):
    """Result from the disease detection AI service."""

    name: str = Field(..., description="Detected disease name, e.g. 'Early Blight'")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Detection confidence (0-1)"
    )
    severity: str = Field(
        default="moderate",
        description="Disease severity: low | moderate | high | critical",
    )
    affected_area_percent: Optional[float] = Field(
        default=None, description="Estimated percentage of leaf area affected"
    )


class WeatherData(BaseModel):
    """Weather snapshot at the time of diagnosis."""

    temperature_celsius: Optional[float] = Field(
        default=None, description="Temperature in Celsius"
    )
    humidity_percent: Optional[float] = Field(
        default=None, description="Relative humidity (%)"
    )
    rainfall_mm: Optional[float] = Field(
        default=None, description="Rainfall in the past 24 h (mm)"
    )
    wind_speed_kmh: Optional[float] = Field(
        default=None, description="Wind speed in km/h"
    )
    condition: Optional[str] = Field(
        default=None, description="Human-readable condition, e.g. 'Partly Cloudy'"
    )
    location: Optional[str] = Field(
        default=None, description="Location name resolved from coordinates"
    )
    source: str = Field(
        default="mock", description="Data source: 'openweathermap' | 'mock'"
    )


class MarketData(BaseModel):
    """Market price snapshot at the time of diagnosis."""

    crop_name: str = Field(..., description="Crop for which prices are reported")
    current_price_per_kg: Optional[float] = Field(
        default=None, description="Current wholesale price"
    )
    predicted_price_per_kg: Optional[float] = Field(
        default=None, description="30-day price prediction"
    )
    price_trend: Optional[str] = Field(
        default=None, description="'up' | 'down' | 'stable'"
    )
    recommendation: Optional[str] = Field(
        default=None, description="Market action recommendation for the farmer"
    )
    currency: str = Field(default="INR", description="Price currency code")
    source: str = Field(
        default="mock", description="Data source: 'agmarknet' | 'mock'"
    )


class LocationData(BaseModel):
    """Geographic location associated with a diagnosis."""

    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)


class ActionPlanTimelineItemData(BaseModel):
    """A single timeline step stored in MongoDB."""

    day: str = Field(..., description="Time frame label")
    action: str = Field(..., description="Action to take")
    reason: str = Field(..., description="Why this action is recommended")


class ActionPlanData(BaseModel):
    """
    Action plan document embedded in DiagnosisDocument.
    Mirrors ActionPlanResponse schema for consistent storage.
    """

    overall_risk: str = Field(..., description="Low | Medium | High | Critical")
    risk_score: int = Field(..., ge=0, le=100, description="Numeric risk score (0-100)")
    estimated_recovery: str = Field(..., description="Recovery estimate, e.g. '90-95%'")
    timeline: list[ActionPlanTimelineItemData] = Field(default_factory=list)
    immediate_actions: list[str] = Field(default_factory=list)
    prevention_tips: list[str] = Field(default_factory=list)


# ─── Main Document Model ───────────────────────────────────────────────────────


class DiagnosisDocument(BaseModel):
    """
    MongoDB document model for a plant disease diagnosis.
    Stored in the ``diagnoses`` collection.
    """

    # Identification
    session_id: str = Field(..., description="Unique identifier for this diagnosis")

    # Image
    image_path: str = Field(..., description="Relative path to the saved upload")
    image_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Width, height, format, etc."
    )

    # AI results
    crop: CropDetectionResult = Field(..., description="Crop detection result")
    disease: DiseaseDetectionResult = Field(..., description="Disease detection result")
    explanation: str = Field(
        default="", description="AI-generated natural-language explanation"
    )
    treatment_recommendations: list[str] = Field(
        default_factory=list, description="Ordered list of treatment steps"
    )

    # Action plan (always present after generation)
    action_plan: Optional[ActionPlanData] = Field(
        default=None, description="Structured action plan and risk assessment"
    )

    # Contextual data
    weather: Optional[WeatherData] = Field(default=None)
    market: Optional[MarketData] = Field(default=None)
    location: Optional[LocationData] = Field(default=None)

    # Meta
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of the diagnosis",
    )
    processing_time_ms: Optional[float] = Field(
        default=None, description="Total backend processing time in milliseconds"
    )
    api_version: str = Field(default="1.1.0")

    model_config = {"arbitrary_types_allowed": True}
