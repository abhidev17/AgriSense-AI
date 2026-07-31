"""
Gemini AI service for AgriSense AI.

PLACEHOLDER IMPLEMENTATION
──────────────────────────
This module will integrate Google Gemini (via the google-generativeai SDK)
to generate natural-language diagnosis explanations and advice.

Current behaviour: returns a well-structured mock explanation so the API
pipeline can run end-to-end without a live Gemini key.
"""

from typing import Optional

from app.utils.logger import logger
from app.utils.config import get_settings

settings = get_settings()


# ─── Prompt template ─────────────────────────────────────────────────────────
# TODO: Tune this prompt with a few-shot agriculture expert persona.
EXPLANATION_PROMPT_TEMPLATE = """
You are AgriSense AI, an expert agronomist. Given the following crop diagnosis,
provide a clear, farmer-friendly explanation in 3–4 concise paragraphs:

Crop:     {crop_name} (confidence: {crop_confidence})
Disease:  {disease_name} (confidence: {disease_confidence})
Severity: {severity}
Weather:  Temperature {temperature}°C, Humidity {humidity}%

Explain:
1. What the disease is and how it affects the crop.
2. Why current weather conditions are relevant.
3. The most critical immediate actions the farmer should take.
4. A brief outlook (recovery timeline, long-term prevention).

Keep the language simple and actionable.
"""


class GeminiService:
    """
    Service that generates natural-language diagnosis explanations using
    Google Gemini generative AI.

    Integration points (TODO when API key is available):
      - Install: pip install google-generativeai
      - Set GEMINI_API_KEY in .env
      - Replace the mock body of ``generate_explanation`` with a real
        genai.GenerativeModel call.
    """

    def __init__(self) -> None:
        # TODO: Initialise Gemini client when API key is set
        # if settings.GEMINI_API_KEY:
        #     import google.generativeai as genai
        #     genai.configure(api_key=settings.GEMINI_API_KEY)
        #     self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
        # else:
        #     self._model = None
        self._model = None
        logger.info(
            "GeminiService initialised — model=%s (mock mode).",
            settings.GEMINI_MODEL,
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
    ) -> str:
        """
        Generate a farmer-friendly explanation of the diagnosis.

        Args:
            crop_name:         Detected crop species.
            crop_confidence:   Crop detection confidence (0–1).
            disease_name:      Detected disease name.
            disease_confidence: Disease detection confidence (0–1).
            severity:          'low' | 'moderate' | 'high' | 'critical'.
            temperature:       Current temperature in °C (optional).
            humidity:          Current humidity % (optional).

        Returns:
            Natural-language explanation string.

        TODO:
            Replace mock block with Gemini API call:

            .. code-block:: python

                prompt = EXPLANATION_PROMPT_TEMPLATE.format(...)
                response = await self._model.generate_content_async(prompt)
                return response.text
        """
        logger.debug(
            "generate_explanation() called — crop=%s, disease=%s (mock mode)",
            crop_name,
            disease_name,
        )

        # ── MOCK RESPONSE ─────────────────────────────────────────────────────
        temp_str = f"{temperature}°C" if temperature is not None else "N/A"
        humid_str = f"{humidity}%" if humidity is not None else "N/A"

        explanation = (
            f"**{disease_name}** has been detected on your **{crop_name}** crop "
            f"with {round(disease_confidence * 100, 1)}% confidence. "
            f"This fungal disease is caused by *Alternaria solani* and typically "
            f"appears as dark, concentric-ringed lesions on older leaves first before "
            f"spreading upward through the canopy.\n\n"
            f"Current weather conditions — temperature {temp_str}, humidity {humid_str} — "
            f"create a moderately favourable environment for disease progression. "
            f"Warm, humid conditions accelerate spore germination and spread, so prompt "
            f"action is essential to prevent further crop loss.\n\n"
            f"**Immediate actions recommended:** Remove and safely dispose of all "
            f"visibly infected leaves. Apply a copper-based or mancozeb fungicide "
            f"within the next 24–48 hours, following label rates. Reduce overhead "
            f"irrigation and improve row spacing to promote airflow.\n\n"
            f"With timely treatment the infection can be contained within 10–14 days. "
            f"For next season, consider disease-resistant varieties and implement a "
            f"3-year crop rotation to break the pathogen cycle."
        )

        logger.info("Explanation generated (mock) for %s / %s.", crop_name, disease_name)
        return explanation

    async def generate_quick_tip(self, crop_name: str, disease_name: str) -> str:
        """
        Generate a single-sentence quick tip for the farmer dashboard widget.

        TODO: Replace with Gemini API call.
        """
        return (
            f"Tip: For {disease_name} on {crop_name}, early morning fungicide "
            "applications are most effective — avoid spraying in full sun or rain."
        )


# ─── Singleton ────────────────────────────────────────────────────────────────
gemini_service = GeminiService()
