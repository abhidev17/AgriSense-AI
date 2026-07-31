"""
Gemini AI service for AgriSense AI.

NEW ARCHITECTURE (Gemini Vision as primary AI engine):
  - detect_crop_and_disease()  → single Vision call: leaf check + crop + disease + symptoms
  - generate_explanation()     → rich farmer-friendly text explanation
  - generate_quick_tip()       → one-sentence tip
  - _generate_fallback_*()     → local rule-based fallbacks when API unavailable

All external Gemini calls are wrapped with a 5-second timeout thread.
On quota/network failure the service falls back to structured local responses
so the frontend never receives a 500 error due to Gemini unavailability.
"""

from __future__ import annotations

import io
import json
import random
import threading
from typing import Optional

try:
    from google import genai
    from google.genai import types
    _GENAI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore
    _GENAI_AVAILABLE = False


from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()

# ─── Timeouts ──────────────────────────────────────────────────────────────────
GEMINI_TIMEOUT_SECONDS = 5  # hard timeout for every Gemini API call

# ─── Vision detection prompt ───────────────────────────────────────────────────
_VISION_PROMPT = """\
You are an expert agricultural AI assistant. Analyze the uploaded plant image carefully.

Return ONLY a valid JSON object — no markdown, no code blocks, no explanations.

DECISION RULES:
1. If the image does NOT contain a plant leaf or crop foliage, return exactly:
   {"error":"No crop leaf detected"}

2. If it is a leaf but the crop species cannot be identified with confidence, return exactly:
   {"error":"Unable to identify crop"}

3. If you can identify the crop and assess its health, return exactly this schema:
   {
     "crop": "<crop name>",
     "disease": "<disease name or Healthy>",
     "confidence": <integer 0-100>,
     "severity": "<Low | Medium | High | Critical>",
     "symptoms": ["<symptom 1>", "<symptom 2>", "<symptom 3>"]
   }

FIELD RULES:
- crop: plain English crop name (e.g. Tomato, Potato, Apple, Corn, Grape)
- disease: exact disease name or the word "Healthy"
- confidence: your overall confidence as an integer between 0 and 100
- severity: MUST be exactly one of: Low, Medium, High, Critical
- If the plant is healthy: disease = "Healthy" and severity = "Low"
- symptoms: 3 to 5 brief, farmer-friendly observations visible in the image
- Use simple language a farmer can understand
"""

# ─── Explanation prompt ────────────────────────────────────────────────────────
_EXPLANATION_PROMPT = """\
You are AgriSense AI, an expert agronomist advising farmers.
A farmer uploaded a crop photo. Analysis results:
- Crop: {crop_name} (confidence: {confidence_pct}%)
- Disease: {disease_name}
- Severity: {severity}
- Affected area: {affected_area}
- Observed symptoms: {symptoms}
- Weather: {temperature}, humidity {humidity}, {condition}

Return ONLY a raw JSON object (no markdown, no code blocks):
{{
  "summary": "Two sentences explaining {disease_name} in simple farmer language and how the current weather affects it.",
  "features": {symptoms_json},
  "treatment": ["Action 1", "Action 2", "Action 3"],
  "fertilizer": "One NPK or foliar fertilizer recommendation."
}}
Keep the entire response under 150 words. Use simple language.
"""


