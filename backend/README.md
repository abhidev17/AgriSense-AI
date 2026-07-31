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
| AI Framework | PyTorch (EfficientNet-B0 fine-tuned) |
| Generative AI | Google Gemini (google-generativeai SDK) |
| Weather | OpenWeatherMap |
| Market | Agmarknet / data.gov.in |
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
│   │   ├── crop_ai.py           # Crop detection (real PyTorch model inference)
│   │   ├── disease_ai.py        # Disease detection (real PyTorch model inference)
│   │   ├── gemini.py            # Gemini explanation generator (structured JSON + Fallback)
│   │   ├── action_plan.py       # Recovery Action Plan Generator (Gemini + Rule-based fallback)
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
├── ai/
│   ├── dataset.py               # PlantVillage PyTorch Dataset class
│   ├── utils.py                 # Dataset loader splits & classes.json generation
│   ├── train_crop.py            # Training script for crop classification
│   ├── train_disease.py         # Training script for disease classification
│   └── inference.py             # Unified lazy-loading inference module
├── models/
│   ├── crop_model.pth           # Saved weights for the crop classifier
│   ├── disease_model.pth        # Saved weights for the disease classifier
│   └── classes.json             # Model class mappings (generated during training)
├── datasets/
│   └── PlantVillage/            # PlantVillage dataset folder
├── requirements.txt
├── .env.example
├── .env
└── README.md
```

---

## AI Layer & Model Training

AgriSense AI utilizes a hierarchical ML pipeline with two fine-tuned deep learning classifiers built on PyTorch.

### 1. Dataset Setup
The dataset used is the standard **PlantVillage** dataset. Ensure the folder structure is organized under `backend/datasets/PlantVillage` with folders named like `Crop___Disease` (e.g. `Tomato___Early_blight`, `Tomato___healthy`, etc.).

Supported Crops:
- Tomato
- Potato
- Pepper
- Corn
- Apple
- Cherry
- Grape
- Peach
- Strawberry
- Soybean

### 2. Training Models
Make sure your working directory is `backend/ai/`. Run the following training commands to fine-tune the classifiers on the PlantVillage dataset:

```bash
cd backend/ai

# Train the Crop Classifier
python train_crop.py

# Train the Disease Classifier
python train_disease.py
```

*Note:* The training scripts automatically scan `backend/datasets/PlantVillage`, execute a train/validation split (80/20 stratified), train using an Adam optimizer with CrossEntropyLoss, and save the best-performing weights (`crop_model.pth` and `disease_model.pth`) alongside the mappings configuration file (`classes.json`) into the `backend/models/` directory.

#### Fast Weight Generation (QUICK_GEN Mode)
For testing and rapid CI environments, a `QUICK_GEN = True` flag can be set inside `train_crop.py` and `train_disease.py`. This subsets the dataset to a few samples and trains for a single epoch to verify the pipeline and output matching weights in seconds.

---

## Inference Service & Lazy Loading

Model loading is handled lazily in `backend/ai/inference.py` to ensure fast startup speeds:
- PyTorch models are loaded only when the first `/diagnose` request is received.
- Subsequent calls reuse the loaded models kept in memory.
- Inference functions support both local image paths and raw image bytes.

### Hierarchical Crop Filtering
During disease classification, `disease_ai.py` fetches the raw predictions of the 38-class disease classifier and filters them dynamically to only match classes matching the detected crop. This prevents cross-crop false positives (e.g. predicting a Tomato disease on a Potato leaf).

---

## Gemini Configuration & Explanation Generator

The diagnosis natural language explanation is generated via the Google Gemini API. 

### 1. Configuration
To activate Gemini, create a `.env` file in the `backend/` directory and configure your API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

### 2. Output Schema
The Gemini service requests a structured JSON response from Gemini, matching this format:

```json
{
    "summary": "A farmer-friendly summary of the disease and current weather risk.",
    "features": ["Visual feature 1", "Visual feature 2"],
    "treatment": ["Immediate treatment step 1", "Immediate treatment step 2"],
    "fertilizer": "NPK or fertilizer recommendation"
}
```

### 3. Graceful Fallback
If `GEMINI_API_KEY` is not set, or if an API error occurs (network issues, rate limits), the backend **gracefully falls back** to a local rule-based expert engine to generate the structured diagnosis explanation. The FastAPI application will never crash.

---

## Recovery Action Planner

The Action Plan service (`action_plan.py`) generates a structured recovery action plan with:
- `overall_risk` (Low | Medium | High | Critical)
- `risk_score` (0-100) calculated from severity, temperature, humidity, and crop value.
- `estimated_recovery` (e.g. 90-95%)
- `timeline` containing day-by-day actions for `Today`, `Tomorrow`, `After 3 Days`, `Next Week`, and `Harvest` (incorporating current date, rain forecast, and market trend).

If Gemini is available, it is used to write a highly tailored recovery plan. If Gemini is not set or fails, the service falls back to a deterministic rule-based engine.

---

## Running the Backend Locally

### 1. Clone & install dependencies
Ensure you are using Python 3.11+.

```bash
cd backend
python -m venv venv

# Activate virtualenv (Windows)
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Run the server
Ensure MongoDB is running locally.

```bash
uvicorn app.main:app --reload
```

---

## Running Tests

Run the full integration and unit test suite using `pytest`:

```bash
python -m pytest
```
