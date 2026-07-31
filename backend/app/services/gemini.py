"""
Gemini AI service for AgriSense AI.

REAL IMPLEMENTATION with graceful mock fallback.
When GEMINI_API_KEY is set in .env, uses Google Generative AI SDK.
When key is absent or any call fails, falls back to a structured rule-based response.
"""

import json
from typing import Optional

from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()

GEMINI_PROMPT_TEMPLATE = """You are AgriSense AI, an expert agronomist. 
A farmer has uploaded a plant photo and you have identified the following:
- Crop: {crop_name} (confidence: {crop_confidence_pct}%)
- Disease: {disease_name} (confidence: {disease_confidence_pct}%)
- Severity: {severity}
- Affected leaf area: {affected_area}
- Current temperature: {temperature}
- Current humidity: {humidity}
- Weather: {condition}

Based on this information, generate an agronomical analysis.
You MUST respond with EXACTLY a JSON object matching this schema:
{{
    "summary": "A farmer-friendly 2-sentence summary of what the disease is, how it spreads, and how the current weather conditions affect it.",
    "features": [
        "List of 2-3 visual features/symptoms shown by the plant (specifically for {disease_name} on {crop_name})"
    ],
    "treatment": [
        "List of 2-3 critical treatment actions (fungicide/bactericide applications, physical removal, cultural practices)"
    ],
    "fertilizer": "NPK or fertilizer recommendation to support plant recovery and boost immunity under these conditions"
}}

Your response must contain ONLY the raw JSON object. Do not include markdown code block formatting (e.g. do not wrap in ```json). Do not add any text before or after the JSON.
"""


