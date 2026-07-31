"""
Weather service for AgriSense AI.

PLACEHOLDER IMPLEMENTATION
──────────────────────────
This module defines the interface for fetching real-time weather data.
OpenWeatherMap will be integrated here once an API key is available.

Current behaviour: returns realistic mock weather data.
"""

import random
from typing import Optional

import httpx

from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()

# ─── Weather condition pool (mock) ────────────────────────────────────────────
MOCK_CONDITIONS = [
    "Partly Cloudy",
    "Overcast",
    "Clear Sky",
    "Light Rain",
    "Humid and Warm",
    "Thunderstorm",
]


class WeatherResult:
    """
    Data class holding weather snapshot data.

    Attributes:
        temperature_celsius: Air temperature in °C.
        humidity_percent:    Relative humidity (%).
        rainfall_mm:         Rainfall in the last 24 h (mm).
        wind_speed_kmh:      Wind speed in km/h.
        condition:           Human-readable weather description.
        location:            Resolved place name from coordinates.
        source:              'openweathermap' | 'mock'.
    """

    def __init__(
        self,
        temperature_celsius: float,
        humidity_percent: float,
        rainfall_mm: float,
        wind_speed_kmh: float,
        condition: str,
        location: str,
        source: str = "mock",
    ) -> None:
        self.temperature_celsius = temperature_celsius
        self.humidity_percent = humidity_percent
        self.rainfall_mm = rainfall_mm
        self.wind_speed_kmh = wind_speed_kmh
        self.condition = condition
        self.location = location
        self.source = source

    def to_dict(self) -> dict:
        return {
            "temperature_celsius": self.temperature_celsius,
            "humidity_percent": self.humidity_percent,
            "rainfall_mm": self.rainfall_mm,
            "wind_speed_kmh": self.wind_speed_kmh,
            "condition": self.condition,
            "location": self.location,
            "source": self.source,
        }


class WeatherService:
    """
    Service that fetches weather data for a given geographic coordinate pair.

    Integration points (TODO when API key is available):
      - Set OPENWEATHER_API_KEY in .env
      - Replace mock block in ``get_weather`` with a real httpx call to
        https://api.openweathermap.org/data/2.5/weather
    """

    def __init__(self) -> None:
        self._api_key = settings.OPENWEATHER_API_KEY
        self._base_url = settings.OPENWEATHER_BASE_URL
        logger.info(
            "WeatherService initialised — API key %s.",
            "present" if self._api_key else "NOT SET (mock mode)",
        )

    async def get_weather(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Optional[WeatherResult]:
        """
        Fetch current weather for the given coordinates.

        Args:
            latitude:  GPS latitude.
            longitude: GPS longitude.

        Returns:
            WeatherResult, or None if both coordinates are missing.

        TODO:
            Replace mock block with real OpenWeatherMap call:

            .. code-block:: python

                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{self._base_url}/weather",
                        params={
                            "lat": latitude,
                            "lon": longitude,
                            "appid": self._api_key,
                            "units": "metric",
                        },
                        timeout=10.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return WeatherResult(
                        temperature_celsius=data["main"]["temp"],
                        humidity_percent=data["main"]["humidity"],
                        rainfall_mm=data.get("rain", {}).get("1h", 0.0),
                        wind_speed_kmh=data["wind"]["speed"] * 3.6,
                        condition=data["weather"][0]["description"].title(),
                        location=data["name"],
                        source="openweathermap",
                    )
        """
        if latitude is None or longitude is None:
            logger.debug("No coordinates provided — skipping weather fetch.")
            return None

        logger.debug(
            "get_weather() called — lat=%.4f, lon=%.4f (mock mode)",
            latitude,
            longitude,
        )

        # ── MOCK RESPONSE ─────────────────────────────────────────────────────
        mock_result = WeatherResult(
            temperature_celsius=round(random.uniform(22.0, 35.0), 1),
            humidity_percent=round(random.uniform(55.0, 85.0), 1),
            rainfall_mm=round(random.uniform(0.0, 8.0), 2),
            wind_speed_kmh=round(random.uniform(5.0, 25.0), 1),
            condition=random.choice(MOCK_CONDITIONS),
            location="Pune, Maharashtra, India",
            source="mock",
        )

        logger.info(
            "Weather fetched (mock): %.1f°C, %.1f%% RH, %s",
            mock_result.temperature_celsius,
            mock_result.humidity_percent,
            mock_result.condition,
        )
        return mock_result

    async def get_weather_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> list[dict]:
        """
        Fetch a multi-day weather forecast.

        TODO: Implement using OpenWeatherMap 5-day / 3-hour forecast endpoint.

        Returns:
            List of daily forecast dicts (mock: empty list).
        """
        logger.debug("get_weather_forecast() — not yet implemented (returning []).")
        return []


# ─── Singleton ────────────────────────────────────────────────────────────────
weather_service = WeatherService()
