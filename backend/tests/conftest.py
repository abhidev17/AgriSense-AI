"""
Pytest configuration and shared fixtures for AgriSense AI tests.
"""

import io
import pytest
from PIL import Image as PILImage
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    FastAPI test client with lifespan events.
    MongoDB connection will attempt localhost; falls back gracefully.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Generate a minimal valid JPEG image in memory (100x100 green square)."""
    img = PILImage.new("RGB", (100, 100), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Generate a minimal valid PNG image in memory."""
    img = PILImage.new("RGB", (80, 80), color=(0, 128, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def tiny_text_bytes() -> bytes:
    """Return non-image bytes to test rejection of invalid file types."""
    return b"this is not an image file"
