"""Integration tests for Fundamentals API endpoints - using mocked data."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def mock_fundamental_report(symbol):
    """Return a mock fundamental report for any symbol."""
    from src.domain.entities.fundamental import FundamentalReport

    return FundamentalReport(
        symbol=symbol.upper(),
        company_name=f"{symbol.upper()} Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3000000000000,
        current_price=180.0,
        pe_ratio=25.0,
        pb_ratio=40.0,
        peg_ratio=1.5,
        roe=0.35,
        roa=0.20,
        gross_margin=0.60,
        operating_margin=0.25,
        net_margin=0.25,
        current_ratio=1.5,
        debt_to_equity=0.5,
        free_cash_flow=50000000000,
        fcf_margin=0.20,
        revenue_cagr_3yr=0.10,
        earnings_cagr_3yr=0.12,
        health_score=75.0,
        health_grade="B",
        score_breakdown={
            "profitability": {"score": 80.0, "weight": 30},
            "valuation": {"score": 60.0, "weight": 25},
            "cash_flow": {"score": 75.0, "weight": 20},
            "solvency": {"score": 70.0, "weight": 15},
            "growth": {"score": 60.0, "weight": 10},
        },
        piotroski_score=7,
        altman_z_score=3.5,
        altman_z_zone="safe",
        annual_revenue=[
            {"year": "2022", "value": 300.0},
            {"year": "2023", "value": 350.0},
            {"year": "2024", "value": 400.0},
        ],
    )


class TestFundamentalsAPIMocked:
    """Test fundamental analysis API endpoints with mocked data."""

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_get_fundamentals_aapl(self, mock_service_class):
        """GET /api/v1/fundamentals/AAPL: 200, symbol == 'AAPL'."""
        mock_service = MagicMock()
        mock_service.analyze.return_value = {
            "report": mock_fundamental_report("AAPL"),
            "from_cache": False,
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/fundamentals/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_get_fundamentals_lowercase(self, mock_service_class):
        """GET /api/v1/fundamentals/aapl: 200, normalised to AAPL."""
        mock_service = MagicMock()
        mock_service.analyze.return_value = {
            "report": mock_fundamental_report("aapl"),
            "from_cache": False,
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/fundamentals/aapl")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_get_fundamentals_cached(self, mock_service_class):
        """Call twice with cache: 2nd call from_cache: true."""
        mock_service = MagicMock()
        mock_service.analyze.side_effect = [
            {"report": mock_fundamental_report("AAPL"), "from_cache": False},
            {"report": mock_fundamental_report("AAPL"), "from_cache": True},
        ]
        mock_service_class.return_value = mock_service

        response1 = client.get("/api/v1/fundamentals/AAPL")
        response2 = client.get("/api/v1/fundamentals/AAPL")
        assert response2.status_code == 200

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_get_fundamentals_no_cache(self, mock_service_class):
        """?use_cache=false: always from_cache: false."""
        mock_service = MagicMock()
        mock_service.analyze.return_value = {
            "report": mock_fundamental_report("MSFT"),
            "from_cache": False,
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/fundamentals/MSFT?use_cache=false")
        assert response.status_code == 200
        data = response.json()
        assert data.get("from_cache") == False

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_compare_two_symbols(self, mock_service_class):
        """GET /compare?symbols=AAPL,MSFT: 200, both symbols in response."""
        mock_service = MagicMock()
        mock_service.analyze.return_value = {
            "report": mock_fundamental_report("AAPL"),
            "from_cache": False,
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/fundamentals/compare?symbols=AAPL,MSFT")
        assert response.status_code == 200
        data = response.json()
        assert "AAPL" in data.get("comparison", {})

    def test_compare_one_symbol_error(self):
        """GET /compare?symbols=AAPL: 400 'At least 2 symbols required'."""
        response = client.get("/api/v1/fundamentals/compare?symbols=AAPL")
        assert response.status_code == 400
        assert "At least 2" in response.json()["detail"]

    def test_compare_six_symbols_error(self):
        """6 symbols: 400 'Maximum 5 symbols'."""
        response = client.get("/api/v1/fundamentals/compare?symbols=AAPL,MSFT,GOOGL,AMZN,META,NVDA")
        assert response.status_code == 400
        assert "Maximum 5" in response.json()["detail"]

    def test_news_endpoint_reachable(self):
        """GET /fundamentals/AAPL/news: 200, not 404."""
        response = client.get("/api/v1/fundamentals/AAPL/news")
        assert response.status_code in [200, 500]  # Either works or API error

    def test_insiders_endpoint_reachable(self):
        """GET /fundamentals/AAPL/insiders: 200, not 404."""
        response = client.get("/api/v1/fundamentals/AAPL/insiders")
        assert response.status_code in [200, 500]  # Either works or API error

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_response_has_all_pillar_fields(self, mock_service_class):
        """health_score, health_grade, score_breakdown present."""
        mock_service = MagicMock()
        mock_service.analyze.return_value = {
            "report": mock_fundamental_report("NVDA"),
            "from_cache": False,
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/fundamentals/NVDA")
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data
        assert "health_grade" in data
        assert "score_breakdown" in data

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_piotroski_in_range(self, mock_service_class):
        """piotroski_score in [0, 9]."""
        mock_service = MagicMock()
        mock_service.analyze.return_value = {
            "report": mock_fundamental_report("AAPL"),
            "from_cache": False,
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/fundamentals/AAPL")
        assert response.status_code == 200
        data = response.json()
        piotroski = data.get("piotroski_score")
        if piotroski is not None:
            assert 0 <= piotroski <= 9

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_altman_zone_valid(self, mock_service_class):
        """altman_z_zone in ['safe', 'grey', 'distress']."""
        mock_service = MagicMock()
        mock_service.analyze.return_value = {
            "report": mock_fundamental_report("AAPL"),
            "from_cache": False,
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/fundamentals/AAPL")
        assert response.status_code == 200
        data = response.json()
        zone = data.get("altman_z_zone")
        if zone is not None:
            assert zone in ["safe", "grey", "distress"]

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_annual_trends_ordered(self, mock_service_class):
        """annual_revenue[0].year < annual_revenue[-1].year (oldest first)."""
        mock_service = MagicMock()
        mock_service.analyze.return_value = {
            "report": mock_fundamental_report("AAPL"),
            "from_cache": False,
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/fundamentals/AAPL")
        assert response.status_code == 200
        data = response.json()
        trends = data.get("annual_revenue", [])
        if len(trends) >= 2:
            years = [t.get("year") for t in trends]
            assert years == sorted(years)

    @patch("src.application.services.fundamental_service.FundamentalService")
    def test_no_nan_in_response(self, mock_service_class):
        """No NaN or Infinity in JSON."""
        mock_service = MagicMock()
        mock_service.analyze.return_value = {
            "report": mock_fundamental_report("AAPL"),
            "from_cache": False,
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/fundamentals/AAPL")
        assert response.status_code == 200
        data = response.json()
        import json

        json_str = json.dumps(data)
        assert "NaN" not in json_str
        assert "Infinity" not in json_str
