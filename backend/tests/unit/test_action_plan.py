"""
Unit tests for the ActionPlanService.
These are pure Python tests — no HTTP or database calls.
"""

import pytest
from app.services.action_plan import ActionPlanService, ActionPlanResult


@pytest.fixture
def service() -> ActionPlanService:
    return ActionPlanService()


class TestRiskScoreCalculation:
    def test_healthy_disease_has_low_score(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Tomato",
            disease_name="Healthy",
            severity="low",
            confidence=0.99,
        )
        assert result.risk_score < 20

    def test_critical_severity_has_high_score(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Tomato",
            disease_name="Late Blight",
            severity="critical",
            confidence=0.98,
            humidity=85.0,
            temperature=28.0,
        )
        assert result.risk_score >= 70

    def test_high_humidity_increases_score(self, service: ActionPlanService):
        result_low_humidity = service.generate(
            crop_name="Tomato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.90,
            humidity=30.0,
        )
        result_high_humidity = service.generate(
            crop_name="Tomato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.90,
            humidity=85.0,
        )
        assert result_high_humidity.risk_score > result_low_humidity.risk_score

    def test_temperature_in_sweet_spot_increases_score(self, service: ActionPlanService):
        result_cold = service.generate(
            crop_name="Potato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.90,
            temperature=5.0,
        )
        result_warm = service.generate(
            crop_name="Potato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.90,
            temperature=26.0,
        )
        assert result_warm.risk_score > result_cold.risk_score

    def test_score_clamped_between_0_and_100(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Apple",
            disease_name="Late Blight",
            severity="critical",
            confidence=1.0,
            humidity=95.0,
            temperature=28.0,
        )
        assert 0 <= result.risk_score <= 100

    def test_low_severity_returns_low_risk_label(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Wheat",
            disease_name="Common Rust",
            severity="low",
            confidence=0.75,
            humidity=40.0,
            temperature=10.0,
        )
        assert result.overall_risk in ("Low", "Medium")

    def test_critical_severity_returns_high_or_critical_label(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Tomato",
            disease_name="Late Blight",
            severity="critical",
            confidence=0.98,
            humidity=80.0,
            temperature=26.0,
        )
        assert result.overall_risk in ("High", "Critical")


class TestTimelineGeneration:
    def test_timeline_not_empty(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Tomato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.95,
        )
        assert len(result.timeline) > 0

    def test_timeline_items_have_required_fields(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Tomato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.95,
        )
        for item in result.timeline:
            assert "day" in item
            assert "action" in item
            assert "reason" in item

    def test_timeline_reason_values(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Tomato",
            disease_name="Early Blight",
            severity="high",
            confidence=0.95,
        )
        for item in result.timeline:
            assert isinstance(item["reason"], str)
            assert len(item["reason"]) > 0


class TestImmediateActions:
    def test_immediate_actions_not_empty(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Potato",
            disease_name="Late Blight",
            severity="high",
            confidence=0.97,
        )
        assert len(result.immediate_actions) > 0

    def test_late_blight_has_urgent_message(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Potato",
            disease_name="Late Blight",
            severity="critical",
            confidence=0.97,
        )
        full_text = " ".join(result.immediate_actions).lower()
        assert "late blight" in full_text or "urgent" in full_text or "days" in full_text


class TestPreventionTips:
    def test_prevention_tips_not_empty(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Tomato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.90,
        )
        assert len(result.prevention_tips) > 0

    def test_price_trend_up_adds_market_tip(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Tomato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.90,
            price_trend="up",
        )
        full_text = " ".join(result.prevention_tips).lower()
        assert "price" in full_text or "invest" in full_text


class TestRecoveryEstimate:
    def test_recovery_estimate_present(self, service: ActionPlanService):
        result = service.generate(
            crop_name="Tomato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.90,
        )
        assert result.estimated_recovery != ""
        assert "%" in result.estimated_recovery

    def test_critical_severity_lower_recovery(self, service: ActionPlanService):
        moderate = service.generate(
            crop_name="Tomato",
            disease_name="Early Blight",
            severity="moderate",
            confidence=0.90,
        )
        critical = service.generate(
            crop_name="Tomato",
            disease_name="Late Blight",
            severity="critical",
            confidence=0.98,
            humidity=85.0,
        )
        # Extract lower bound of percentage range and compare
        def lower_bound(s: str) -> int:
            return int(s.split("-")[0].strip().replace("%", ""))

        assert lower_bound(critical.estimated_recovery) <= lower_bound(moderate.estimated_recovery)
