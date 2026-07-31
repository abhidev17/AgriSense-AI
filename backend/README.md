# AgriSense AI — Backend

A production-ready **FastAPI** backend for the AgriSense AI agriculture assistant.  
Provides plant disease diagnosis via image analysis, enriched with real-time weather and commodity market data.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.115 |
| ASGI Server | Uvicorn |
| Database | MongoDB (async via Motor) |
| Image Processing | Pillow |
| AI (pending) | Google Gemini |
| Weather (pending) | OpenWeatherMap |
| Market (pending) | Agmarknet / data.gov.in |
| Validation | Pydantic v2 |
| Config | pydantic-settings + python-dotenv |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, middleware, exception handlers
│   ├── routes/
│   │   ├── diagnose.py          # POST /diagnose  — core diagnosis pipeline
│   │   ├── weather.py           # GET  /weather
│   │   ├── market.py            # GET  /market
│   │   ├── history.py           # GET|DELETE /history
│   │   └── health.py            # GET  /health
│   ├── services/
│   │   ├── crop_ai.py           # Crop detection (mock → real AI)
│   │   ├── disease_ai.py        # Disease detection (mock → real AI)
│   │   ├── gemini.py            # Gemini explanation generator (mock → API)
│   │   ├── weather.py           # OpenWeatherMap (mock → API)
│   │   ├── market.py            # Agmarknet prices (mock → API)
│   │   └── mongo.py             # MongoDB CRUD service
│   ├── database/
│   │   ├── mongodb.py           # Async Motor connection manager
│   │   └── models.py            # MongoDB document Pydantic models
│   ├── utils/
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── image.py             # Validation, save, metadata helpers
│   │   └── logger.py            # Rotating file + console logger
│   ├── schemas/
│   │   └── __init__.py          # API request/response Pydantic schemas
│   └── uploads/                 # Saved plant images (auto-organised by month)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Prerequisites

- Python 3.12+
- MongoDB running locally (or a MongoDB Atlas URI)

### 2. Clone & install

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your keys
```

Minimum required for the server to start (everything else is mock):

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=agrisense
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Server starts at **http://localhost:8000**

---

## API Documentation

| URL | Description |
|---|---|
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc (read-only) |
| http://localhost:8000/openapi.json | Raw OpenAPI schema |

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | API welcome & status |
| `GET` | `/health` | Health check (DB status) |
| `POST` | `/diagnose` | **Core** — plant disease diagnosis |
| `GET` | `/weather` | Current weather by coordinates |
| `GET` | `/market` | Commodity price by crop name |
| `GET` | `/history` | Paginated diagnosis history |
| `GET` | `/history/{session_id}` | Single diagnosis detail |
| `DELETE` | `/history/{session_id}` | Delete a diagnosis record |

---

## POST /diagnose — Form Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `image` | file | ✅ | Plant photo (JPEG / PNG / WebP, ≤ 10 MB) |
| `crop` | string | ❌ | Crop name (skips AI crop detection if provided) |
| `latitude` | float | ❌ | GPS latitude for weather lookup |
| `longitude` | float | ❌ | GPS longitude for weather lookup |

### Example Response

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "crop": { "name": "Tomato", "confidence": 0.97, "confidence_percent": "97.0%", "source": "ai" },
  "disease": { "name": "Early Blight", "confidence": 0.98, "severity": "moderate", "affected_area_percent": 35.0 },
  "explanation": "Early Blight has been detected on your Tomato crop…",
  "treatment_recommendations": ["Remove infected leaves immediately.", "Apply copper fungicide every 7–10 days."],
  "weather": { "temperature_celsius": 28.5, "humidity_percent": 72.0, "condition": "Partly Cloudy" },
  "market": { "current_price_per_kg": 22.5, "predicted_price_per_kg": 26.0, "price_trend": "up" },
  "processing_time_ms": 312.5
}
```

---

## Current State — Mock Services

All AI and external API services return **mock data** until real keys are configured:

| Service | Mock Behaviour | Activation |
|---|---|---|
| Crop AI | Returns "Tomato @ 97%" | Set model path in `crop_ai.py` |
| Disease AI | Returns "Early Blight @ 98%" | Set model path in `disease_ai.py` |
| Gemini | Returns a rich template explanation | Set `GEMINI_API_KEY` in `.env` |
| Weather | Returns randomised Pune weather | Set `OPENWEATHER_API_KEY` in `.env` |
| Market | Returns randomised ₹ prices | Set `MARKET_API_KEY` in `.env` |

---

## Error Codes

| HTTP Code | When |
|---|---|
| 400 | Invalid image (type, size, corrupted) or missing coordinates |
| 404 | Session ID not found in history |
| 422 | Form field validation failure |
| 500 | Unexpected server error |

---

## Development Tips

- All services are singletons — no need to instantiate them in routes.
- Weather and market failures are **non-fatal** — the diagnosis still succeeds.
- MongoDB unavailability is **non-fatal** — results are returned but not stored.
- Use `LOG_LEVEL=DEBUG` in `.env` for verbose request/response tracing.
