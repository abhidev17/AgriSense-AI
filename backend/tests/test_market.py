"""
API integration tests for GET /market.
"""

import pytest
from fastapi.testclient import TestClient


class TestMarketEndpoint:
    def test_missing_crop_returns_422(self, client: TestClient):
        """crop is a required query parameter."""
        response = client.get("/market")
        assert response.status_code == 422

    def test_valid_crop_returns_200(self, client: TestClient):
        response = client.get("/market", params={"crop": "Tomato"})
        assert response.status_code == 200

    def test_valid_crop_schema(self, client: TestClient):
        data = client.get("/market", params={"crop": "Tomato"}).json()
        assert "crop_name" in data
        assert "current_price_per_kg" in data
        assert "predicted_price_per_kg" in data
        assert "price_trend" in data
        assert "recommendation" in data
        assert "currency" in data
        assert "source" in data

    def test_crop_name_echoed_in_response(self, client: TestClient):
        data = client.get("/market", params={"crop": "Potato"}).json()
        assert data["crop_name"] == "Potato"

    def test_price_trend_values(self, client: TestClient):
        """price_trend must be one of the valid values."""
        data = client.get("/market", params={"crop": "Wheat"}).json()
        assert data["price_trend"] in ("up", "down", "stable")

    def test_prices_are_positive(self, client: TestClient):
        data = client.get("/market", params={"crop": "Apple"}).json()
        assert data["current_price_per_kg"] > 0
        assert data["predicted_price_per_kg"] > 0

    def test_short_crop_name_returns_422(self, client: TestClient):
        """min_length=2 on crop param."""
        response = client.get("/market", params={"crop": "T"})
        assert response.status_code == 422

    def test_unknown_crop_still_returns_data(self, client: TestClient):
        """Unknown crops should return mock data, not 404."""
        response = client.get("/market", params={"crop": "Durian"})
        assert response.status_code == 200
