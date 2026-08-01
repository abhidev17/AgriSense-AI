"""
AgriSense AI — FastAPI Application Entry Point (v1.1.0)

Phase 2 additions:
  - RequestLoggingMiddleware registered
  - MongoDB indexes created on startup
  - New /history/stats route available
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.database.mongodb import mongodb_manager
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.routes import diagnose, health, history, market, weather
from app.schemas import ErrorResponse, RootResponse
from app.utils.config import get_settings
from app.utils.logger import logger, setup_logger

settings = get_settings()

# Re-configure logger with values from .env
setup_logger(level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)


# ─── Lifespan (startup / shutdown) ────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    FastAPI lifespan context manager.
    Startup: connect DB, create indexes, ensure upload dir.
    Shutdown: close DB connection.
    """
    logger.info("=========================================")
    logger.info("  AgriSense AI backend starting up...")
    logger.info("  Version  : %s", settings.APP_VERSION)
    logger.info("  Debug    : %s", settings.DEBUG)
    logger.info("=========================================")

    # Connect to MongoDB (also creates indexes)
    await mongodb_manager.connect()

    # Ensure uploads directory exists
    from pathlib import Path
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("Upload directory ready: %s", settings.UPLOAD_DIR)

    yield  # Application runs here

    # Graceful shutdown
    await mongodb_manager.close()
    logger.info("AgriSense AI backend shut down cleanly.")


# ─── FastAPI application ───────────────────────────────────────────────────────


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "## AgriSense AI - Plant Disease Diagnosis API\n\n"
        "An AI-powered agriculture assistant that detects crop diseases from images, "
        "generates a risk-scored **Action Plan**, and enriches results with real-time "
        "weather and market data.\n\n"
        "### Services\n"
        "- **Crop Detection** - Identifies the crop species.\n"
        "- **Disease Detection** - Detects diseases and estimates severity.\n"
        "- **Gemini AI** - Generates farmer-friendly explanations (real or mock).\n"
        "- **Weather** - Temperature, humidity, rainfall via OpenWeatherMap (real or mock).\n"
        "- **Market** - Commodity prices and trends via Agmarknet (real or mock).\n"
        "- **Action Plan** - Risk-scored recovery timeline (always computed).\n\n"
        "> Services marked 'real or mock' activate automatically when API keys "
        "are set in `.env`."
    ),
    contact={"name": "AgriSense AI Team", "email": "support@agrisense.ai"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ─── Middleware ────────────────────────────────────────────────────────────────

# 1. Request logging (innermost — wraps all requests)
app.add_middleware(RequestLoggingMiddleware)

# 2. CORS (outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Exception Handlers ───────────────────────────────────────────────────────


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """HTTP 422 with structured field-level error messages."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        errors.append(f"{field}: {error.get('msg', 'validation error')}")

    logger.warning("Validation error on %s: %s", request.url.path, errors)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed.",
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Consistent JSON envelope for all HTTP errors."""
    logger.warning(
        "HTTP %d on %s: %s", exc.status_code, request.url.path, exc.detail
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected server errors — logs full traceback."""
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected internal server error occurred.",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(diagnose.router)
app.include_router(weather.router)
app.include_router(market.router)
app.include_router(history.router)


# ─── Root ─────────────────────────────────────────────────────────────────────


@app.get(
    "/",
    response_model=RootResponse,
    summary="API Root",
    description="Returns a welcome message and links to the API documentation.",
    tags=["Root"],
)
async def root() -> RootResponse:
    """Root endpoint — API status and docs link."""
    return RootResponse(
        message=f"Welcome to {settings.APP_NAME} API",
        version=settings.APP_VERSION,
        docs_url="/docs",
        status="running",
    )