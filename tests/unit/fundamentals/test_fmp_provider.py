"""Tests for FMP data provider normalisation.

We test FMPFundamentalProvider directly so we can inject a dummy API key
without triggering the production guard that raises on missing keys.
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.infrastructure.data_providers.fundamental_provider import (
    FMPFundamentalProvider,
    FundamentalProviderError,
)


@pytest.fixture
def provider():
    """FMPFundamentalProvider with a dummy key — no real network calls made."""
    return FMPFundamentalProvider(api_key="test_dummy_key")


# ── _build_info() — field mapping ────────────────────────────────────────────

class TestBuildInfo:
    """Test that FMP JSON fields are correctly mapped to yfinance-compatible keys."""

    def test_maps_company_name(self, provider):
        profile = [{"companyName": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics"}]
        info = provider._build_info(profile, [], [])
        assert info["shortName"] == "Apple Inc."
        assert info["sector"] == "Technology"
        assert info["industry"] == "Consumer Electronics"

    def test_maps_pe_ratio(self, provider):
        ratios = [{"priceEarningsRatio": 28.5, "priceEarningsToGrowthRatio": 1.4}]
        info = provider._build_info([], ratios, [])
        assert info["trailingPE"] == 28.5
        assert info["trailingPegRatio"] == 1.4

    def test_forward_pe_not_equal_peg(self, provider):
        """forwardPE and peg_ratio should come from different fields."""
        ratios = [{"priceEarningsRatio": 25.0, "priceEarningsToGrowthRatio": 1.5}]
        info = provider._build_info([], ratios, [])
        # trailingPE (25.0) must not equal trailingPegRatio (1.5)
        assert info["trailingPE"] != info["trailingPegRatio"]

    def test_maps_profitability(self, provider):
        ratios = [{"grossProfitMargin": 0.43, "netProfitMargin": 0.25, "returnOnEquity": 0.31}]
        info = provider._build_info([], ratios, [])
        assert info["grossMargins"] == 0.43
        assert info["profitMargins"] == 0.25
        assert info["returnOnEquity"] == 0.31

    def test_maps_liquidity(self, provider):
        ratios = [{"currentRatio": 1.5, "quickRatio": 1.2}]
        info = provider._build_info([], ratios, [])
        assert info["currentRatio"] == 1.5
        assert info["quickRatio"] == 1.2

    def test_empty_profile_no_crash(self, provider):
        info = provider._build_info([], [], [])
        assert isinstance(info, dict)
        assert info["shortName"] == ""

    def test_list_profile_takes_first(self, provider):
        profile = [
            {"companyName": "First Corp."},
            {"companyName": "Should Not Appear"},
        ]
        info = provider._build_info(profile, [], [])
        assert info["shortName"] == "First Corp."


# ── _statements_to_df() — DataFrame conversion ───────────────────────────────

class TestStatementsToDf:
    """Test that FMP statement lists are correctly pivoted into DataFrames."""

    def test_df_has_correct_shape(self, provider):
        statements = [
            {"date": "2024-12-31", "revenue": 50_000_000, "netIncome": 10_000_000},
            {"date": "2023-12-31", "revenue": 45_000_000, "netIncome":  8_000_000},
        ]
        df = provider._statements_to_df(statements)
        assert df is not None
        # Rows = line items, cols = dates
        assert df.shape[1] == 2   # 2 years

    def test_revenue_renamed_to_total_revenue(self, provider):
        statements = [{"date": "2024-12-31", "revenue": 50_000_000}]
        df = provider._statements_to_df(statements)
        assert df is not None
        assert "Total Revenue" in df.index

    def test_net_income_renamed(self, provider):
        statements = [{"date": "2024-12-31", "netIncome": 12_000_000}]
        df = provider._statements_to_df(statements)
        assert df is not None
        assert "Net Income" in df.index

    def test_operating_cash_flow_renamed(self, provider):
        statements = [{"date": "2024-12-31", "operatingCashFlow": 8_000_000}]
        df = provider._statements_to_df(statements)
        assert df is not None
        assert "Operating Cash Flow" in df.index

    def test_empty_list_returns_none(self, provider):
        result = provider._statements_to_df([])
        assert result is None

    def test_values_are_numeric(self, provider):
        statements = [{"date": "2024-12-31", "revenue": "50000000"}]
        df = provider._statements_to_df(statements)
        assert df is not None
        assert pd.api.types.is_numeric_dtype(df.loc["Total Revenue"])

    def test_metadata_rows_dropped(self, provider):
        """Non-numeric metadata fields like 'symbol', 'period' are not kept as rows."""
        statements = [{
            "date": "2024-12-31",
            "symbol": "AAPL",
            "period": "FY",
            "revenue": 50_000_000,
        }]
        df = provider._statements_to_df(statements)
        assert df is not None
        assert "symbol" not in df.index
        assert "period" not in df.index


# ── fetch() error handling ────────────────────────────────────────────────────

class TestFMPFetch:
    """Test that network errors and bad responses raise FundamentalProviderError."""

    @patch("requests.get")
    def test_api_error_message_raises(self, mock_get, provider):
        """FMP error JSON → FundamentalProviderError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"Error Message": "Invalid API call."}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with pytest.raises(FundamentalProviderError):
            provider.fetch("INVALID_XYZ")

    @patch("requests.get")
    def test_network_timeout_raises(self, mock_get, provider):
        """Network timeout → FundamentalProviderError."""
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.Timeout

        with pytest.raises(FundamentalProviderError):
            provider.fetch("AAPL")