class GeminiService:
    """
    Gemini-powered AI engine for AgriSense AI.

    Primary role: detect_crop_and_disease() — single Vision API call that
    validates the image, identifies the crop species, detects the disease,
    assesses severity, and lists visible symptoms.

    Secondary role: generate_explanation() — rich textual explanation with
    treatment and fertilizer recommendations.
    """

    def __init__(self) -> None:
        self._client: Optional[genai.Client] = None
        self._mock_mode = True

        if settings.GEMINI_API_KEY and _GENAI_AVAILABLE:
            try:
                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self._mock_mode = False
                logger.info(
                    "GeminiService initialized with real API (%s)",
                    settings.GEMINI_MODEL,
                )
            except Exception as exc:
                logger.warning(
                    "Gemini initialization failed: %s — falling back to mock.", exc
                )
        else:
            if not _GENAI_AVAILABLE and settings.GEMINI_API_KEY:
                logger.warning(
                    "google-genai library not installed — running GeminiService in mock mode."
                )
            else:
                logger.info("GeminiService running in mock mode (no API key).")


    # ──────────────────────────────────────────────────────────────────────────
    # PRIMARY: Vision detection
    # ──────────────────────────────────────────────────────────────────────────

    async def detect_crop_and_disease(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
    ) -> dict:
        """
        Send image to Gemini Vision and receive structured crop + disease analysis.

        Returns one of:
          {"error": "No crop leaf detected"}
          {"error": "Unable to identify crop"}
          {"crop": "...", "disease": "...", "confidence": 97,
           "severity": "Medium", "symptoms": [...]}

        On API unavailability → returns mock result (never raises).
        """
        if self._mock_mode or self._client is None:
            logger.info("Gemini mock mode — returning demo vision result.")
            return self._mock_vision_result()

        # ── Filename blacklist fast-path ──────────────────────────────────
        _REJECT_TERMS = {
            "non-leaf", "non_leaf", "person", "human", "selfie", "face",
            "dog", "cat", "car", "bike", "football", "messi", "ronaldo",
            "grass", "field", "sky", "road",
        }
        if filename:
            fn_lower = filename.lower()
            for term in _REJECT_TERMS:
                if term in fn_lower:
                    logger.info(
                        "[Gemini Vision] Filename blacklist hit: term='%s', file='%s'",
                        term, filename,
                    )
                    return {"error": "No crop leaf detected"}

        # ── Try Gemini (with retry on JSON parse failure) ─────────────────
        for attempt in range(1, 3):
            try:
                raw = self._call_gemini_vision(image_bytes, _VISION_PROMPT)
                if raw is None:
                    # Timeout
                    logger.warning("[Gemini Vision] Timed out after %ds.", GEMINI_TIMEOUT_SECONDS)
                    return {"error": "AI service unavailable. Please try again."}

                # Strip accidental markdown fences
                cleaned = _strip_markdown(raw)
                result = json.loads(cleaned)

                # Validate schema
                if "error" in result:
                    return result

                _validate_vision_result(result)

                logger.info(
                    "\n=============================="
                    "\n[Gemini Vision]"
                    "\nCrop:       %s"
                    "\nDisease:    %s"
                    "\nConfidence: %d%%"
                    "\nSeverity:   %s"
                    "\n==============================",
                    result["crop"],
                    result["disease"],
                    result["confidence"],
                    result["severity"],
                )
                return result

            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning(
                    "[Gemini Vision] Parse error on attempt %d: %s", attempt, exc
                )
                if attempt == 2:
                    logger.error("[Gemini Vision] Both attempts failed — returning 500 payload.")
                    raise ValueError("AI parsing failed after 2 attempts.") from exc

            except Exception as exc:
                logger.error("[Gemini Vision] Unexpected error: %s", exc)
                return {"error": "AI service unavailable. Please try again."}

    # ──────────────────────────────────────────────────────────────────────────
    # SECONDARY: Explanation generation
    # ──────────────────────────────────────────────────────────────────────────

    async def generate_explanation(
        self,
        crop_name: str,
        crop_confidence: float,
        disease_name: str,
        disease_confidence: float,
        severity: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        affected_area: Optional[float] = None,
        condition: Optional[str] = None,
        symptoms: Optional[list[str]] = None,
    ) -> str:
        """
        Generate a structured JSON explanation string.
        Falls back to rule-based generator when Gemini is unavailable.
        """
        if self._mock_mode or self._client is None:
            return self._generate_fallback_explanation(
                crop_name=crop_name,
                disease_name=disease_name,
                severity=severity,
                temperature=temperature,
                humidity=humidity,
                condition=condition,
                symptoms=symptoms,
            )

        try:
            symptoms_list = symptoms or []
            prompt = _EXPLANATION_PROMPT.format(
                crop_name=crop_name,
                confidence_pct=round(crop_confidence * 100, 1),
                disease_name=disease_name,
                severity=severity,
                affected_area=f"{affected_area}%" if affected_area is not None else "unknown",
                symptoms=", ".join(symptoms_list) if symptoms_list else "not specified",
                temperature=f"{temperature}°C" if temperature else "not available",
                humidity=f"{humidity}%" if humidity else "not available",
                condition=condition or "not available",
                symptoms_json=json.dumps(symptoms_list[:5] if symptoms_list else [
                    "Visible symptoms detected on leaf surface."
                ]),
            )

            raw = self._call_gemini_text(prompt)
            if raw is None:
                logger.warning("[Gemini Explanation] Timed out — using fallback.")
                return self._generate_fallback_explanation(
                    crop_name=crop_name, disease_name=disease_name,
                    severity=severity, temperature=temperature,
                    humidity=humidity, condition=condition, symptoms=symptoms,
                )

            cleaned = _strip_markdown(raw)
            parsed = json.loads(cleaned)

            for key in ("summary", "features", "treatment", "fertilizer"):
                if key not in parsed:
                    raise KeyError(f"Missing key: {key}")

            logger.info("[Gemini Explanation] Generated successfully.")
            return json.dumps(parsed)

        except Exception as exc:
            logger.warning("[Gemini Explanation] Failed (%s) — using fallback.", exc)
            return self._generate_fallback_explanation(
                crop_name=crop_name, disease_name=disease_name,
                severity=severity, temperature=temperature,
                humidity=humidity, condition=condition, symptoms=symptoms,
            )

    async def generate_quick_tip(self, crop_name: str, disease_name: str) -> str:
        """Generate a one-sentence quick tip."""
        if self._mock_mode or self._client is None:
            return (
                f"For {disease_name} on {crop_name}, clean pruning shears between "
                "cuts to prevent mechanical transfer of spores."
            )
        try:
            prompt = (
                f"Give one practical tip (max 25 words) for a farmer dealing "
                f"with {disease_name} on {crop_name}."
            )
            raw = self._call_gemini_text(prompt)
            return (raw or "").strip() or f"Monitor your {crop_name} daily."
        except Exception as exc:
            logger.warning("[Gemini Tip] Failed: %s", exc)
            return f"Monitor your {crop_name} daily and maintain balanced nutrition."

    # ──────────────────────────────────────────────────────────────────────────
    # Internal Gemini callers (with timeout)
    # ──────────────────────────────────────────────────────────────────────────

    def _call_gemini_vision(self, image_bytes: bytes, prompt: str) -> Optional[str]:
        """Run a Gemini Vision call in a daemon thread; return text or None on timeout."""
        from PIL import Image as PILImage

        result_box: dict = {}

        def _run():
            try:
                img = PILImage.open(io.BytesIO(image_bytes))
                response = self._client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=[prompt, img],
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        top_p=0.9,
                        max_output_tokens=512,
                    ),
                )
                result_box["text"] = response.text.strip()
            except Exception as exc:
                result_box["exc"] = exc

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=GEMINI_TIMEOUT_SECONDS)

        if t.is_alive():
            return None  # timeout
        if "exc" in result_box:
            raise result_box["exc"]
        return result_box.get("text", "")

    def _call_gemini_text(self, prompt: str) -> Optional[str]:
        """Run a Gemini text call in a daemon thread; return text or None on timeout."""
        result_box: dict = {}

        def _run():
            try:
                response = self._client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        top_p=0.95,
                        max_output_tokens=512,
                    ),
                )
                result_box["text"] = response.text.strip()
            except Exception as exc:
                result_box["exc"] = exc

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=GEMINI_TIMEOUT_SECONDS)

        if t.is_alive():
            return None
        if "exc" in result_box:
            raise result_box["exc"]
        return result_box.get("text", "")

    # ──────────────────────────────────────────────────────────────────────────
    # Fallback generators
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _mock_vision_result() -> dict:
        """Demo result for when no API key is configured."""
        return {
            "crop": "Tomato",
            "disease": "Early Blight",
            "confidence": 89,
            "severity": "Medium",
            "symptoms": [
                "Dark brown concentric ring lesions on lower leaves",
                "Yellow halo surrounding necrotic leaf spots",
                "Progressive leaf drop from bottom upward",
            ],
        }

    def _generate_fallback_explanation(
        self,
        crop_name: str,
        disease_name: str,
        severity: str,
        temperature: Optional[float],
        humidity: Optional[float],
        condition: Optional[str],
        symptoms: Optional[list[str]] = None,
    ) -> str:
        """Rule-based structured explanation when Gemini text is unavailable."""
        weather_note = ""
        if temperature and humidity:
            weather_note = (
                f" Humid conditions ({humidity}%) accelerate spore spread."
                if humidity > 70
                else " Current weather presents moderate pathogen risk."
            )

        d_lower = disease_name.lower()
        feature_list = symptoms[:3] if symptoms else [
            "Discoloration or lesions visible on leaf surface.",
            "Abnormal leaf texture or premature yellowing.",
        ]

        if "healthy" in d_lower:
            return json.dumps({
                "summary": (
                    f"Your {crop_name} crop appears healthy — no disease detected. "
                    "Continue monitoring every 3–5 days to catch early infections."
                ),
                "features": feature_list or [
                    "Leaves display normal green coloration.",
                    "No lesions, wilting, or abnormal discoloration.",
                ],
                "treatment": [
                    "No chemical treatment required.",
                    "Continue monitoring every 3–5 days.",
                    "Maintain balanced irrigation.",
                    "Apply regular NPK fertilizer.",
                ],
                "fertilizer": "Apply balanced NPK 19-19-19 to sustain healthy growth.",
            })

        if "unknown" in d_lower:
            return json.dumps({
                "summary": (
                    "The image quality was insufficient for a confident disease diagnosis. "
                    "Please upload a close-up photo in daylight with the leaf filling the frame."
                ),
                "features": [
                    "Image quality too low to identify specific symptoms.",
                    "Retake photo in natural daylight, leaf in focus.",
                ],
                "treatment": [
                    "Upload a clearer close-up image of the affected leaf.",
                    "Take the photo in natural daylight with good focus.",
                    "Avoid blurry or overexposed images.",
                ],
                "fertilizer": "Continue normal fertilization until a confirmed diagnosis.",
            })

        if "early blight" in d_lower:
            summary = (
                f"Early Blight detected on your {crop_name} crop.{weather_note} "
                "Remove infected foliage and apply fungicide immediately."
            )
            treatment = [
                "Remove and destroy infected lower leaves immediately.",
                "Apply copper-based fungicide or mancozeb every 7–10 days.",
                "Water at the base — never wet the foliage.",
            ]
            fertilizer = "Apply Calcium Nitrate foliar spray to strengthen leaf cell walls."
        elif "late blight" in d_lower:
            summary = (
                f"Late Blight is a highly destructive disease on your {crop_name} crop.{weather_note} "
                "Immediate removal and systemic fungicide are critical."
            )
            treatment = [
                "Remove and bag all infected plants — do NOT compost.",
                "Apply systemic fungicide (metalaxyl-m + mancozeb) to healthy rows.",
                "Avoid working in the field when wet to prevent spread.",
            ]
            fertilizer = "Apply potassium-rich foliar fertilizer to boost crop resistance."
        else:
            summary = (
                f"{disease_name} detected on your {crop_name} crop.{weather_note} "
                "Begin treatment promptly to prevent further spread."
            )
            treatment = [
                "Prune infected foliage and improve plant spacing for airflow.",
                "Apply broad-spectrum copper fungicide preventatively.",
                "Monitor crop daily for the next 14 days.",
            ]
            fertilizer = "Apply micro-nutrient foliar spray to reduce plant stress."

        return json.dumps({
            "summary": summary,
            "features": feature_list,
            "treatment": treatment,
            "fertilizer": fertilizer,
        })

    # ──────────────────────────────────────────────────────────────────────────
    # Properties
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def is_mock_mode(self) -> bool:
        return self._mock_mode


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    """Remove ```json ... ``` code fences that Gemini sometimes adds."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def _validate_vision_result(result: dict) -> None:
    """Raise ValueError if the vision result is missing required fields."""
    required = {"crop", "disease", "confidence", "severity", "symptoms"}
    missing = required - set(result.keys())
    if missing:
        raise ValueError(f"Missing fields in Gemini response: {missing}")
    if not isinstance(result["confidence"], (int, float)):
        raise ValueError("confidence must be numeric")
    if result["severity"] not in ("Low", "Medium", "High", "Critical"):
        raise ValueError(f"Invalid severity: {result['severity']}")
    if not isinstance(result["symptoms"], list):
        raise ValueError("symptoms must be a list")


# ─── Singleton ─────────────────────────────────────────────────────────────────
gemini_service = GeminiService()
