"""
Weather route for AgriSense AI.
GET /weather
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import WeatherInfo
from app.services.weather import weather_service
from app.utils.logger import logger

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get(
    "",
    response_model=WeatherInfo,
    summary="Get Current Weather",
    description=(
        "Returns current weather conditions for the provided GPS coordinates. "
        "Both ``latitude`` and ``longitude`` are required. "
        "When an OpenWeatherMap API key is configured the response reflects "
        "real-time data; otherwise mock data is returned."
    ),
    responses={
        200: {
            "description": "Weather data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "temperature_celsius": 28.5,
                        "humidity_percent": 72.0,
                        "rainfall_mm": 2.4,
                        "wind_speed_kmh": 14.0,
                        "condition": "Partly Cloudy",
                        "location": "Pune, Maharashtra, India",
                        "source": "mock",
                    }
                }
            },
        },
        400: {"description": "Missing or invalid coordinates"},
    },
)
async def get_weather(
    latitude: Optional[float] = Query(
        default=None,
        ge=-90.0,
        le=90.0,
        description="GPS latitude (-90 to 90)",
        examples=[18.5204],
    ),
    longitude: Optional[float] = Query(
        default=None,
        ge=-180.0,
        le=180.0,
        description="GPS longitude (-180 to 180)",
        examples=[73.8567],
    ),
) -> WeatherInfo:
    """
    Fetch current weather for the given latitude / longitude.
    """
    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'latitude' and 'longitude' query parameters are required.",
        )

    logger.info("GET /weather — lat=%.4f, lon=%.4f", latitude, longitude)

    result = await weather_service.get_weather(latitude=latitude, longitude=longitude)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve weather data for the provided coordinates.",
        )

    return WeatherInfo(**result.to_dict())
