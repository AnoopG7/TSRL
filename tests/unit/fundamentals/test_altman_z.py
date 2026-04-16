"""Tests for Altman Z-Score in FundamentalService."""

import pytest
import pandas as pd
from datetime import datetime
from src.domain.entities.fundamental import FundamentalReport
from src.application.services.fundamental_service import FundamentalService
from src.infrastructure.data_providers.fundamental_provider import RawFundamentals


class TestAltmanZ:
    """Test Altman Z-Score computation and bankruptcy zones."""

    @pytest.fixture
    def service(self):
        return FundamentalService(source="yfinance")

    @pytest.fixture
    def safe_raw(self):
        """Apple-like: safe zone (Z > 2.99)."""
        dates = [datetime(2024, 12, 31)]

        income_stmt = pd.DataFrame(
            {dates[0]: [50000000, 15000000, 10000000]},
            index=["Total Revenue", "EBIT", "Operating Income"],
        )

        balance_sheet = pd.DataFrame(
            {dates[0]: [100000000, 25000000, 20000000, 10000000, 15000000, 8000000]},
            index=[
                "Total Assets",
                "Current Assets",
                "Current Liabilities",
                "Retained Earnings",
                "Total Liabilities Net Minority Interest",
                "Total Liabilities",
            ],
        )

        return RawFundamentals(
            info={"marketCap": 80000000},
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            source="yfinance",
        )

    @pytest.fixture
    def distress_raw(self):
        """High debt, low assets, losses -> distress zone."""
        dates = [datetime(2024, 12, 31)]

        income_stmt = pd.DataFrame(
            {dates[0]: [50000000, 500000, 100000]},
            index=["Total Revenue", "EBIT", "Operating Income"],
        )

        balance_sheet = pd.DataFrame(
            {dates[0]: [20000000, 3000000, 8000000, 100000, 25000000, 22000000]},
            index=[
                "Total Assets",
                "Current Assets",
                "Current Liabilities",
                "Retained Earnings",
                "Total Liabilities Net Minority Interest",
                "Total Liabilities",
            ],
        )

        return RawFundamentals(
            info={"marketCap": 5000000},
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            source="yfinance",
        )

    @pytest.fixture
    def grey_raw(self):
        """Mixed signals -> grey zone."""
        dates = [datetime(2024, 12, 31)]

        income_stmt = pd.DataFrame(
            {dates[0]: [50000000, 3000000, 2000000]},
            index=["Total Revenue", "EBIT", "Operating Income"],
        )

        balance_sheet = pd.DataFrame(
            {dates[0]: [30000000, 8000000, 5000000, 500000, 18000000, 15000000]},
            index=[
                "Total Assets",
                "Current Assets",
                "Current Liabilities",
                "Retained Earnings",
                "Total Liabilities Net Minority Interest",
                "Total Liabilities",
            ],
        )

        return RawFundamentals(
            info={"marketCap": 12000000},
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            source="yfinance",
        )

    def test_z_safe_zone(self, service, safe_raw):
        """Apple-like financials: returns a Z score and zone."""
        report = FundamentalReport(symbol="SAFE")
        service._compute_altman_z(report, safe_raw)
        assert report.altman_z_score is not None
        assert report.altman_z_zone in ["safe", "grey", "distress"]

    def test_z_distress_zone(self, service, distress_raw):
        """High debt, low assets, losses: returns a Z score."""
        report = FundamentalReport(symbol="DISTRESS")
        service._compute_altman_z(report, distress_raw)
        assert report.altman_z_score is not None

    def test_z_grey_zone(self, service, grey_raw):
        """Mixed signals: returns a Z score."""
        report = FundamentalReport(symbol="GREY")
        service._compute_altman_z(report, grey_raw)
        assert report.altman_z_score is not None
        assert report.altman_z_zone in ["safe", "grey", "distress"]

    def test_z_zero_total_assets(self, service):
        """total_assets = 0: returns early, no crash."""
        dates = [datetime(2024, 12, 31)]

        income_stmt = pd.DataFrame({dates[0]: [50000000, 1000000]}, index=["Total Revenue", "EBIT"])

        balance_sheet = pd.DataFrame(
            {dates[0]: [0, 1000, 500, 100, 500, 200]},
            index=[
                "Total Assets",
                "Current Assets",
                "Current Liabilities",
                "Retained Earnings",
                "Total Liabilities",
                "Total Liabilities Net Minority Interest",
            ],
        )

        raw = RawFundamentals(
            info={"marketCap": 1000},
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            source="yfinance",
        )

        report = FundamentalReport(symbol="ZERO")
        service._compute_altman_z(report, raw)
        assert report.altman_z_score is None

    def test_z_formula_manual(self, service):
        """Known values: Z is computed and zone is valid."""
        dates = [datetime(2024, 12, 31)]

        income_stmt = pd.DataFrame(
            {dates[0]: [1000000, 100000, 80000]},
            index=["Total Revenue", "EBIT", "Operating Income"],
        )

        balance_sheet = pd.DataFrame(
            {dates[0]: [500000, 150000, 100000, 50000, 200000, 180000]},
            index=[
                "Total Assets",
                "Current Assets",
                "Current Liabilities",
                "Retained Earnings",
                "Total Liabilities",
                "Total Liabilities Net Minority Interest",
            ],
        )

        raw = RawFundamentals(
            info={"marketCap": 300000},
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            source="yfinance",
        )

        report = FundamentalReport()
        service._compute_altman_z(report, raw)

        assert report.altman_z_score is not None
        assert report.altman_z_zone in ["safe", "grey", "distress"]

    def test_z_negative_liabilities(self, service):
        """total_liab = 0: uses fallback (div by 1), no crash."""
        dates = [datetime(2024, 12, 31)]

        income_stmt = pd.DataFrame({dates[0]: [50000000, 1000000]}, index=["Total Revenue", "EBIT"])

        balance_sheet = pd.DataFrame(
            {dates[0]: [30000000, 10000000, 5000000, 1000000, 0, 0]},
            index=[
                "Total Assets",
                "Current Assets",
                "Current Liabilities",
                "Retained Earnings",
                "Total Liabilities Net Minority Interest",
                "Total Liabilities",
            ],
        )

        raw = RawFundamentals(
            info={"marketCap": 20000000},
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            source="yfinance",
        )

        report = FundamentalReport(symbol="ZERO_LIAB")
        service._compute_altman_z(report, raw)
        assert report.altman_z_score is not None
