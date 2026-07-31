"""
Diagnosis history route for AgriSense AI.
GET  /history          — paginated list of past diagnoses
GET  /history/{id}     — single diagnosis detail
DELETE /history/{id}   — remove a diagnosis record
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import DiagnosisHistoryItem, DiagnosisHistoryResponse, DiagnosisResponse
from app.services.mongo import mongo_service
from app.utils.logger import logger

router = APIRouter(prefix="/history", tags=["History"])


# ─── List ─────────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=DiagnosisHistoryResponse,
    summary="List Diagnosis History",
    description=(
        "Returns a paginated list of past plant diagnoses, sorted newest-first. "
        "Returns an empty list when MongoDB is unavailable."
    ),
    responses={
        200: {
            "description": "Paginated list of diagnoses",
            "content": {
                "application/json": {
                    "example": {
                        "total": 42,
                        "page": 1,
                        "page_size": 20,
                        "items": [
                            {
                                "session_id": "abc-123",
                                "crop_name": "Tomato",
                                "disease_name": "Early Blight",
                                "disease_severity": "moderate",
                                "timestamp": "2024-07-31T10:00:00",
                                "image_path": "app/uploads/2024-07/abc123.jpg",
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def list_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Records per page (max 100)"
    ),
) -> DiagnosisHistoryResponse:
    """
    Retrieve paginated diagnosis history from MongoDB.
    """
    logger.info("GET /history — page=%d, page_size=%d", page, page_size)

    records, total = await mongo_service.get_history(page=page, page_size=page_size)

    items: list[DiagnosisHistoryItem] = []
    for rec in records:
        try:
            items.append(
                DiagnosisHistoryItem(
                    session_id=rec.get("session_id", ""),
                    crop_name=rec.get("crop", {}).get("name", "Unknown"),
                    disease_name=rec.get("disease", {}).get("name", "Unknown"),
                    disease_severity=rec.get("disease", {}).get("severity", "unknown"),
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
    description="Returns the full diagnosis record for a given session ID.",
    responses={
        200: {"description": "Diagnosis record found"},
        404: {"description": "No diagnosis found with the given session_id"},
    },
)
async def get_diagnosis_detail(session_id: str) -> dict:
    """
    Retrieve a single full diagnosis document by session_id.
    """
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
    """
    Delete a diagnosis document from MongoDB by session_id.
    """
    logger.info("DELETE /history/%s", session_id)

    deleted = await mongo_service.delete_diagnosis(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnosis with session_id '{session_id}' not found.",
        )