class GeminiService:
    """
    Service that generates structured, farmer-friendly explanations using Google Gemini AI.
    Gracefully falls back to rule-based JSON output when key is absent or API fails.
    """

    def __init__(self) -> None:
        self._model = None
        self._mock_mode = True

        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai

                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 1024,
                    },
                )
                self._mock_mode = False
                logger.info(
                    "GeminiService initialised with real API — model=%s",
                    settings.GEMINI_MODEL,
                )
            except ImportError:
                logger.warning(
                    "google-generativeai not installed. "
                    "Run: pip install google-generativeai. Falling back to mock."
                )
            except Exception as exc:
                logger.warning(
                    "Gemini SDK init failed (%s). Falling back to mock.", exc
                )
        else:
            logger.info(
                "GeminiService initialised in mock mode (GEMINI_API_KEY not set)."
            )

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
    ) -> str:
        """
        Generate a structured JSON explanation.
        If Gemini is unavailable or fails, returns a rule-based fallback JSON string.
        """
        if self._mock_mode or self._model is None:
            return self._generate_fallback_explanation(
                crop_name=crop_name,
                disease_name=disease_name,
                severity=severity,
                temperature=temperature,
                humidity=humidity,
                condition=condition,
            )

        try:
            prompt = GEMINI_PROMPT_TEMPLATE.format(
                crop_name=crop_name,
                crop_confidence_pct=round(crop_confidence * 100, 1),
                disease_name=disease_name,
                disease_confidence_pct=round(disease_confidence * 100, 1),
                severity=severity,
                affected_area=f"{affected_area}%" if affected_area else "unknown",
                temperature=f"{temperature}°C" if temperature else "not available",
                humidity=f"{humidity}%" if humidity else "not available",
                condition=condition or "not available",
            )

            # Call Gemini
            response = await self._model.generate_content_async(prompt)
            text_response = response.text.strip()
            
            # Clean up JSON if wrapped in markdown formatting by accident
            if text_response.startswith("```"):
                lines = text_response.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                text_response = "\n".join(lines).strip()

            # Verify it is valid JSON
            parsed = json.loads(text_response)
            
            # Ensure it contains all expected keys
            required_keys = ["summary", "features", "treatment", "fertilizer"]
            for key in required_keys:
                if key not in parsed:
                    raise KeyError(f"Missing key in Gemini response: {key}")

            logger.info("Gemini explanation generated successfully.")
            return json.dumps(parsed)

        except Exception as exc:
            logger.warning(
                "Gemini API call or parsing failed (%s). Falling back to mock.", exc
            )
            return self._generate_fallback_explanation(
                crop_name=crop_name,
                disease_name=disease_name,
                severity=severity,
                temperature=temperature,
                humidity=humidity,
                condition=condition,
            )

    async def generate_quick_tip(self, crop_name: str, disease_name: str) -> str:
        """Generate a single-sentence quick tip."""
        if self._mock_mode or self._model is None:
            return (
                f"For {disease_name} on {crop_name}, clean pruning shears between cuts "
                "to prevent mechanical transfer of spores."
            )

        try:
            prompt = (
                f"Give a single practical tip (one sentence, max 25 words) "
                f"for a farmer dealing with {disease_name} on {crop_name}."
            )
            response = await self._model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.warning("Gemini quick tip failed: %s", exc)
            return f"Monitor your {crop_name} daily and maintain balanced crop nutrition."

    def _generate_fallback_explanation(
        self,
        crop_name: str,
        disease_name: str,
        severity: str,
        temperature: Optional[float],
        humidity: Optional[float],
        condition: Optional[str],
    ) -> str:
        """Generate structured fallback explanation when Gemini is unavailable."""
        weather_details = ""
        if temperature and humidity:
            weather_details = f" Weather conditions (temp {temperature}°C, humidity {humidity}%) "
            if humidity > 70:
                weather_details += "are warm and humid, accelerating fungal spore spread."
            else:
                weather_details += "present moderate risks for pathogen multiplication."
        else:
            weather_details = "Fungal pathogens thrive in warm, damp conditions above 60% relative humidity."

        # Default rules based on disease
        d_lower = disease_name.lower()
        if "healthy" in d_lower:
            summary = f"Your {crop_name} crop appears healthy. Continued monitoring and regular irrigation will help maintain yield potential."
            features = [
                "Leaves display normal green coloration.",
                "Foliage lacks lesions, necrotic spots, or wilting symptoms."
            ]
            treatment = [
                "Continue standard agricultural practices and balanced irrigation.",
                "Perform regular crop inspections every 3-5 days to catch early infections."
            ]
            fertilizer = "Apply regular balanced NPK fertilizer (19-19-19) to sustain growth."
        elif "early blight" in d_lower:
            summary = f"Early Blight has been identified on your {crop_name} crop. {weather_details}"
            features = [
                "Small, dark brown spots on older leaves developing concentric rings (target spots).",
                "Yellowing surrounding leaf spots leading to leaf drop."
            ]
            treatment = [
                "Remove and destroy heavily infected lower foliage to reduce inoculum.",
                "Apply protective copper-based fungicide or mancozeb every 7-10 days."
            ]
            fertilizer = "Apply Calcium Nitrate foliar spray to strengthen leaf cell walls and support recovery."
        elif "late blight" in d_lower:
            summary = f"Late Blight has been identified on your {crop_name} crop. This is a highly destructive disease. {weather_details}"
            features = [
                "Large, dark water-soaked lesions on leaves that expand rapidly.",
                "White fungal growth visible on the undersides of leaves in humid weather."
            ]
            treatment = [
                "Immediately harvest/destroy infected plants; do not compost.",
                "Apply systemic fungicides (e.g., metalaxyl-m + mancozeb) to protect healthy rows."
            ]
            fertilizer = "Apply potassium-rich foliar fertilizers to boost general crop resistance."
        else:
            summary = f"{disease_name} has been detected on your {crop_name} crop. {weather_details}"
            features = [
                "Discoloration, lesions, or spotting on the leaf surfaces.",
                "Abnormal leaf texture or premature leaf senescence."
            ]
            treatment = [
                "Prune infected foliage and improve spacing to maximize airflow.",
                "Apply a broad-spectrum copper fungicide preventatively."
            ]
            fertilizer = "Foliar application of micro-nutrients to reduce stress and help recovery."

        return json.dumps({
            "summary": summary,
            "features": features,
            "treatment": treatment,
            "fertilizer": fertilizer
        })

    @property
    def is_mock_mode(self) -> bool:
        """Return True when running without a real Gemini API key."""
        return self._mock_mode


# ─── Singleton ────────────────────────────────────────────────────────────────
gemini_service = GeminiService()
