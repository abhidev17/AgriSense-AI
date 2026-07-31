"""
Health check route for AgriSense AI.
GET /health
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.database.mongodb import mongodb_manager
from app.schemas import HealthResponse
from app.utils.config import Settings, get_settings
from app.utils.logger import logger

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description=(
        "Returns the current health status of the AgriSense AI API, "
        "including database connectivity and running version."
    ),
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "database": "connected",
                        "version": "1.0.0",
                        "timestamp": "2024-07-31T10:00:00",
                    }
                }
            },
        }
    },
)
async def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Lightweight health probe endpoint.

    Checks:
      - API is reachable (trivially true if this runs).
      - MongoDB connection status.

    Suitable for use as a Kubernetes liveness/readiness probe.
    """
    db_status = "connected" if mongodb_manager.is_connected else "disconnected"

    logger.debug("Health check — DB: %s", db_status)

    return HealthResponse(
        status="healthy",
        database=db_status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
    )
