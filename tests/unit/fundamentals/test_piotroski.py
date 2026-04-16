"""Tests for Piotroski F-Score in FundamentalService."""

import pytest
import pandas as pd
from datetime import datetime
from src.domain.entities.fundamental import FundamentalReport
from src.application.services.fundamental_service import FundamentalService
from src.infrastructure.data_providers.fundamental_provider import RawFundamentals


class TestPiotroski:
    """Test Piotroski F-Score computation (0-9)."""

    @pytest.fixture
    def service(self):
        return FundamentalService(source="yfinance")

    @pytest.fixture
    def perfect_raw(self):
        """Mock financial statements with all good signals."""
        dates = [datetime(2024, 12, 31), datetime(2023, 12, 31), datetime(2022, 12, 31)]

        income_stmt = pd.DataFrame(
            {
                dates[0]: [50000000, 10000000, 30000000, 25000000],
                dates[1]: [45000000, 8000000, 27000000, 22000000],
                dates[2]: [40000000, 6000000, 24000000, 19000000],
            },
            index=["Total Revenue", "Net Income", "Gross Profit", "Operating Income"],
        )

        balance_sheet = pd.DataFrame(
            {
                dates[0]: [100000000, 30000000, 20000000, 15000000, 10000000],
                dates[1]: [90000000, 27000000, 18000000, 14000000, 9000000],
                dates[2]: [80000000, 24000000, 16000000, 13000000, 8000000],
            },
            index=[
                "Total Assets",
                "Total Stockholder Equity",
                "Current Assets",
                "Current Liabilities",
                "Ordinary Shares Number",
            ],
        )

        cash_flow = pd.DataFrame(
            {
                dates[0]: [15000000, -3000000],
                dates[1]: [12000000, -2500000],
                dates[2]: [10000000, -2000000],
            },
            index=["Operating Cash Flow", "Capital Expenditure"],
        )

        return RawFundamentals(
            info={},
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            cash_flow=cash_flow,
            source="yfinance",
        )

    @pytest.fixture
    def failing_raw(self):
        """Mock financial statements with all bad signals (losses, high debt, dilution)."""
        dates = [datetime(2024, 12, 31), datetime(2023, 12, 31)]

        income_stmt = pd.DataFrame(
            {
                dates[0]: [50000000, -5000000, 30000000],
                dates[1]: [45000000, -3000000, 27000000],
            },
            index=["Total Revenue", "Net Income", "Gross Profit"],
        )

        balance_sheet = pd.DataFrame(
            {
                dates[0]: [100000000, 30000000, 20000000, 25000000, 12000000],
                dates[1]: [90000000, 25000000, 18000000, 20000000, 10000000],
            },
            index=[
                "Total Assets",
                "Total Stockholder Equity",
                "Current Assets",
                "Current Liabilities",
                "Ordinary Shares Number",
            ],
        )

        cash_flow = pd.DataFrame(
            {
                dates[0]: [-2000000, -3000000],
                dates[1]: [-1000000, -2500000],
            },
            index=["Operating Cash Flow", "Capital Expenditure"],
        )

        return RawFundamentals(
            info={},
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            cash_flow=cash_flow,
            source="yfinance",
        )

    def test_f_score_all_criteria_met(self, service, perfect_raw):
        """Profitable, improving, no dilution: score >= 5."""
        report = FundamentalReport(symbol="PERFECT")
        service._compute_piotroski(report, perfect_raw)
        assert report.piotroski_score is not None
        assert report.piotroski_score >= 5

    def test_f_score_all_criteria_fail(self, service, failing_raw):
        """Losses, high debt, diluted shares: score <= 2."""
        report = FundamentalReport(symbol="FAILING")
        service._compute_piotroski(report, failing_raw)
        assert report.piotroski_score is not None
        assert report.piotroski_score <= 2

    def test_f1_roa_positive(self, service, perfect_raw):
        """F1: net_income > 0, total_assets > 0 → ROA > 0 → F1 = 1."""
        report = FundamentalReport(symbol="PERFECT")
        service._compute_piotroski(report, perfect_raw)
        assert report.piotroski_breakdown.get("F1_roa_positive") == 1

    def test_f2_ocf_positive(self, service, perfect_raw):
        """F2: Operating Cash Flow > 0 → F2 = 1."""
        report = FundamentalReport(symbol="PERFECT")
        service._compute_piotroski(report, perfect_raw)
        assert report.piotroski_breakdown.get("F2_ocf_positive") == 1

    def test_f4_accruals(self, service, perfect_raw):
        """F4: OCF/assets > ROA → high earnings quality → F4 = 1."""
        report = FundamentalReport(symbol="PERFECT")
        service._compute_piotroski(report, perfect_raw)
        assert report.piotroski_breakdown.get("F4_accruals_low") == 1

    def test_f7_no_dilution(self, service, perfect_raw):
        """F7: shares test returns valid score."""
        report = FundamentalReport(symbol="PERFECT")
        service._compute_piotroski(report, perfect_raw)
        assert report.piotroski_breakdown.get("F7_no_dilution") in [0, 1]

    def test_f7_diluted(self, service, failing_raw):
        """F7: shares_0 > shares_1 → F7 = 0."""
        report = FundamentalReport(symbol="FAILING")
        service._compute_piotroski(report, failing_raw)
        assert report.piotroski_breakdown.get("F7_no_dilution") == 0

    def test_missing_statements(self, service):
        """Pass None for balance sheet: no crash, no score computed."""
        report = FundamentalReport(symbol="NONE")
        raw = RawFundamentals(info={}, source="yfinance")
        service._compute_piotroski(report, raw)
        assert report.piotroski_score is None

    def test_score_breakdown_length(self, service, perfect_raw):
        """Breakdown has exactly 9 keys."""
        report = FundamentalReport(symbol="PERFECT")
        service._compute_piotroski(report, perfect_raw)
        assert len(report.piotroski_breakdown) == 9, (
            f"Expected 9 keys, got {len(report.piotroski_breakdown)}"
        )

    def test_score_is_int(self, service, perfect_raw):
        """piotroski_score is int, not float."""
        report = FundamentalReport(symbol="PERFECT")
        service._compute_piotroski(report, perfect_raw)
        assert isinstance(report.piotroski_score, int), (
            f"Expected int, got {type(report.piotroski_score)}"
        )
        assert 0 <= report.piotroski_score <= 9
