"""
Action Plan service for AgriSense AI.

Generates a structured, risk-scored action plan from combined diagnosis results.
Optionally uses Gemini for richer text; falls back to deterministic rule engine.
"""

import json
import datetime
from typing import Optional

from app.utils.logger import logger

# ─── Risk scoring weights (for deterministic fallback) ─────────────────────────

SEVERITY_SCORES: dict[str, int] = {
    "low":      15,
    "moderate": 40,
    "high":     65,
    "critical": 90,
}

DISEASE_RISK_MODIFIERS: dict[str, int] = {
    "Late Blight":             +20,
    "Early Blight":             +5,
    "Bacterial Spot":           +8,
    "Bacterial Leaf Spot":      +8,
    "Yellow Leaf Curl Virus":  +15,
    "Powdery Mildew":           -5,
    "Healthy":                 -80,
    "Downy Mildew":             +5,
    "Cercospora Leaf Spot":      0,
    "Common Rust":               +5,
    "Northern Leaf Blight":    +10,
    "Apple Scab":                +8,
    "Black Rot":                +12,
    "Leaf Mold":                 +3,
    "Target Spot":               +3,
    "Spider Mites":              +5,
}

HIGH_VALUE_CROPS = {"Apple", "Grape", "Strawberry", "Cherry", "Blueberry", "Peach"}

RISK_LABELS: dict[str, str] = {
    "critical": "Critical",
    "high":     "High",
    "moderate": "Medium",
    "low":      "Low",
}

RECOVERY_ESTIMATES: dict[str, str] = {
    "critical": "30-50%",
    "high":     "60-75%",
    "moderate": "85-95%",
    "low":      "95-100%",
}

FUNGICIDE_MAP: dict[str, str] = {
    "Early Blight":        "Copper Fungicide (Blitox) or Mancozeb",
    "Late Blight":         "Metalaxyl-M + Mancozeb (Ridomil Gold)",
    "Powdery Mildew":      "Sulphur-based fungicide (Sulfex)",
    "Downy Mildew":        "Fosetyl-Al (Aliette) or Copper Hydroxide",
    "Leaf Mold":           "Chlorothalonil or Mancozeb",
    "Bacterial Spot":      "Copper Bactericide + Streptomycin",
    "Bacterial Leaf Spot": "Copper Bactericide + Streptomycin",
    "Target Spot":         "Azoxystrobin or Difenoconazole",
    "Common Rust":         "Propiconazole or Tebuconazole",
    "Northern Leaf Blight":"Propiconazole (Tilt) or Azoxystrobin",
    "Apple Scab":          "Captan or Mancozeb at bud break",
    "Black Rot":           "Captan or Ziram-based fungicide",
    "Cercospora Leaf Spot":"Carbendazim or Chlorothalonil",
}

DEFAULT_FUNGICIDE = "Copper-based fungicide (Bordeaux mixture)"


class ActionPlanResult:
    """
    Holds the full action plan result.
    """

    def __init__(self) -> None:
        self.overall_risk = "Medium"
        self.risk_score = 50
        self.estimated_recovery = "85-95%"
        self.timeline = []
        self.immediate_actions = []
        self.prevention_tips = []

    def __init__(
        self,
        overall_risk: str,
        risk_score: int,
        estimated_recovery: str,
        timeline: list[dict],
        immediate_actions: list[str],
        prevention_tips: list[str],
    ) -> None:
        self.overall_risk = overall_risk
        self.risk_score = risk_score
        self.estimated_recovery = estimated_recovery
        self.timeline = timeline
        self.immediate_actions = immediate_actions
        self.prevention_tips = prevention_tips

    def to_dict(self) -> dict:
        return {
            "overall_risk": self.overall_risk,
            "risk_score": self.risk_score,
            "estimated_recovery": self.estimated_recovery,
            "timeline": self.timeline,
            "immediate_actions": self.immediate_actions,
            "prevention_tips": self.prevention_tips,
        }


