"""
Image utility helpers for AgriSense AI.
Handles validation, saving, and basic processing of uploaded images.
"""

import uuid
import mimetypes
from pathlib import Path
from datetime import datetime

from fastapi import HTTPException, UploadFile, status
from PIL import Image as PILImage

from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()


# ─── Validation ───────────────────────────────────────────────────────────────


async def validate_image(file: UploadFile) -> bytes:
    """
    Read and validate an uploaded image file.

    Checks:
      - Content-Type against the allow-list.
      - File size against the configured maximum.
      - That the bytes represent a real, parseable image.

    Args:
        file: The FastAPI UploadFile object.

    Returns:
        Raw image bytes.

    Raises:
        HTTPException 400: If the file fails any validation check.
    """
    # ── Content-Type check ────────────────────────────────────────────────────
    content_type = file.content_type or ""
    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported image type '{content_type}'. "
                f"Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            ),
        )

    # ── Read bytes ────────────────────────────────────────────────────────────
    image_bytes = await file.read()

    # ── Size check ────────────────────────────────────────────────────────────
    size_bytes = len(image_bytes)
    if size_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if size_bytes > settings.max_image_size_bytes:
        max_mb = settings.MAX_IMAGE_SIZE_MB
        actual_mb = round(size_bytes / (1024 * 1024), 2)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image size {actual_mb} MB exceeds the {max_mb} MB limit.",
        )

    # ── PIL integrity check ───────────────────────────────────────────────────
    try:
        import io
        img = PILImage.open(io.BytesIO(image_bytes))
        img.verify()  # Raises if file is corrupted
    except Exception as exc:
        logger.warning("Image integrity check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid image or is corrupted.",
        )

    logger.debug(
        "Image validated — type: %s, size: %s bytes", content_type, size_bytes
    )
    return image_bytes


# ─── Persistence ──────────────────────────────────────────────────────────────


def save_image(image_bytes: bytes, original_filename: str | None = None) -> str:
    """
    Save raw image bytes to the configured uploads directory with a unique name.

    Args:
        image_bytes:       Raw bytes of the validated image.
        original_filename: Original filename (used for extension detection).

    Returns:
        Relative file path string (e.g. ``app/uploads/2024-01/abc123.jpg``).
    """
    upload_dir = Path(settings.UPLOAD_DIR)

    # Organise uploads by year-month to avoid huge flat directories
    month_dir = upload_dir / datetime.utcnow().strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)

    # Determine extension from original filename or default to .jpg
    ext = ".jpg"
    if original_filename:
        suffix = Path(original_filename).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = suffix

    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = month_dir / unique_name

    file_path.write_bytes(image_bytes)
    logger.info("Image saved → %s", file_path)

    return str(file_path)


# ─── Metadata ─────────────────────────────────────────────────────────────────


def get_image_metadata(image_bytes: bytes) -> dict:
    """
    Extract basic metadata from image bytes using Pillow.

    Args:
        image_bytes: Raw image bytes.

    Returns:
        Dict with width, height, mode, and format fields.
    """
    import io

    try:
        img = PILImage.open(io.BytesIO(image_bytes))
        return {
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "format": img.format or "unknown",
        }
    except Exception as exc:
        logger.warning("Could not extract image metadata: %s", exc)
        return {}
