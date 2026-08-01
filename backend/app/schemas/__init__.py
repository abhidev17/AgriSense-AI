"""
Pydantic request / response schemas for AgriSense AI API.
These are the shapes exposed to external clients (distinct from DB models).

BACKWARD COMPATIBLE — existing fields are unchanged.
New fields: ActionPlanTimelineItem, ActionPlanResponse added to DiagnosisResponse.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ─── Shared sub-schemas ────────────────────────────────────────────────────────


class CropInfo(BaseModel):
    """Crop detection result returned to the client."""

    name: str = Field(..., examples=["Tomato"], description="Detected crop name")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, examples=[0.97], description="Confidence score (0-1)"
    )
    confidence_percent: str = Field(
        ..., examples=["97%"], description="Confidence as a formatted percentage"
    )
    source: str = Field(
        ...,
        examples=["ai"],
        description="'ai' = auto-detected | 'user' = manually supplied",
    )


class DiseaseInfo(BaseModel):
    """Disease detection result returned to the client."""

    name: str = Field(
        ..., examples=["Early Blight"], description="Detected disease name"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, examples=[0.98], description="Confidence score (0-1)"
    )
    confidence_percent: str = Field(
        ..., examples=["98%"], description="Confidence as a formatted percentage"
    )
    severity: str = Field(
        ...,
        examples=["moderate"],
        description="Disease severity: low | moderate | high | critical",
    )
    affected_area_percent: Optional[float] = Field(
        default=None,
        examples=[35.0],
        description="Estimated percentage of affected leaf area",
    )


class WeatherInfo(BaseModel):
    """Weather snapshot returned to the client."""

    temperature_celsius: Optional[float] = Field(
        default=None, examples=[28.5], description="Temperature in Celsius"
    )
    humidity_percent: Optional[float] = Field(
        default=None, examples=[72.0], description="Relative humidity (%)"
    )
    rainfall_mm: Optional[float] = Field(
        default=None, examples=[2.4], description="Rainfall last 24 h (mm)"
    )
    wind_speed_kmh: Optional[float] = Field(
        default=None, examples=[14.0], description="Wind speed km/h"
    )
    condition: Optional[str] = Field(
        default=None, examples=["Partly Cloudy"], description="Weather condition"
    )
    location: Optional[str] = Field(
        default=None, examples=["Pune, Maharashtra"], description="Resolved location"
    )
    source: str = Field(
        default="mock", examples=["openweathermap"], description="Data source"
    )


class MarketInfo(BaseModel):
    """Market price snapshot returned to the client."""

    crop_name: str = Field(
        ..., examples=["Tomato"], description="Crop for which prices are shown"
    )
    current_price_per_kg: Optional[float] = Field(
        default=None, examples=[22.5], description="Current wholesale price"
    )
    predicted_price_per_kg: Optional[float] = Field(
        default=None, examples=[26.0], description="30-day predicted price"
    )
    price_trend: Optional[str] = Field(
        default=None, examples=["up"], description="'up' | 'down' | 'stable'"
    )
    recommendation: Optional[str] = Field(
        default=None,
        examples=["Hold stock for 2-3 weeks; prices expected to rise."],
        description="Market action recommendation",
    )
    currency: str = Field(default="INR", examples=["INR"])
    source: str = Field(default="mock", examples=["agmarknet"])


# ─── Action Plan schemas ───────────────────────────────────────────────────────


class ActionPlanTimelineItem(BaseModel):
    """A single step in the recovery action timeline."""

    day: str = Field(
        ...,
        examples=["Today"],
        description="Time frame label: Today | Tomorrow | After 3 Days | Next Week | Harvest",
    )
    action: str = Field(
        ...,
        examples=["Remove infected leaves"],
        description="Specific action to take in this time frame",
    )
    reason: str = Field(
        ...,
        examples=["Prevents disease spread to healthy tissue."],
        description="Why this action is recommended at this time",
    )


class ActionPlanResponse(BaseModel):
    """
    Structured risk assessment and recovery plan.
    Generated from disease severity + weather + market context.
    """

    overall_risk: str = Field(
        ...,
        examples=["Medium"],
        description="Overall risk level: Low | Medium | High | Critical",
    )
    risk_score: int = Field(
        ...,
        ge=0,
        le=100,
        examples=[62],
        description="Numeric risk score (0=no risk, 100=critical)",
    )
    estimated_recovery: str = Field(
        ...,
        examples=["90-95%"],
        description="Estimated crop recovery percentage with prompt treatment",
    )
    timeline: list[ActionPlanTimelineItem] = Field(
        default_factory=list,
        description="Ordered day-by-day action plan",
    )
    immediate_actions: list[str] = Field(
        default_factory=list,
        description="Critical actions required within 24 hours",
    )
    prevention_tips: list[str] = Field(
        default_factory=list,
        description="Long-term prevention recommendations for next season",
    )


# ─── Diagnosis Response ────────────────────────────────────────────────────────


class DiagnosisResponse(BaseModel):
    """
    Full diagnosis response returned by POST /diagnose.
    Combines AI, weather, market results, and action plan in one payload.
    """

    session_id: str = Field(
        ..., description="Unique identifier for this diagnosis session"
    )
    status: str = Field(
        default="success", examples=["success"], description="'success' or 'error'"
    )

    # AI results
    crop: CropInfo
    disease: DiseaseInfo
    explanation: str = Field(
        ..., description="AI-generated natural-language explanation"
    )
    treatment_recommendations: list[str] = Field(
        default_factory=list,
        description="Ordered list of treatment steps",
    )
    treatment: list[str] = Field(
        default_factory=list,
        description="Ordered list of treatment steps (alias/compatible field)",
    )

    # Contextual enrichment
    weather: Optional[WeatherInfo] = Field(
        default=None, description="Weather data (None if coordinates not provided)"
    )
    market: Optional[MarketInfo] = Field(
        default=None, description="Market data for the detected crop"
    )

    # Action plan (always present)
    action_plan: ActionPlanResponse = Field(
        ..., description="Structured risk assessment and recovery action plan"
    )

    # Meta
    image_path: str = Field(..., description="Server-side path where image was saved")
    timestamp: datetime = Field(..., description="UTC timestamp of the diagnosis")
    processing_time_ms: float = Field(
        ..., description="Total backend processing time in ms"
    )


# ─── History schemas ───────────────────────────────────────────────────────────


class DiagnosisHistoryItem(BaseModel):
    """Compact representation of a past diagnosis used in list views."""

    session_id: str
    crop_name: str
    disease_name: str
    disease_severity: str
    risk_score: Optional[int] = Field(default=None, description="Action plan risk score")
    overall_risk: Optional[str] = Field(default=None, description="Risk level label")
    timestamp: datetime
    image_path: str


class DiagnosisHistoryResponse(BaseModel):
    """Paginated history response with optional filtering."""

    total: int = Field(..., description="Total number of matching records")
    page: int = Field(..., description="Current page (1-indexed)")
    page_size: int = Field(..., description="Number of records per page")
    items: list[DiagnosisHistoryItem]


# ─── Health & generic schemas ──────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Response for GET /health."""

    status: str = Field(default="healthy", examples=["healthy"])
    database: str = Field(
        default="connected",
        examples=["connected"],
        description="'connected' | 'disconnected'",
    )
    version: str = Field(default="1.0.0")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RootResponse(BaseModel):
    """Response for GET /."""

    message: str
    version: str
    docs_url: str
    status: str


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
