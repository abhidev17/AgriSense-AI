"""
Diagnosis history routes for AgriSense AI.
GET    /history          — paginated, filtered list of past diagnoses
GET    /history/stats    — aggregated statistics
GET    /history/{id}     — single diagnosis detail
DELETE /history/{id}     — remove a diagnosis record

Phase 2 additions:
  - Filter params: crop, disease, date_from, date_to, search, min_risk_score
  - GET /history/stats endpoint for dashboard metrics
  - DiagnosisHistoryItem now includes risk_score and overall_risk
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import DiagnosisHistoryItem, DiagnosisHistoryResponse
from app.services.mongo import mongo_service
from app.utils.logger import logger

router = APIRouter(prefix="/history", tags=["History"])


# ─── Stats ────────────────────────────────────────────────────────────────────


@router.get(
    "/stats",
    summary="Diagnosis Statistics",
    description=(
        "Returns aggregated statistics: total diagnoses, top crops, "
        "top diseases, average risk score, and severity distribution."
    ),
    responses={
        200: {
            "description": "Statistics retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "total_diagnoses": 128,
                        "top_crops": [{"crop": "Tomato", "count": 45}],
                        "top_diseases": [{"disease": "Early Blight", "count": 38}],
                        "avg_risk_score": 58.4,
                        "severity_distribution": {"moderate": 55, "high": 30, "low": 25},
                    }
                }
            },
        }
    },
)
async def get_stats() -> dict:
    """Return aggregated MongoDB statistics for the analytics dashboard."""
    logger.info("GET /history/stats")
    return await mongo_service.get_stats()


# ─── List ─────────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=DiagnosisHistoryResponse,
    summary="List Diagnosis History",
    description=(
        "Returns a paginated list of past plant diagnoses, sorted newest-first. "
        "Supports filtering by crop name, disease name, date range, free-text "
        "search, and minimum risk score."
    ),
    responses={
        200: {"description": "Paginated list of diagnoses"},
    },
)
async def list_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Records per page (max 100)"
    ),
    crop: Optional[str] = Query(
        default=None,
        description="Filter by crop name (case-insensitive partial match)",
        examples=["Tomato"],
    ),
    disease: Optional[str] = Query(
        default=None,
        description="Filter by disease name (case-insensitive partial match)",
        examples=["Blight"],
    ),
    date_from: Optional[datetime] = Query(
        default=None,
        description="Show diagnoses after this UTC datetime (ISO 8601)",
        examples=["2024-01-01T00:00:00"],
    ),
    date_to: Optional[datetime] = Query(
        default=None,
        description="Show diagnoses before this UTC datetime (ISO 8601)",
        examples=["2024-12-31T23:59:59"],
    ),
    search: Optional[str] = Query(
        default=None,
        min_length=2,
        description="Full-text search across crop, disease, and explanation",
        examples=["fungal infection"],
    ),
    min_risk_score: Optional[int] = Query(
        default=None,
        ge=0,
        le=100,
        description="Only return diagnoses with risk_score >= this value",
        examples=[60],
    ),
) -> DiagnosisHistoryResponse:
    """Retrieve paginated, filtered diagnosis history from MongoDB."""
    logger.info(
        "GET /history — page=%d, size=%d, crop=%s, disease=%s, search=%s, min_risk=%s",
        page, page_size, crop, disease, search, min_risk_score,
    )

    records, total = await mongo_service.get_history(
        page=page,
        page_size=page_size,
        crop=crop,
        disease=disease,
        date_from=date_from,
        date_to=date_to,
        search=search,
        min_risk_score=min_risk_score,
    )

    items: list[DiagnosisHistoryItem] = []
    for rec in records:
        try:
            action_plan = rec.get("action_plan") or {}
            items.append(
                DiagnosisHistoryItem(
                    session_id=rec.get("session_id", ""),
                    crop_name=rec.get("crop", {}).get("name", "Unknown"),
                    disease_name=rec.get("disease", {}).get("name", "Unknown"),
                    disease_severity=rec.get("disease", {}).get("severity", "unknown"),
                    risk_score=action_plan.get("risk_score"),
                    overall_risk=action_plan.get("overall_risk"),
                    timestamp=rec.get("timestamp"),
                    image_path=rec.get("image_path", ""),
                )
            )
        except Exception as exc:
            logger.warning("Skipping malformed history record: %s", exc)

    return DiagnosisHistoryResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


# ─── Detail ───────────────────────────────────────────────────────────────────


@router.get(
    "/{session_id}",
    summary="Get Diagnosis Detail",
    description="Returns the full diagnosis record including action plan for a given session ID.",
    responses={
        200: {"description": "Diagnosis record found"},
        404: {"description": "No diagnosis found with the given session_id"},
    },
)
async def get_diagnosis_detail(session_id: str) -> dict:
    """Retrieve a single full diagnosis document by session_id."""
    logger.info("GET /history/%s", session_id)

    record = await mongo_service.get_diagnosis_by_session(session_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnosis with session_id '{session_id}' not found.",
        )
    return record


# ─── Delete ───────────────────────────────────────────────────────────────────


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Diagnosis",
    description="Permanently deletes a diagnosis record by session ID.",
    responses={
        204: {"description": "Diagnosis deleted successfully"},
        404: {"description": "No diagnosis found with the given session_id"},
    },
)
async def delete_diagnosis(session_id: str) -> None:
    """Delete a diagnosis document from MongoDB by session_id."""
    logger.info("DELETE /history/%s", session_id)

    deleted = await mongo_service.delete_diagnosis(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnosis with session_id '{session_id}' not found.",
        )
