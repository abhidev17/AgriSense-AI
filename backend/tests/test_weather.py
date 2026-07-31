"""
API integration tests for GET /weather.
"""

import pytest
from fastapi.testclient import TestClient


class TestWeatherEndpoint:
    def test_missing_params_returns_400(self, client: TestClient):
        """Both latitude and longitude are required."""
        response = client.get("/weather")
        assert response.status_code == 400

    def test_only_lat_returns_400(self, client: TestClient):
        response = client.get("/weather", params={"latitude": 18.52})
        assert response.status_code == 400

    def test_only_lon_returns_400(self, client: TestClient):
        response = client.get("/weather", params={"longitude": 73.85})
        assert response.status_code == 400

    def test_valid_coords_returns_200(self, client: TestClient):
        response = client.get(
            "/weather", params={"latitude": 18.5204, "longitude": 73.8567}
        )
        assert response.status_code == 200

    def test_valid_coords_schema(self, client: TestClient):
        data = client.get(
            "/weather", params={"latitude": 18.5204, "longitude": 73.8567}
        ).json()
        assert "temperature_celsius" in data
        assert "humidity_percent" in data
        assert "condition" in data
        assert "source" in data

    def test_out_of_range_latitude_returns_422(self, client: TestClient):
        response = client.get(
            "/weather", params={"latitude": 200.0, "longitude": 73.85}
        )
        assert response.status_code == 422

    def test_out_of_range_longitude_returns_422(self, client: TestClient):
        response = client.get(
            "/weather", params={"latitude": 18.52, "longitude": 300.0}
        )
        assert response.status_code == 422

    def test_source_field_is_string(self, client: TestClient):
        data = client.get(
            "/weather", params={"latitude": 18.5204, "longitude": 73.8567}
        ).json()
        assert isinstance(data["source"], str)
        assert data["source"] in ("openweathermap", "mock")
