"""
API integration tests for GET /history endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestHistoryEndpoint:
    def test_list_history_returns_200(self, client: TestClient):
        response = client.get("/history")
        assert response.status_code == 200

    def test_list_history_schema(self, client: TestClient):
        data = client.get("/history").json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_pagination_defaults(self, client: TestClient):
        data = client.get("/history").json()
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_custom_page_size(self, client: TestClient):
        data = client.get("/history", params={"page_size": 5}).json()
        assert data["page_size"] == 5

    def test_invalid_page_size_returns_422(self, client: TestClient):
        """page_size must be between 1 and 100."""
        response = client.get("/history", params={"page_size": 200})
        assert response.status_code == 422

    def test_crop_filter_param_accepted(self, client: TestClient):
        """Crop filter should not cause a server error."""
        response = client.get("/history", params={"crop": "Tomato"})
        assert response.status_code == 200

    def test_disease_filter_param_accepted(self, client: TestClient):
        response = client.get("/history", params={"disease": "Blight"})
        assert response.status_code == 200

    def test_min_risk_score_filter(self, client: TestClient):
        response = client.get("/history", params={"min_risk_score": 60})
        assert response.status_code == 200

    def test_nonexistent_session_returns_404(self, client: TestClient):
        response = client.get("/history/nonexistent-session-id-12345")
        assert response.status_code == 404

    def test_delete_nonexistent_returns_404(self, client: TestClient):
        response = client.delete("/history/nonexistent-session-id-99999")
        assert response.status_code == 404

    def test_stats_endpoint_returns_200(self, client: TestClient):
        response = client.get("/history/stats")
        assert response.status_code == 200

    def test_stats_returns_dict(self, client: TestClient):
        data = client.get("/history/stats").json()
        assert isinstance(data, dict)

    def test_search_param_accepted(self, client: TestClient):
        response = client.get("/history", params={"search": "tomato blight"})
        assert response.status_code == 200

    def test_search_too_short_returns_422(self, client: TestClient):
        """min_length=2 on search param."""
        response = client.get("/history", params={"search": "a"})
        assert response.status_code == 422
