"""
Market data service for AgriSense AI.

PLACEHOLDER IMPLEMENTATION
──────────────────────────
This module defines the interface for fetching agricultural commodity prices.
Agmarknet / data.gov.in API (or a similar market data provider) will be
integrated here once an API key is available.

Current behaviour: returns realistic mock market data.
"""

import random
from typing import Optional

from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()

# ─── Mock price ranges per crop (₹/kg) ────────────────────────────────────────
CROP_PRICE_RANGES: dict[str, tuple[float, float]] = {
    "Tomato":       (12.0,  45.0),
    "Potato":       (10.0,  28.0),
    "Corn (Maize)": (18.0,  32.0),
    "Wheat":        (20.0,  30.0),
    "Rice":         (25.0,  50.0),
    "Bell Pepper":  (30.0,  80.0),
    "Apple":        (60.0, 150.0),
    "Grape":        (40.0, 120.0),
    "Onion":        (10.0,  40.0),
    "Soybean":      (35.0,  55.0),
}

DEFAULT_PRICE_RANGE = (15.0, 50.0)

TREND_RECOMMENDATIONS: dict[str, str] = {
    "up": (
        "Prices are trending upward. Consider holding stock for 2–3 weeks "
        "to maximise returns if storage is available."
    ),
    "down": (
        "Prices are declining. Consider selling soon to avoid further losses, "
        "or explore value-added processing options."
    ),
    "stable": (
        "Prices are stable. A good time to sell at current market rates "
        "or plan phased sales over the next month."
    ),
}


class MarketResult:
    """
    Data class holding a market price snapshot for a crop.

    Attributes:
        crop_name:               Crop for which prices are reported.
        current_price_per_kg:    Current wholesale price (₹/kg).
        predicted_price_per_kg:  30-day price prediction (₹/kg).
        price_trend:             'up' | 'down' | 'stable'.
        recommendation:          Market action recommendation.
        currency:                Price currency code ('INR').
        source:                  'agmarknet' | 'mock'.
    """

    def __init__(
        self,
        crop_name: str,
        current_price_per_kg: float,
        predicted_price_per_kg: float,
        price_trend: str,
        recommendation: str,
        currency: str = "INR",
        source: str = "mock",
    ) -> None:
        self.crop_name = crop_name
        self.current_price_per_kg = current_price_per_kg
        self.predicted_price_per_kg = predicted_price_per_kg
        self.price_trend = price_trend
        self.recommendation = recommendation
        self.currency = currency
        self.source = source

    def to_dict(self) -> dict:
        return {
            "crop_name": self.crop_name,
            "current_price_per_kg": self.current_price_per_kg,
            "predicted_price_per_kg": self.predicted_price_per_kg,
            "price_trend": self.price_trend,
            "recommendation": self.recommendation,
            "currency": self.currency,
            "source": self.source,
        }


class MarketService:
    """
    Service that fetches commodity price data for a given crop.

    Integration points (TODO when API key is available):
      - Set MARKET_API_KEY and MARKET_API_BASE_URL in .env
      - Replace mock block in ``get_market_data`` with a real httpx call.
      - Possible sources:
          * Agmarknet (data.gov.in/resource/…)
          * NHRDF onion/garlic prices
          * Custom commodity price microservice
    """

    def __init__(self) -> None:
        self._api_key = settings.MARKET_API_KEY
        self._base_url = settings.MARKET_API_BASE_URL
        logger.info(
            "MarketService initialised — API key %s.",
            "present" if self._api_key else "NOT SET (mock mode)",
        )

    async def get_market_data(self, crop_name: str) -> Optional[MarketResult]:
        """
        Fetch current and predicted prices for the given crop.

        Args:
            crop_name: Crop species name (e.g. 'Tomato').

        Returns:
            MarketResult, or None if crop_name is empty / unknown.

        TODO:
            Replace mock block with real API call:

            .. code-block:: python

                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{self._base_url}/prices",
                        params={"crop": crop_name, "api-key": self._api_key},
                        timeout=10.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()["records"][0]
                    return MarketResult(
                        crop_name=crop_name,
                        current_price_per_kg=float(data["modal_price"]) / 100,
                        predicted_price_per_kg=...,
                        price_trend=...,
                        recommendation=...,
                        source="agmarknet",
                    )
        """
        if not crop_name:
            return None

        logger.debug("get_market_data() — crop=%s (mock mode)", crop_name)

        # ── MOCK RESPONSE ─────────────────────────────────────────────────────
        low, high = CROP_PRICE_RANGES.get(crop_name, DEFAULT_PRICE_RANGE)
        current_price = round(random.uniform(low, high), 2)

        # Simulate a predicted price within ±20% of current
        delta_pct = random.uniform(-0.10, 0.20)
        predicted_price = round(current_price * (1 + delta_pct), 2)

        if delta_pct > 0.05:
            trend = "up"
        elif delta_pct < -0.05:
            trend = "down"
        else:
            trend = "stable"

        recommendation = TREND_RECOMMENDATIONS[trend]

        result = MarketResult(
            crop_name=crop_name,
            current_price_per_kg=current_price,
            predicted_price_per_kg=predicted_price,
            price_trend=trend,
            recommendation=recommendation,
            source="mock",
        )

        logger.info(
            "Market data fetched (mock): %s @ ₹%.2f/kg | trend=%s",
            crop_name,
            current_price,
            trend,
        )
        return result

    async def get_price_history(
        self, crop_name: str, days: int = 30
    ) -> list[dict]:
        """
        Return historical daily prices for the given crop.

        TODO: Implement using a real market data API.

        Returns:
            List of {'date': str, 'price': float} dicts (mock: empty list).
        """
        logger.debug("get_price_history() — not yet implemented (returning []).")
        return []


# ─── Singleton ────────────────────────────────────────────────────────────────
market_service = MarketService()
