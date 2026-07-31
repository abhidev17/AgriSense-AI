"""
Configuration module for AgriSense AI backend.
All settings are loaded from environment variables via .env file.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic-settings for automatic validation and type coercion.
    """

    # ─── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = Field(default="AgriSense AI", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="API version")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    # ─── MongoDB ───────────────────────────────────────────────────────────────
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string",
    )
    MONGODB_DB_NAME: str = Field(
        default="agrisense",
        description="MongoDB database name",
    )

    # ─── File Uploads ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = Field(default="app/uploads", description="Upload directory path")
    MAX_IMAGE_SIZE_MB: int = Field(default=10, description="Max image size in MB")
    ALLOWED_IMAGE_TYPES: list[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "image/jpg"],
        description="Allowed MIME types for uploaded images",
    )

    # ─── AI Services (placeholders) ────────────────────────────────────────────
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(
        default="gemini-1.5-flash", description="Gemini model name"
    )

    # ─── Weather API (placeholder) ─────────────────────────────────────────────
    OPENWEATHER_API_KEY: str = Field(
        default="", description="OpenWeatherMap API key"
    )
    OPENWEATHER_BASE_URL: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        description="OpenWeatherMap base URL",
    )

    # ─── Market API (placeholder) ──────────────────────────────────────────────
    MARKET_API_KEY: str = Field(default="", description="Market data API key")
    MARKET_API_BASE_URL: str = Field(
        default="https://api.data.gov.in",
        description="Agmarknet / Market API base URL",
    )

    # ─── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )

    # ─── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="agrisense.log", description="Log file path")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def max_image_size_bytes(self) -> int:
        """Return max image size in bytes."""
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """
    Return cached Settings instance.
    Uses lru_cache so the .env file is read only once per process.
    """
    return Settings()
