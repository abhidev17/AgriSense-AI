"""
AgriSense AI — FastAPI Application Entry Point

Architecture overview:
  app/
    main.py              ← You are here: lifespan, middleware, routers, exception handlers
    routes/              ← HTTP route handlers (thin layer, delegates to services)
    services/            ← Business logic + AI / external API integrations
    database/            ← MongoDB connection & document models
    utils/               ← Config, logger, image helpers
    schemas/             ← Pydantic request/response models for the API layer

Run with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.database.mongodb import mongodb_manager
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
    Code before ``yield`` runs at startup; code after runs at shutdown.
    """
    logger.info("=========================================")
    logger.info("  AgriSense AI backend starting up...")
    logger.info("  Version  : %s", settings.APP_VERSION)
    logger.info("  Debug    : %s", settings.DEBUG)
    logger.info("=========================================")

    # Connect to MongoDB
    await mongodb_manager.connect()

    # Ensure uploads directory exists
    from pathlib import Path
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("Upload directory ready: %s", settings.UPLOAD_DIR)

    yield  # ← Application runs here

    # Graceful shutdown
    await mongodb_manager.close()
    logger.info("AgriSense AI backend shut down cleanly.")


# ─── FastAPI application ───────────────────────────────────────────────────────


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "## AgriSense AI — Plant Disease Diagnosis API\n\n"
        "An AI-powered agriculture assistant that detects crop diseases from images, "
        "enriches results with real-time weather and market data, and provides "
        "actionable, farmer-friendly recommendations.\n\n"
        "### AI Services (mock mode)\n"
        "- **Crop Detection** — Identifies the crop species in an uploaded image.\n"
        "- **Disease Detection** — Detects diseases and estimates severity.\n"
        "- **Gemini Explanation** — Generates a natural-language diagnosis explanation.\n\n"
        "### Data Enrichment\n"
        "- **Weather** — Temperature, humidity, and rainfall via OpenWeatherMap.\n"
        "- **Market** — Commodity prices and trend recommendations via Agmarknet.\n\n"
        "> **Note:** All AI and external API services are currently returning mock data. "
        "Real integrations will be enabled once API keys are configured in `.env`."
    ),
    contact={
        "name": "AgriSense AI Team",
        "email": "support@agrisense.ai",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ─── CORS Middleware ───────────────────────────────────────────────────────────


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
    """
    Return HTTP 422 with a structured error body for Pydantic validation failures.
    Provides detailed field-level error messages.
    """
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error.get("loc", []))
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
    """
    Return a consistent JSON envelope for all HTTP errors.
    """
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
    """
    Catch-all handler for unexpected server errors.
    Logs the full traceback and returns HTTP 500.
    """
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


# ─── Root endpoint ─────────────────────────────────────────────────────────────


@app.get(
    "/",
    response_model=RootResponse,
    summary="API Root",
    description="Returns a welcome message and links to the API documentation.",
    tags=["Root"],
)
async def root() -> RootResponse:
    """
    Root endpoint.
    Returns backend status and a link to the Swagger docs.
    """
    return RootResponse(
        message=f"Welcome to {settings.APP_NAME} API",
        version=settings.APP_VERSION,
        docs_url="/docs",
        status="running",
    )