class ActionPlanService:
    """
    Generates a structured recovery action plan.
    Uses Gemini when available, otherwise falls back to a deterministic rule engine.
    """

    def generate(
        self,
        crop_name: str,
        disease_name: str,
        severity: str,
        confidence: float,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        rainfall_mm: Optional[float] = None,
        current_price: Optional[float] = None,
        price_trend: Optional[str] = None,
        treatment_steps: Optional[list[str]] = None,
    ) -> ActionPlanResult:
        """
        Generate a recovery action plan.
        """
        # Try to use Gemini
        from app.services.gemini import gemini_service
        if not gemini_service.is_mock_mode and gemini_service._model is not None:
            try:
                current_date = datetime.date.today().isoformat()
                prompt = f"""You are an expert recovery planner for AgriSense AI.
Generate a recovery action plan for:
- Crop: {crop_name}
- Disease: {disease_name}
- Severity: {severity}
- Confidence: {confidence:.2f}
- Temperature: {temperature if temperature is not None else 'unknown'}°C
- Humidity: {humidity if humidity is not None else 'unknown'}%
- Rain: {rainfall_mm if rainfall_mm is not None else 'unknown'}mm
- Market price: {current_price if current_price is not None else 'unknown'} per kg
- Market Trend: {price_trend if price_trend is not None else 'stable'}
- Treatment: {treatment_steps if treatment_steps else 'unknown'}
- Current Date: {current_date}

You MUST respond with EXACTLY a JSON object matching this schema:
{{
    "overall_risk": "Low | Medium | High | Critical",
    "risk_score": <int between 0 and 100>,
    "estimated_recovery": "E.g., 90-95%",
    "timeline": [
        {{"day": "Today", "action": "...", "reason": "..."}},
        {{"day": "Tomorrow", "action": "...", "reason": "..."}},
        {{"day": "After 3 Days", "action": "...", "reason": "..."}},
        {{"day": "Next Week", "action": "...", "reason": "..."}},
        {{"day": "Harvest", "action": "...", "reason": "..."}}
    ],
    "immediate_actions": [
        "List of 2-3 immediate action items within 24h"
    ],
    "prevention_tips": [
        "List of 2-3 long-term prevention tips"
    ]
}}
Do not include any formatting or text outside the JSON. Return only valid raw JSON."""

                response = gemini_service._model.generate_content(prompt)
                text = response.text.strip()
                if text.startswith("```"):
                    lines = text.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                    text = "\n".join(lines).strip()

                plan_data = json.loads(text)
                
                logger.info("Structured action plan generated successfully using Gemini.")
                return ActionPlanResult(
                    overall_risk=plan_data["overall_risk"],
                    risk_score=int(plan_data["risk_score"]),
                    estimated_recovery=plan_data["estimated_recovery"],
                    timeline=plan_data["timeline"],
                    immediate_actions=plan_data["immediate_actions"],
                    prevention_tips=plan_data["prevention_tips"]
                )
            except Exception as exc:
                logger.warning("Gemini action plan generation failed (%s). Falling back to rule-based.", exc)

        # Fallback to rule engine
        return self._generate_rule_based(
            crop_name=crop_name,
            disease_name=disease_name,
            severity=severity,
            confidence=confidence,
            temperature=temperature,
            humidity=humidity,
            rainfall_mm=rainfall_mm,
            current_price=current_price,
            price_trend=price_trend,
        )

    def generate_action_plan(
        self,
        crop: str,
        disease: str,
        severity: str,
        weather: Optional[dict] = None,
        humidity: Optional[float] = None,
        rain: Optional[float] = None,
        temperature: Optional[float] = None,
        treatment: Optional[list[str]] = None,
        market_trend: Optional[str] = None,
        current_date: Optional[str] = None,
    ) -> dict:
        """
        Complies with the generate_action_plan() method requested in requirements.
        Returns a raw dictionary representing the action plan JSON.
        """
        # Map parameters to generate() signature
        weather_cond = weather.get("condition") if weather else None
        curr_price = weather.get("price") if weather else None  # generic fallback
        
        result = self.generate(
            crop_name=crop,
            disease_name=disease,
            severity=severity,
            confidence=0.95,  # default
            temperature=temperature,
            humidity=humidity,
            rainfall_mm=rain,
            current_price=curr_price,
            price_trend=market_trend,
            treatment_steps=treatment,
        )
        return result.to_dict()

    def _generate_rule_based(
        self,
        crop_name: str,
        disease_name: str,
        severity: str,
        confidence: float,
        temperature: Optional[float],
        humidity: Optional[float],
        rainfall_mm: Optional[float],
        current_price: Optional[float],
        price_trend: Optional[str],
    ) -> ActionPlanResult:
        """
        Deterministic rule-based recovery planner fallback.
        """
        risk_score = self._calculate_risk_score(
            disease_name=disease_name,
            severity=severity,
            confidence=confidence,
            temperature=temperature,
            humidity=humidity,
            crop_name=crop_name,
        )

        risk_level = self._score_to_level(risk_score)
        overall_risk = RISK_LABELS.get(risk_level, "Medium")
        estimated_recovery = RECOVERY_ESTIMATES.get(risk_level, "85-95%")

        # Build timeline
        timeline = self._build_timeline(
            crop_name=crop_name,
            disease_name=disease_name,
            severity=severity,
            risk_level=risk_level,
            humidity=humidity,
            rainfall_mm=rainfall_mm,
            current_price=current_price,
            price_trend=price_trend,
        )

        # Build immediate actions and prevention tips
        immediate_actions = self._build_immediate_actions(
            disease_name=disease_name,
            severity=severity,
            risk_level=risk_level,
        )

        prevention_tips = self._build_prevention_tips(
            crop_name=crop_name,
            disease_name=disease_name,
            price_trend=price_trend,
        )

        return ActionPlanResult(
            overall_risk=overall_risk,
            risk_score=risk_score,
            estimated_recovery=estimated_recovery,
            timeline=timeline,
            immediate_actions=immediate_actions,
            prevention_tips=prevention_tips,
        )

    def _calculate_risk_score(
        self,
        disease_name: str,
        severity: str,
        confidence: float,
        temperature: Optional[float],
        humidity: Optional[float],
        crop_name: str,
    ) -> int:
        base = SEVERITY_SCORES.get(severity.lower(), 40)
        score = int(base * 0.44)
        score += int(confidence * 10)

        if humidity is not None:
            if humidity > 80:
                score += 15
            elif humidity > 70:
                score += 10
            elif humidity > 60:
                score += 5

        if temperature is not None:
            if 20 <= temperature <= 32:
                score += 10
            elif 15 <= temperature < 20 or 32 < temperature <= 38:
                score += 5

        score += DISEASE_RISK_MODIFIERS.get(disease_name, 0)

        if crop_name in HIGH_VALUE_CROPS:
            score += 5

        return max(0, min(100, score))

    def _score_to_level(self, score: int) -> str:
        if score >= 75:
            return "critical"
        elif score >= 55:
            return "high"
        elif score >= 30:
            return "moderate"
        else:
            return "low"

    def _build_timeline(
        self,
        crop_name: str,
        disease_name: str,
        severity: str,
        risk_level: str,
        humidity: Optional[float],
        rainfall_mm: Optional[float],
        current_price: Optional[float],
        price_trend: Optional[str],
    ) -> list[dict]:
        fungicide = FUNGICIDE_MAP.get(disease_name, DEFAULT_FUNGICIDE)

        # Today
        if disease_name == "Healthy":
            today_act, today_reason = "Inspect and document plant health", "Your crop appears healthy. Record baseline for comparison."
        elif risk_level == "critical":
            today_act, today_reason = "Remove and destroy all infected plant parts immediately", "Critical infection. Delayed action increases spread exponentially."
        else:
            today_act, today_reason = "Remove infected leaves and improve field drainage", "Removing infected tissue reduces spore load and slows spread."

        # Tomorrow
        rain_expected = rainfall_mm is not None and rainfall_mm > 2.0
        high_humidity = humidity is not None and humidity > 70
        if disease_name == "Healthy":
            tomorrow_act, tomorrow_reason = "Ensure drip irrigation is functioning correctly", "Consistent base watering supports plant immune function."
        elif rain_expected:
            tomorrow_act, tomorrow_reason = f"Apply {fungicide} before rain", "Provides preventative systemic protection before leaf surface wetting."
        elif high_humidity:
            tomorrow_act, tomorrow_reason = f"Spray {fungicide} early morning", "High humidity accelerates fungal spread. Early morning spray avoids leaf burn."
        else:
            tomorrow_act, tomorrow_reason = f"Spray {fungicide} on affected zones", "Halts disease progression in localized zones."

        # After 3 Days
        if disease_name == "Healthy":
            day3_act, day3_reason = "Apply balanced NPK fertilizer (19-19-19)", "Supports strong immune response and healthy vegetative growth."
        elif severity in ("high", "critical"):
            day3_act, day3_reason = "Apply NPK 19-19-19 or Calcium Nitrate foliar spray", "Nutrient stress depletes plant vigor. Foliar feeding bypasses root system for fast recovery."
        else:
            day3_act, day3_reason = "Apply NPK 19-19-19 for recovery support", "Replenishes minerals lost due to disease damage."

        # Next Week
        if disease_name == "Healthy":
            week_act, week_reason = "Continue regular monitoring and care schedule", "Consistently healthy plants yield premium grades."
        elif risk_level in ("critical", "high"):
            week_act, week_reason = "Re-inspect crop and apply second spray cycle if needed", "High-risk pathogens often require multiple application cycles."
        else:
            week_act, week_reason = "Inspect new leaves for disease resurgence", "New growth is vulnerable to leftover spores in the soil."

        # Harvest
        price_str = f"Rs {current_price:.0f}/kg" if current_price else ""
        if disease_name == "Healthy":
            harvest_act, harvest_reason = f"Harvest {crop_name} at optimal maturity", "Optimal quality drives top market pricing."
        elif price_trend == "up" and price_str:
            harvest_act, harvest_reason = f"Sell stock at peak price {price_str}", "Market is trending up. Short holding can optimize profit margins."
        elif price_trend == "down" and price_str:
            harvest_act, harvest_reason = f"Harvest early and sell immediately at {price_str}", "Prices are declining. Early exit prevents deeper economic losses."
        else:
            harvest_act, harvest_reason = f"Assess quality and harvest clean rows first", "Segregating clean crop from infected rows yields higher premium pricing."

        return [
            {"day": "Today",        "action": today_act,    "reason": today_reason},
            {"day": "Tomorrow",     "action": tomorrow_act, "reason": tomorrow_reason},
            {"day": "After 3 Days", "action": day3_act,     "reason": day3_reason},
            {"day": "Next Week",    "action": week_act,     "reason": week_reason},
            {"day": "Harvest",      "action": harvest_act,  "reason": harvest_reason},
        ]

    def _build_immediate_actions(
        self,
        disease_name: str,
        severity: str,
        risk_level: str,
    ) -> list[str]:
        if disease_name == "Healthy":
            return [
                "Photograph all healthy sections to maintain a reference log.",
                "Ensure drip irrigation pipes are clear and free of blockages."
            ]

        actions = [
            "Photograph infected leaves to track disease progression.",
            "Remove and bag infected plant material — do NOT compost."
        ]

        if risk_level in ("critical", "high"):
            actions.append("Apply crop-appropriate fungicide/bactericide TODAY.")
            actions.append("Isolate the infected rows to limit spore movement.")

        if disease_name == "Late Blight":
            actions.append(
                "URGENT: Late Blight can destroy an entire crop in 3-5 days under humid conditions. "
                "Contact your local agriculture office immediately."
            )
        elif disease_name == "Yellow Leaf Curl Virus":
            actions.append(
                "Control whitefly vectors immediately — apply imidacloprid and install "
                "yellow sticky traps."
            )

        return actions

    def _build_prevention_tips(
        self,
        crop_name: str,
        disease_name: str,
        price_trend: Optional[str],
    ) -> list[str]:
        if disease_name == "Healthy":
            return [
                f"Plant disease-resistant {crop_name} varieties next season.",
                "Implement a 3-year crop rotation schedule with non-host crops."
            ]

        tips = [
            f"Select certified disease-resistant {crop_name} seeds next season.",
            "Implement a 3-year crop rotation schedule to break the disease cycle.",
            "Switch to drip irrigation to prevent leaves from remaining wet.",
        ]

        if price_trend == "up":
            tips.append("With prices trending up, invest in preventative spraying to secure yield.")
        elif price_trend == "down":
            tips.append("With prices trending down, focus on lower-cost cultural control practices.")

        return tips


# ─── Singleton ────────────────────────────────────────────────────────────────
action_plan_service = ActionPlanService()
