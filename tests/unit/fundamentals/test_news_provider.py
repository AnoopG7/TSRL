"""Tests for NewsProvider.

We isolate tests from environment API keys by patching os.environ
so that 'no keys' tests don't accidentally pass because a real key is set.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.infrastructure.data_providers.news_provider import NewsProvider


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def provider():
    """Provider with a finnhub key set (mocked, not real)."""
    return NewsProvider(finnhub_key="test_finnhub_key", av_key="test_av_key")


@pytest.fixture
def provider_no_keys():
    """Provider with absolutely no API keys — env is patched to be empty."""
    with patch.dict("os.environ", {}, clear=True):
        p = NewsProvider(finnhub_key=None, av_key=None)
    return p


# ── No-key behaviour ──────────────────────────────────────────────────────────

class TestNewsProviderNoKeys:
    """Test graceful degradation when no API keys are available."""

    def test_get_company_news_returns_empty_list(self, provider_no_keys):
        """No keys → returns empty list, no crash."""
        result = provider_no_keys.get_company_news("AAPL")
        assert isinstance(result, list)
        assert result == []

    def test_get_sentiment_returns_neutral(self, provider_no_keys):
        """No keys → returns neutral sentinel dict."""
        result = provider_no_keys.get_sentiment("AAPL")
        assert result["avg_sentiment"] == 0.0
        assert result["label"] == "Neutral"
        assert result["article_count"] == 0

    def test_get_analyst_recommendations_returns_empty(self, provider_no_keys):
        """No finnhub key → returns empty list."""
        result = provider_no_keys.get_analyst_recommendations("AAPL")
        assert isinstance(result, list)
        assert result == []


# ── Neutral sentiment helper ───────────────────────────────────────────────────

class TestNeutralSentiment:
    def test_neutral_sentiment_structure(self, provider):
        result = provider._neutral_sentiment()
        assert result == {
            "avg_sentiment": 0.0,
            "label": "Neutral",
            "article_count": 0,
            "confidence": 0.0,
        }


# ── Finnhub news fetching ──────────────────────────────────────────────────────

class TestFinnhubNews:
    @patch("requests.get")
    def test_returns_normalized_list(self, mock_get, provider):
        """Finnhub response is normalized to our schema."""
        import time
        ts = int(time.time())
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "headline": "Test News",
                "summary": "Summary text",
                "url": "https://example.com",
                "datetime": ts,
                "source": "Reuters",
                "category": "company",
                "image": "",
            }
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_company_news("AAPL")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["headline"] == "Test News"
        assert result[0]["source"] == "Reuters"
        # datetime should be an ISO string, not an int
        assert isinstance(result[0]["datetime"], str)

    @patch("requests.get")
    def test_finnhub_non_list_returns_empty(self, mock_get, provider):
        """Unexpected response type (not a list) → empty list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "symbol not found"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider._fetch_finnhub_news("AAPL", days=7)
        assert result == []

    @patch("requests.get")
    def test_finnhub_network_error_returns_empty(self, mock_get, provider):
        """Network error on news fetch → empty list, no crash."""
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.ConnectionError

        result = provider.get_company_news("AAPL")
        assert result == []


# ── Alpha Vantage sentiment ───────────────────────────────────────────────────

class TestAlphaVantagesentiment:
    @patch("requests.get")
    def test_bullish_label(self, mock_get, provider):
        """avg score > 0.15 → Bullish."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "feed": [
                {
                    "ticker_sentiment": [
                        {"ticker": "AAPL", "ticker_sentiment_score": "0.5", "relevance_score": "0.9"}
                    ]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_sentiment("AAPL")
        assert result["label"] == "Bullish"
        assert result["avg_sentiment"] > 0.15

    @patch("requests.get")
    def test_bearish_label(self, mock_get, provider):
        """avg score < -0.15 → Bearish."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "feed": [
                {
                    "ticker_sentiment": [
                        {"ticker": "AAPL", "ticker_sentiment_score": "-0.5", "relevance_score": "0.8"}
                    ]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_sentiment("AAPL")
        assert result["label"] == "Bearish"
        assert result["avg_sentiment"] < -0.15

    @patch("requests.get")
    def test_neutral_label_on_small_score(self, mock_get, provider):
        """avg score between -0.15 and 0.15 → Neutral."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "feed": [
                {
                    "ticker_sentiment": [
                        {"ticker": "AAPL", "ticker_sentiment_score": "0.05", "relevance_score": "0.5"}
                    ]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_sentiment("AAPL")
        assert result["label"] == "Neutral"

    @patch("requests.get")
    def test_case_insensitive_ticker_match(self, mock_get, provider):
        """Ticker matching is case-insensitive."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "feed": [
                {
                    "ticker_sentiment": [
                        {"ticker": "aapl", "ticker_sentiment_score": "0.4", "relevance_score": "0.9"}
                    ]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_sentiment("AAPL")
        assert result["label"] == "Bullish"

    @patch("requests.get")
    def test_empty_feed_returns_neutral(self, mock_get, provider):
        """Empty feed → neutral sentiment."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"feed": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_sentiment("AAPL")
        assert result["label"] == "Neutral"
        assert result["article_count"] == 0

    @patch("requests.get")
    def test_rate_limit_note_returns_neutral(self, mock_get, provider):
        """AV rate limit 'Note' in response → graceful neutral."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"Note": "Thank you for using Alpha Vantage! ..."}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_sentiment("AAPL")
        assert result["label"] == "Neutral"


# ── Analyst recommendations ───────────────────────────────────────────────────

class TestAnalystRecommendations:
    @patch("requests.get")
    def test_returns_formatted_list(self, mock_get, provider):
        """Finnhub recs are normalized to snake_case keys."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"period": "2024-01", "strongBuy": 5, "buy": 10, "hold": 3, "sell": 1, "strongSell": 0}
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_analyst_recommendations("AAPL")
        assert isinstance(result, list)
        assert result[0]["strong_buy"] == 5
        assert result[0]["buy"] == 10
        assert result[0]["period"] == "2024-01"

    @patch("requests.get")
    def test_max_6_months_returned(self, mock_get, provider):
        """Only last 6 months are returned even if more data is available."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"period": f"2024-0{i}", "strongBuy": i, "buy": 0, "hold": 0, "sell": 0, "strongSell": 0}
            for i in range(1, 10)  # 9 periods
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_analyst_recommendations("AAPL")
        assert len(result) <= 6
