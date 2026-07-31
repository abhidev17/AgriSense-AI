"""
Gemini AI service for AgriSense AI.

REAL IMPLEMENTATION with graceful mock fallback.
When GEMINI_API_KEY is set in .env, uses Google Generative AI SDK.
When key is absent, falls back to a rich template response so the
full pipeline runs without an API key.
"""

from typing import Optional

from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()

# ─── Prompt Templates ─────────────────────────────────────────────────────────

EXPLANATION_PROMPT = """You are AgriSense AI, an expert agronomist with 20 years of field experience.
A farmer has uploaded a plant photo and you have identified the following:

- Crop: {crop_name} (detection confidence: {crop_confidence_pct}%)
- Disease: {disease_name} (detection confidence: {disease_confidence_pct}%)
- Severity: {severity}
- Affected leaf area: {affected_area}
- Current temperature: {temperature}
- Current humidity: {humidity}
- Current weather: {condition}

Write a clear, farmer-friendly explanation in exactly 4 paragraphs:

Paragraph 1 — What the disease is: Describe {disease_name} in simple language. What causes it,
how it spreads, and what it looks like on {crop_name}.

Paragraph 2 — Why now: Explain how the current weather conditions (temperature {temperature},
humidity {humidity}) are influencing the disease progression.

Paragraph 3 — Immediate actions: List the 2-3 most critical things the farmer must do in the
next 48 hours to stop further spread.

Paragraph 4 — Outlook: Give a realistic recovery timeline and one long-term prevention tip
for next season.

Keep the language simple (8th grade reading level), avoid jargon, and be specific and actionable.
Do NOT use bullet points — write in flowing paragraphs only.
"""


class GeminiService:
    """
    Service that generates natural-language diagnosis explanations using
    Google Gemini generative AI.

    Automatically uses mock fallback when GEMINI_API_KEY is not configured.
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
                        "temperature": 0.7,
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

    # ─── Public API ───────────────────────────────────────────────────────────

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
        Generate a farmer-friendly 4-paragraph explanation of the diagnosis.

        Uses Gemini API when key is configured, otherwise returns a rich
        template-based mock response.

        Args:
            crop_name:          Detected crop species.
            crop_confidence:    Crop detection confidence (0-1).
            disease_name:       Detected disease name.
            disease_confidence: Disease detection confidence (0-1).
            severity:           'low' | 'moderate' | 'high' | 'critical'.
            temperature:        Current temperature in Celsius (optional).
            humidity:           Current humidity percentage (optional).
            affected_area:      Estimated % of leaf area affected (optional).
            condition:          Weather condition string (optional).

        Returns:
            Natural-language explanation string.
        """
        if self._mock_mode or self._model is None:
            return self._generate_mock_explanation(
                crop_name=crop_name,
                disease_name=disease_name,
                disease_confidence=disease_confidence,
                severity=severity,
                temperature=temperature,
                humidity=humidity,
                affected_area=affected_area,
            )

        # ── Real Gemini call ──────────────────────────────────────────────────
        try:
            prompt = EXPLANATION_PROMPT.format(
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

            response = await self._model.generate_content_async(prompt)
            text = response.text.strip()

            logger.info(
                "Gemini explanation generated — crop=%s, disease=%s (%d chars)",
                crop_name,
                disease_name,
                len(text),
            )
            return text

        except Exception as exc:
            logger.warning(
                "Gemini API call failed (%s). Falling back to mock explanation.", exc
            )
            return self._generate_mock_explanation(
                crop_name=crop_name,
                disease_name=disease_name,
                disease_confidence=disease_confidence,
                severity=severity,
                temperature=temperature,
                humidity=humidity,
                affected_area=affected_area,
            )

    async def generate_quick_tip(self, crop_name: str, disease_name: str) -> str:
        """
        Generate a single-sentence quick tip for dashboard widgets.
        """
        if self._mock_mode or self._model is None:
            return (
                f"Tip: For {disease_name} on {crop_name}, early morning fungicide "
                "applications are most effective — avoid spraying in full sun or rain."
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
            return f"Monitor your {crop_name} daily and consult a local agronomist."

    # ─── Mock fallback ────────────────────────────────────────────────────────

    def _generate_mock_explanation(
        self,
        crop_name: str,
        disease_name: str,
        disease_confidence: float,
        severity: str,
        temperature: Optional[float],
        humidity: Optional[float],
        affected_area: Optional[float],
    ) -> str:
        """Generate a rich template-based explanation when Gemini is unavailable."""
        temp_str = f"{temperature}°C" if temperature is not None else "unknown"
        humid_str = f"{humidity}%" if humidity is not None else "unknown"
        area_str = f"{affected_area}% of the leaf area" if affected_area else "a portion of the crop"
        conf_pct = round(disease_confidence * 100, 1)

        severity_context = {
            "low": "caught early and can be managed with minimal intervention",
            "moderate": "at a stage where prompt action will prevent further spread",
            "high": "serious and requires immediate treatment to save the crop",
            "critical": "at a critical stage — aggressive treatment is urgently needed",
        }.get(severity, "present and requires attention")

        weather_context = ""
        if temperature is not None and humidity is not None:
            if humidity > 70:
                weather_context = (
                    f"The current weather conditions — temperature {temp_str} and high humidity "
                    f"{humid_str} — are creating an ideal environment for this disease to spread. "
                    f"Warm, humid conditions accelerate spore germination and increase the rate "
                    f"of infection, making the next 48 hours critical for intervention."
                )
            else:
                weather_context = (
                    f"The current weather — temperature {temp_str} and humidity {humid_str} — "
                    f"presents a moderately favorable environment for this disease. While conditions "
                    f"are not at peak risk levels, the pathogen is still active and will spread "
                    f"without treatment."
                )
        else:
            weather_context = (
                "Without location data, specific weather-based risk cannot be calculated. "
                "Fungal diseases like this one generally thrive in warm, humid conditions above 60% "
                "relative humidity. Monitor local weather closely over the next 7 days."
            )

        return (
            f"{disease_name} has been detected on your {crop_name} crop with "
            f"{conf_pct}% confidence. This disease is currently {severity_context}, "
            f"affecting {area_str}. It is typically caused by fungal or bacterial "
            f"pathogens that overwinter in infected plant debris and spread through "
            f"water splash, wind, or contact during cultivation.\n\n"
            f"{weather_context}\n\n"
            f"Your most critical immediate actions are: First, remove and safely destroy "
            f"all visibly infected leaves — do NOT compost them as this spreads the pathogen. "
            f"Second, apply a copper-based or mancozeb fungicide within the next 24-48 hours, "
            f"following the label rate. Third, switch to drip irrigation if possible and avoid "
            f"wetting the foliage, as moisture on leaves dramatically accelerates the disease cycle.\n\n"
            f"With timely and consistent treatment, most {crop_name} plants can recover "
            f"within 10-14 days and yield losses can be kept below 15%. For next season, "
            f"plant disease-resistant varieties, implement a 3-year crop rotation with "
            f"non-host plants, and begin preventive fungicide sprays at first leaf emergence."
        )

    @property
    def is_mock_mode(self) -> bool:
        """Return True when running without a real Gemini API key."""
        return self._mock_mode


# ─── Singleton ────────────────────────────────────────────────────────────────
gemini_service = GeminiService()
