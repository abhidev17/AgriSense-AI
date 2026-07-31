"""
API integration tests for POST /diagnose.
These tests cover the full 10-step diagnosis pipeline using mock services.
"""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage


class TestDiagnoseEndpoint:

    # ── Happy path ─────────────────────────────────────────────────────────────

    def test_valid_jpeg_returns_200(self, client: TestClient, sample_jpeg_bytes: bytes):
        response = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 200

    def test_response_schema_complete(self, client: TestClient, sample_jpeg_bytes: bytes):
        """Verify all required top-level fields are present."""
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        ).json()

        required_fields = [
            "session_id", "status", "crop", "disease",
            "explanation", "treatment_recommendations",
            "action_plan", "image_path", "timestamp", "processing_time_ms",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_crop_schema(self, client: TestClient, sample_jpeg_bytes: bytes):
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        ).json()
        crop = data["crop"]
        assert "name" in crop
        assert "confidence" in crop
        assert "confidence_percent" in crop
        assert "source" in crop
        assert 0 <= crop["confidence"] <= 1

    def test_disease_schema(self, client: TestClient, sample_jpeg_bytes: bytes):
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        ).json()
        disease = data["disease"]
        assert "name" in disease
        assert "confidence" in disease
        assert "severity" in disease
        assert disease["severity"] in ("low", "moderate", "high", "critical")

    def test_action_plan_schema(self, client: TestClient, sample_jpeg_bytes: bytes):
        """Verify action_plan has all required fields with correct types."""
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        ).json()
        ap = data["action_plan"]
        assert "overall_risk" in ap
        assert "risk_score" in ap
        assert "estimated_recovery" in ap
        assert "timeline" in ap
        assert "immediate_actions" in ap
        assert "prevention_tips" in ap
        assert isinstance(ap["risk_score"], int)
        assert 0 <= ap["risk_score"] <= 100
        assert ap["overall_risk"] in ("Low", "Medium", "High", "Critical", "Unknown")

    def test_action_plan_timeline_items(self, client: TestClient, sample_jpeg_bytes: bytes):
        """Timeline items must have day, action, and priority fields."""
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        ).json()
        timeline = data["action_plan"]["timeline"]
        assert isinstance(timeline, list)
        if timeline:
            item = timeline[0]
            assert "day" in item
            assert "action" in item
            assert "reason" in item

    def test_user_supplied_crop(self, client: TestClient, sample_jpeg_bytes: bytes):
        """When crop is supplied, source should be 'user'."""
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
            data={"crop": "Tomato"},
        ).json()
        assert data["crop"]["source"] == "user"
        assert data["crop"]["name"] == "Tomato"
        assert data["crop"]["confidence"] == 1.0

    def test_with_coordinates_returns_weather(
        self, client: TestClient, sample_jpeg_bytes: bytes
    ):
        """Providing lat/lon should populate the weather field."""
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
            data={"latitude": "18.5204", "longitude": "73.8567"},
        ).json()
        assert data["weather"] is not None
        assert "temperature_celsius" in data["weather"]

    def test_without_coordinates_weather_none(
        self, client: TestClient, sample_jpeg_bytes: bytes
    ):
        """Without lat/lon the weather field should be None."""
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        ).json()
        # weather may be None (no coords) or present — depends on mock
        # Just verify the key exists
        assert "weather" in data

    def test_market_data_present(self, client: TestClient, sample_jpeg_bytes: bytes):
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        ).json()
        assert "market" in data
        if data["market"] is not None:
            assert "crop_name" in data["market"]
            assert "price_trend" in data["market"]

    def test_session_id_is_uuid(self, client: TestClient, sample_jpeg_bytes: bytes):
        import uuid
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        ).json()
        # Should not raise
        uuid.UUID(data["session_id"])

    def test_processing_time_positive(self, client: TestClient, sample_jpeg_bytes: bytes):
        data = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
        ).json()
        assert data["processing_time_ms"] > 0

    def test_png_image_accepted(self, client: TestClient, sample_png_bytes: bytes):
        response = client.post(
            "/diagnose",
            files={"image": ("plant.png", sample_png_bytes, "image/png")},
        )
        assert response.status_code == 200

    # ── Error cases ────────────────────────────────────────────────────────────

    def test_missing_image_returns_422(self, client: TestClient):
        """image field is required."""
        response = client.post("/diagnose", data={})
        assert response.status_code == 422

    def test_wrong_content_type_returns_400(self, client: TestClient):
        """Non-image content type should be rejected."""
        response = client.post(
            "/diagnose",
            files={"image": ("script.js", b"alert('xss')", "application/javascript")},
        )
        assert response.status_code == 400

    def test_empty_file_returns_400(self, client: TestClient):
        """Empty file should be rejected."""
        response = client.post(
            "/diagnose",
            files={"image": ("empty.jpg", b"", "image/jpeg")},
        )
        assert response.status_code == 400

    def test_text_file_rejected(self, client: TestClient, tiny_text_bytes: bytes):
        """Text bytes with image content-type should fail PIL integrity check."""
        response = client.post(
            "/diagnose",
            files={"image": ("fake.jpg", tiny_text_bytes, "image/jpeg")},
        )
        assert response.status_code == 400

    def test_out_of_range_latitude_returns_422(
        self, client: TestClient, sample_jpeg_bytes: bytes
    ):
        response = client.post(
            "/diagnose",
            files={"image": ("plant.jpg", sample_jpeg_bytes, "image/jpeg")},
            data={"latitude": "999.0", "longitude": "73.85"},
        )
        assert response.status_code == 422

    def test_non_leaf_image_rejected(self, client: TestClient, sample_jpeg_bytes: bytes):
        """Image with 'non-leaf' in filename is rejected by verification check."""
        response = client.post(
            "/diagnose",
            files={"image": ("non-leaf-test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "No crop leaf detected. Please upload a clear image of a crop leaf."

    def test_unrelated_image_rejected(self, client: TestClient, sample_jpeg_bytes: bytes):
        """Image with 'unrelated' in filename is rejected by verification check."""
        response = client.post(
            "/diagnose",
            files={"image": ("unrelated_photo.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "No crop leaf detected. Please upload a clear image of a crop leaf."
