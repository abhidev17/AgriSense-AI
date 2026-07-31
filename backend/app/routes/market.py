"""
Market data route for AgriSense AI.
GET /market
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import MarketInfo
from app.services.market import market_service
from app.utils.logger import logger

router = APIRouter(prefix="/market", tags=["Market"])


@router.get(
    "",
    response_model=MarketInfo,
    summary="Get Market Price Data",
    description=(
        "Returns current and predicted commodity prices for a given crop name. "
        "Includes a market trend indicator and farmer-friendly recommendation. "
        "When a market API key is configured the response reflects real data; "
        "otherwise mock data is returned."
    ),
    responses={
        200: {
            "description": "Market data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "crop_name": "Tomato",
                        "current_price_per_kg": 22.5,
                        "predicted_price_per_kg": 26.0,
                        "price_trend": "up",
                        "recommendation": "Hold stock for 2–3 weeks; prices expected to rise.",
                        "currency": "INR",
                        "source": "mock",
                    }
                }
            },
        },
        400: {"description": "Missing or invalid crop name"},
        404: {"description": "No market data found for the given crop"},
    },
)
async def get_market_data(
    crop: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Crop name to fetch market prices for",
        examples=["Tomato"],
    ),
) -> MarketInfo:
    """
    Fetch current and predicted wholesale prices for the given crop.
    """
    logger.info("GET /market — crop=%s", crop)

    result = await market_service.get_market_data(crop_name=crop)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No market data available for crop '{crop}'.",
        )

    return MarketInfo(**result.to_dict())
