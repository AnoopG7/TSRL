"""Tests for CAGR helper in FundamentalService."""

import pytest
from src.application.services.fundamental_service import FundamentalService


class TestCAGR:
    """Test CAGR computation for growth trends."""

    @pytest.fixture
    def service(self):
        return FundamentalService(source="yfinance")

    def test_cagr_standard(self, service):
        """start=100, end=200, years=3 → ≈ 0.2599 (26%)."""
        result = service._cagr(200, 100, 3)
        assert result is not None
        expected = (200 / 100) ** (1 / 3) - 1
        assert abs(result - expected) < 0.0001

    def test_cagr_flat(self, service):
        """start=100, end=100, years=3 → 0.0."""
        result = service._cagr(100, 100, 3)
        assert result is not None
        assert result == 0.0

    def test_cagr_zero_years(self, service):
        """years=0 → None."""
        result = service._cagr(200, 100, 0)
        assert result is None

    def test_cagr_zero_start(self, service):
        """start=0 → None."""
        result = service._cagr(200, 0, 3)
        assert result is None

    def test_cagr_negative_to_positive(self, service):
        """start=-50, end=100, years=3 → turnaround proxy, not None."""
        result = service._cagr(100, -50, 3)
        assert result is not None
        assert result > 0

    def test_cagr_negative_to_negative(self, service):
        """start=-100, end=-60 (improving): positive improvement rate."""
        result = service._cagr(-60, -100, 3)
        assert result is not None
        assert result > 0

    def test_cagr_positive_to_negative(self, service):
        """start=100, end=-10 → None (total decline, undefined)."""
        result = service._cagr(-10, 100, 3)
        assert result is None
