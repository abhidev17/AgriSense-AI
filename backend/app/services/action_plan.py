"""
Action Plan service for AgriSense AI.

Generates a structured, risk-scored action plan from combined diagnosis results.
Optionally uses Gemini for richer text; falls back to deterministic rule engine.

Output format (matches user spec exactly):
{
    "overall_risk": "Medium",
    "risk_score": 62,
    "estimated_recovery": "90-95%",
    "timeline": [
        {"day": "Today",        "action": "...", "reason": "..."},
        {"day": "Tomorrow",     "action": "...", "reason": "..."},
        {"day": "After 3 Days", "action": "...", "reason": "..."},
        {"day": "Next Week",    "action": "...", "reason": "..."},
        {"day": "Harvest",      "action": "...", "reason": "..."}
    ]
}
"""

from typing import Optional

from app.utils.logger import logger

# ─── Risk scoring weights ─────────────────────────────────────────────────────

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

# ─── Fungicide recommendations per disease ────────────────────────────────────

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

    Attributes:
        overall_risk:       'Low' | 'Medium' | 'High' | 'Critical'
        risk_score:         0-100 numeric risk score
        estimated_recovery: E.g. '85-95%'
        timeline:           List of {day, action, reason} dicts
        immediate_actions:  Critical actions required within 24h
        prevention_tips:    Long-term prevention recommendations
    """

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
    Generates a structured, risk-scored action plan from diagnosis results.

    The risk score (0-100) is computed using:
      1. Disease severity base score
      2. Disease detection confidence
      3. Weather humidity (high = higher risk)
      4. Temperature (warm = higher fungal risk)
      5. Disease-specific modifier
      6. Crop economic value modifier
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
        Generate a comprehensive action plan.

        Args:
            crop_name:        Detected crop species name.
            disease_name:     Detected disease name.
            severity:         'low' | 'moderate' | 'high' | 'critical'.
            confidence:       Disease detection confidence (0-1).
            temperature:      Current air temperature in Celsius.
            humidity:         Current relative humidity (%).
            rainfall_mm:      Expected/recent rainfall in mm.
            current_price:    Current crop market price.
            price_trend:      'up' | 'down' | 'stable'.
            treatment_steps:  Treatment recommendations from disease AI.

        Returns:
            ActionPlanResult with risk score, timeline, and recommendations.
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
        estimated_recovery = RECOVERY_ESTIMATES.get(risk_level, "80-90%")

        # Build the 5-step timeline with correct format
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

        result = ActionPlanResult(
            overall_risk=overall_risk,
            risk_score=risk_score,
            estimated_recovery=estimated_recovery,
            timeline=timeline,
            immediate_actions=immediate_actions,
            prevention_tips=prevention_tips,
        )

        logger.info(
            "Action plan — crop=%s, disease=%s, risk=%s (%d/100), recovery=%s",
            crop_name, disease_name, overall_risk, risk_score, estimated_recovery,
        )
        return result

    # ─── Timeline builder ─────────────────────────────────────────────────────

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
        """
        Build exactly 5 timeline steps with the required format:
        {day, action, reason}

        Days: Today, Tomorrow, After 3 Days, Next Week, Harvest
        """
        fungicide = FUNGICIDE_MAP.get(disease_name, DEFAULT_FUNGICIDE)

        # ── Today ─────────────────────────────────────────────────────────────
        today_action, today_reason = self._today_step(disease_name, severity, risk_level)

        # ── Tomorrow ──────────────────────────────────────────────────────────
        tomorrow_action, tomorrow_reason = self._tomorrow_step(
            disease_name, fungicide, humidity, rainfall_mm
        )

        # ── After 3 Days ──────────────────────────────────────────────────────
        day3_action, day3_reason = self._day3_step(
            crop_name, disease_name, severity
        )

        # ── Next Week ─────────────────────────────────────────────────────────
        week_action, week_reason = self._next_week_step(
            disease_name, severity, risk_level
        )

        # ── Harvest ───────────────────────────────────────────────────────────
        harvest_action, harvest_reason = self._harvest_step(
            crop_name, current_price, price_trend, severity
        )

        return [
            {"day": "Today",        "action": today_action,    "reason": today_reason},
            {"day": "Tomorrow",     "action": tomorrow_action, "reason": tomorrow_reason},
            {"day": "After 3 Days", "action": day3_action,     "reason": day3_reason},
            {"day": "Next Week",    "action": week_action,     "reason": week_reason},
            {"day": "Harvest",      "action": harvest_action,  "reason": harvest_reason},
        ]

    @staticmethod
    def _today_step(
        disease_name: str, severity: str, risk_level: str
    ) -> tuple[str, str]:
        if disease_name == "Healthy":
            return (
                "Inspect and document plant health",
                "Your crop appears healthy. Record baseline for future comparison.",
            )
        if risk_level == "critical":
            return (
                "Remove and destroy all infected plant parts immediately",
                "Critical infection detected. Every hour of delay increases spread exponentially.",
            )
        elif risk_level == "high":
            return (
                "Remove all visibly infected leaves and stems",
                "High severity detected. Early removal prevents the disease spreading to healthy tissue.",
            )
        else:
            return (
                "Remove infected leaves and improve field drainage",
                "Removing infected tissue reduces the spore load and slows disease progression.",
            )

    @staticmethod
    def _tomorrow_step(
        disease_name: str,
        fungicide: str,
        humidity: Optional[float],
        rainfall_mm: Optional[float],
    ) -> tuple[str, str]:
        rain_expected = rainfall_mm is not None and rainfall_mm > 2.0
        high_humidity = humidity is not None and humidity > 70

        if rain_expected:
            reason = (
                f"Rain is forecast. Apply {fungicide} before the rain for systemic protection; "
                "do not spray during or immediately after rain."
            )
        elif high_humidity:
            reason = (
                f"High humidity ({humidity:.0f}%) creates ideal conditions for disease spread. "
                f"Apply {fungicide} early morning for maximum efficacy."
            )
        else:
            reason = (
                f"Begin chemical control with {fungicide} to halt further spread. "
                "Early morning application avoids leaf burn in full sun."
            )

        if disease_name in ("Late Blight", "Yellow Leaf Curl Virus"):
            action = f"URGENT: Spray {fungicide} across entire field"
        else:
            action = f"Spray {fungicide} on affected plants"

        return action, reason

    @staticmethod
    def _day3_step(
        crop_name: str, disease_name: str, severity: str
    ) -> tuple[str, str]:
        if disease_name == "Healthy":
            return (
                "Apply balanced NPK fertilizer (19-19-19)",
                "Supports strong immune response and healthy growth.",
            )
        if severity in ("high", "critical"):
            return (
                "Apply NPK 19-19-19 or Calcium Nitrate foliar spray",
                "Disease stress depletes nutrients. Foliar feeding speeds recovery and strengthens cell walls.",
            )
        else:
            return (
                "Apply NPK 19-19-19 for plant recovery",
                "Supports plant recovery by replenishing nutrients lost to disease stress.",
            )

    @staticmethod
    def _next_week_step(
        disease_name: str, severity: str, risk_level: str
    ) -> tuple[str, str]:
        if disease_name == "Healthy":
            return (
                "Continue regular monitoring and care schedule",
                "Healthy plants benefit from consistent care to maintain yield potential.",
            )
        if risk_level in ("critical", "high"):
            return (
                "Re-inspect entire crop and apply second fungicide spray if needed",
                "High-risk diseases often require 2-3 spray cycles to achieve full control. "
                "Check for new lesions on previously healthy leaves.",
            )
        else:
            return (
                "Inspect new leaf growth for signs of disease",
                "New growth is most vulnerable. Early detection of any resurgence allows "
                "immediate action before a second wave develops.",
            )

    @staticmethod
    def _harvest_step(
        crop_name: str,
        current_price: Optional[float],
        price_trend: Optional[str],
        severity: str,
    ) -> tuple[str, str]:
        # Build price string
        if current_price:
            price_str = f"Rs {current_price:.0f}/kg"
            if price_trend == "up":
                price_advice = (
                    f"Estimated selling price {price_str} (trending up). "
                    "Wait 5-7 days for prices to peak before selling."
                )
                reason = "Market prices are rising — a short delay will increase your profit."
            elif price_trend == "down":
                price_advice = (
                    f"Estimated selling price {price_str} (trending down). "
                    "Sell within 3-5 days to maximise returns."
                )
                reason = "Prices are declining — early harvest and quick sale minimises losses."
            else:
                price_advice = (
                    f"Estimated selling price {price_str}. "
                    "Stable prices — sell when crop reaches optimal maturity."
                )
                reason = "Stable market — focus on crop quality to achieve premium pricing."
        else:
            price_advice = f"Assess {crop_name} quality and contact local market for current rates."
            reason = "Selling at peak quality and freshness maximises your return per kg."

        # Add safety notice for treated crops
        if severity in ("high", "critical"):
            reason += " Observe the fungicide pre-harvest interval (PHI) — typically 7-14 days."

        return price_advice, reason

    # ─── Immediate actions & prevention tips ──────────────────────────────────

    @staticmethod
    def _build_immediate_actions(
        disease_name: str, severity: str, risk_level: str
    ) -> list[str]:
        actions = [
            "Photograph all infected plants to document the progression.",
            "Remove and bag infected plant material — do NOT compost.",
        ]

        if risk_level in ("critical", "high"):
            actions.append(
                "Apply fungicide/bactericide TODAY — every hour of delay increases the infection area."
            )
            actions.append(
                "Isolate the affected section if possible to prevent spread to healthy rows."
            )

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
        elif disease_name == "Healthy":
            actions = [
                "Your crop appears healthy. Continue regular monitoring every 3-5 days.",
                "Maintain balanced fertilisation and consistent irrigation schedule.",
            ]

        return actions

    @staticmethod
    def _build_prevention_tips(
        crop_name: str, disease_name: str, price_trend: Optional[str]
    ) -> list[str]:
        if disease_name == "Healthy":
            return [
                f"Continue using disease-resistant {crop_name} varieties.",
                "Maintain 3-year crop rotation with non-host plants.",
                "Begin preventive fungicide spray at the start of the monsoon season.",
            ]

        tips = [
            f"Plant disease-resistant {crop_name} varieties next season.",
            "Implement 3-year crop rotation with non-host plants to break the disease cycle.",
            "Switch to drip irrigation — wet foliage is the #1 disease accelerator.",
            "Begin preventive copper sprays at first sign of warm, humid weather.",
        ]

        if price_trend == "up":
            tips.append(
                "With prices trending up, investing in quality fungicides maximises your profit."
            )
        elif price_trend == "down":
            tips.append(
                "With prices declining, use cost-effective generic fungicides (same efficacy, lower cost)."
            )

        tips.append(
            "Keep a spray diary — record all treatments, dates, and rates for reference."
        )
        return tips

    # ─── Risk score calculation ───────────────────────────────────────────────

    @staticmethod
    def _calculate_risk_score(
        disease_name: str,
        severity: str,
        confidence: float,
        temperature: Optional[float],
        humidity: Optional[float],
        crop_name: str,
    ) -> int:
        """
        Calculate 0-100 risk score.

        Breakdown:
          Severity base:       0-40 pts
          Confidence:          0-10 pts
          Humidity penalty:    0-15 pts
          Temperature penalty: 0-10 pts
          Disease modifier:   -20 to +20 pts
          High-value crop:     +5 pts
        """
        # 1. Severity base (scale from 90-max to 40-max)
        base = SEVERITY_SCORES.get(severity, 40)
        score = int(base * 0.44)

        # 2. Confidence weight
        score += int(confidence * 10)

        # 3. Humidity penalty
        if humidity is not None:
            if humidity > 80:
                score += 15
            elif humidity > 70:
                score += 10
            elif humidity > 60:
                score += 5

        # 4. Temperature penalty (fungal pathogens peak 20-32°C)
        if temperature is not None:
            if 20 <= temperature <= 32:
                score += 10
            elif 15 <= temperature < 20 or 32 < temperature <= 38:
                score += 5

        # 5. Disease-specific modifier
        score += DISEASE_RISK_MODIFIERS.get(disease_name, 0)

        # 6. High-value crop modifier
        if crop_name in HIGH_VALUE_CROPS:
            score += 5

        return max(0, min(100, score))

    @staticmethod
    def _score_to_level(score: int) -> str:
        if score >= 75:
            return "critical"
        elif score >= 55:
            return "high"
        elif score >= 30:
            return "moderate"
        else:
            return "low"


# ─── Singleton ────────────────────────────────────────────────────────────────
action_plan_service = ActionPlanService()
