"""
API integration tests for GET / and GET /health.
"""

import pytest
from fastapi.testclient import TestClient


class TestRoot:
    def test_root_returns_200(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_schema(self, client: TestClient):
        data = client.get("/").json()
        assert "message" in data
        assert "version" in data
        assert "docs_url" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_root_docs_url(self, client: TestClient):
        data = client.get("/").json()
        assert data["docs_url"] == "/docs"


class TestHealth:
    def test_health_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_schema(self, client: TestClient):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "version" in data
        assert "timestamp" in data

    def test_health_database_field(self, client: TestClient):
        data = client.get("/health").json()
        assert data["database"] in ("connected", "disconnected")

    def test_health_has_x_request_id_header(self, client: TestClient):
        """Verify logging middleware injects X-Request-ID."""
        response = client.get("/health")
        assert "x-request-id" in response.headers

    def test_health_has_process_time_header(self, client: TestClient):
        """Verify logging middleware injects X-Process-Time-Ms."""
        response = client.get("/health")
        assert "x-process-time-ms" in response.headers
