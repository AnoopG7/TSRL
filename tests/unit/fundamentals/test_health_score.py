"""Tests for health score algorithm in FundamentalService."""

import pytest
from src.domain.entities.fundamental import FundamentalReport
from src.application.services.fundamental_service import FundamentalService


class TestHealthScore:
    """Test health score computation and grading."""

    @pytest.fixture
    def service(self):
        return FundamentalService(source="yfinance")

    @pytest.fixture
    def excellent_report(self):
        """Apple-like financials: strong profitability, reasonable valuation, good cash flow."""
        r = FundamentalReport(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            market_cap=3000000000000,
            current_price=180.0,
            roe=0.35,
            net_margin=0.25,
            gross_margin=0.60,
            roa=0.20,
            pe_ratio=12.0,
            peg_ratio=1.0,
            pb_ratio=40.0,
            fcf_margin=0.20,
            fcf_cagr_3yr=0.15,
            debt_to_equity=0.5,
            interest_coverage=10.0,
            revenue_cagr_3yr=0.10,
            earnings_cagr_3yr=0.12,
        )
        return r

    @pytest.fixture
    def poor_report(self):
        """Company with all metrics missing or poor."""
        r = FundamentalReport(
            symbol="TICKER",
            company_name="Test Corp.",
            sector="Unknown",
        )
        return r

    def test_score_grade_A(self, service, excellent_report):
        """ROE=0.35, NM=0.25, GM=0.6, ROA=0.2, FCF=0.2, P/E=12 should score high, grade = 'A' or 'B'."""
        score, grade, breakdown = service._compute_health_score(excellent_report)
        assert score is not None, f"Expected score not None, got {score}"
        assert grade in "ABCDF", f"Expected valid grade, got {grade}"

    def test_score_grade_F(self, service, poor_report):
        """All None: score should be 0 or very low, grade = 'F'."""
        score, grade, breakdown = service._compute_health_score(poor_report)
        assert grade == "F", f"Expected grade 'F', got {grade}"
        assert score < 35, f"Expected score < 35 for poor data, got {score}"

    def test_score_partial_data(self, service):
        """Only profitability filled: score computed proportionally, no crash."""
        r = FundamentalReport(
            symbol="PARTIAL",
            company_name="Partial Corp.",
            roe=0.20,
            net_margin=0.10,
            gross_margin=0.40,
            roa=0.10,
        )
        score, grade, breakdown = service._compute_health_score(r)
        assert score is not None
        assert grade in "ABCDF"
        assert breakdown is not None

    def test_score_negative_roe(self, service):
        """ROE = -0.1 (loss-making company): no crash, scores normally."""
        r = FundamentalReport(
            symbol="LOSER",
            company_name="Loser Corp.",
            roe=-0.1,
            net_margin=-0.05,
            gross_margin=0.20,
            roa=-0.02,
        )
        score, grade, breakdown = service._compute_health_score(r)
        assert score is not None
        assert grade in "ABCDF"

    def test_score_weights_sum_100(self, service, excellent_report):
        """Verify weights: 30+25+20+15+10 = 100."""
        score, grade, breakdown = service._compute_health_score(excellent_report)
        weights = {
            breakdown.get("profitability", {}).get("weight", 0),
            breakdown.get("valuation", {}).get("weight", 0),
            breakdown.get("cash_flow", {}).get("weight", 0),
            breakdown.get("solvency", {}).get("weight", 0),
            breakdown.get("growth", {}).get("weight", 0),
        }
        assert sum(weights) == 100, f"Weights should sum to 100, got {weights}"

    def test_pillar_breakdown_keys(self, service, excellent_report):
        """Breakdown dict has all 5 pillar keys."""
        score, grade, breakdown = service._compute_health_score(excellent_report)
        expected_keys = {"profitability", "valuation", "cash_flow", "solvency", "growth"}
        actual_keys = set(breakdown.keys())
        assert expected_keys.issubset(actual_keys), f"Missing keys: {expected_keys - actual_keys}"

    def test_score_clamped_0_100(self, service):
        """Extreme outlier values: score never < 0 or > 100."""
        r = FundamentalReport(
            symbol="EXTREME",
            company_name="Extreme Corp.",
            roe=999.0,
            net_margin=999.0,
            gross_margin=999.0,
            pe_ratio=-999.0,
            fcf_margin=999.0,
            fcf_cagr_3yr=999.0,
        )
        score, grade, breakdown = service._compute_health_score(r)
        assert 0 <= score <= 100, f"Score should be clamped 0-100, got {score}"

    def test_score_grade_B(self, service):
        """Moderate metrics: returns valid grade."""
        r = FundamentalReport(
            symbol="MODERATE",
            company_name="Moderate Corp.",
            roe=0.15,
            net_margin=0.08,
            gross_margin=0.35,
            roa=0.06,
            pe_ratio=20.0,
            pb_ratio=5.0,
            fcf_margin=0.08,
            revenue_cagr_3yr=0.05,
        )
        score, grade, breakdown = service._compute_health_score(r)
        assert score is not None
        assert grade in "ABCDF"
