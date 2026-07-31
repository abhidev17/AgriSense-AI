"""
Weather service for AgriSense AI.

REAL IMPLEMENTATION with graceful mock fallback.
When OPENWEATHER_API_KEY is set in .env, fetches real-time data from
OpenWeatherMap Current Weather API (v2.5).
When key is absent, returns realistic randomised mock data.
"""

import random
from typing import Optional

import httpx

from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()

# ─── Mock data pools ──────────────────────────────────────────────────────────
MOCK_CONDITIONS = [
    "Partly Cloudy",
    "Overcast",
    "Clear Sky",
    "Light Rain",
    "Humid and Warm",
    "Hazy Sunshine",
    "Scattered Showers",
]


class WeatherResult:
    """
    Holds a weather snapshot.

    Attributes:
        temperature_celsius: Air temperature in °C.
        humidity_percent:    Relative humidity (%).
        rainfall_mm:         Rainfall in the last 24 h (mm).
        wind_speed_kmh:      Wind speed in km/h.
        condition:           Human-readable description.
        location:            Resolved place name.
        source:              'openweathermap' | 'mock'.
    """

    __slots__ = (
        "temperature_celsius",
        "humidity_percent",
        "rainfall_mm",
        "wind_speed_kmh",
        "condition",
        "location",
        "source",
    )

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
        self.temperature_celsius = round(temperature_celsius, 1)
        self.humidity_percent = round(humidity_percent, 1)
        self.rainfall_mm = round(rainfall_mm, 2)
        self.wind_speed_kmh = round(wind_speed_kmh, 1)
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
    Service that fetches current weather for a given coordinate pair.

    Uses OpenWeatherMap API when OPENWEATHER_API_KEY is set;
    falls back to mock data otherwise.
    """

    # Request timeout in seconds
    _TIMEOUT = 8.0

    def __init__(self) -> None:
        self._api_key = settings.OPENWEATHER_API_KEY
        self._base_url = settings.OPENWEATHER_BASE_URL
        self._mock_mode = not bool(self._api_key)

        logger.info(
            "WeatherService initialised — %s",
            "mock mode (OPENWEATHER_API_KEY not set)"
            if self._mock_mode
            else f"real mode (OWM key present, base={self._base_url})",
        )

    # ─── Public API ───────────────────────────────────────────────────────────

    async def get_weather(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Optional[WeatherResult]:
        """
        Fetch current weather for the given GPS coordinates.

        Args:
            latitude:  GPS latitude.
            longitude: GPS longitude.

        Returns:
            WeatherResult, or None if coordinates are missing.
        """
        if latitude is None or longitude is None:
            logger.debug("No coordinates provided — skipping weather fetch.")
            return None

        if self._mock_mode:
            return self._mock_weather(latitude, longitude)

        return await self._fetch_openweathermap(latitude, longitude)

    async def get_weather_forecast(
        self, latitude: float, longitude: float, days: int = 5
    ) -> list[dict]:
        """
        Fetch a multi-day weather forecast using OWM 5-day / 3-hour endpoint.
        Returns empty list when in mock mode or if API fails.
        """
        if self._mock_mode:
            logger.debug("get_weather_forecast() — mock mode, returning [].")
            return []

        try:
            async with httpx.AsyncClient(timeout=self._TIMEOUT) as client:
                resp = await client.get(
                    f"{self._base_url}/forecast",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": self._api_key,
                        "units": "metric",
                        "cnt": days * 8,  # 8 readings per day (3-hourly)
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                forecasts = []
                seen_dates: set[str] = set()
                for item in data.get("list", []):
                    date_str = item["dt_txt"].split(" ")[0]
                    if date_str not in seen_dates:
                        seen_dates.add(date_str)
                        forecasts.append(
                            {
                                "date": date_str,
                                "temp_high": item["main"]["temp_max"],
                                "temp_low": item["main"]["temp_min"],
                                "humidity": item["main"]["humidity"],
                                "condition": item["weather"][0]["description"].title(),
                                "rain_mm": item.get("rain", {}).get("3h", 0.0),
                            }
                        )
                return forecasts[:days]

        except Exception as exc:
            logger.warning("Weather forecast fetch failed: %s", exc)
            return []

    @property
    def is_mock_mode(self) -> bool:
        return self._mock_mode

    # ─── Private helpers ──────────────────────────────────────────────────────

    async def _fetch_openweathermap(
        self, latitude: float, longitude: float
    ) -> Optional[WeatherResult]:
        """Call the OWM Current Weather API and parse the response."""
        try:
            async with httpx.AsyncClient(timeout=self._TIMEOUT) as client:
                resp = await client.get(
                    f"{self._base_url}/weather",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": self._api_key,
                        "units": "metric",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            # Extract rainfall — OWM puts rain under "rain.1h" key
            rainfall = data.get("rain", {}).get("1h", 0.0)

            # Wind is in m/s — convert to km/h
            wind_kmh = data.get("wind", {}).get("speed", 0.0) * 3.6

            # Build location string: city + country
            city = data.get("name", "")
            country = data.get("sys", {}).get("country", "")
            location = f"{city}, {country}".strip(", ")

            result = WeatherResult(
                temperature_celsius=data["main"]["temp"],
                humidity_percent=data["main"]["humidity"],
                rainfall_mm=rainfall,
                wind_speed_kmh=wind_kmh,
                condition=data["weather"][0]["description"].title(),
                location=location or f"{latitude:.2f}, {longitude:.2f}",
                source="openweathermap",
            )

            logger.info(
                "Weather fetched (OWM): %s — %.1f°C, %.0f%% RH",
                result.location,
                result.temperature_celsius,
                result.humidity_percent,
            )
            return result

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "OWM API HTTP error %d: %s. Falling back to mock.",
                exc.response.status_code,
                exc.response.text[:200],
            )
        except httpx.RequestError as exc:
            logger.warning(
                "OWM API network error: %s. Falling back to mock.", exc
            )
        except (KeyError, ValueError) as exc:
            logger.warning(
                "OWM API response parse error: %s. Falling back to mock.", exc
            )
        except Exception as exc:
            logger.warning(
                "Unexpected weather error: %s. Falling back to mock.", exc
            )

        # Fall through to mock on any failure
        return self._mock_weather(latitude, longitude)

    @staticmethod
    def _mock_weather(latitude: float, longitude: float) -> WeatherResult:
        """Return randomised but realistic mock weather data."""
        result = WeatherResult(
            temperature_celsius=random.uniform(22.0, 35.0),
            humidity_percent=random.uniform(55.0, 85.0),
            rainfall_mm=random.uniform(0.0, 8.0),
            wind_speed_kmh=random.uniform(5.0, 25.0),
            condition=random.choice(MOCK_CONDITIONS),
            location="Pune, Maharashtra, India",
            source="mock",
        )
        logger.info(
            "Weather (mock): %.1f°C, %.0f%% RH, %s",
            result.temperature_celsius,
            result.humidity_percent,
            result.condition,
        )
        return result


# ─── Singleton ────────────────────────────────────────────────────────────────
weather_service = WeatherService()
