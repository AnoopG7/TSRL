"""News and sentiment data provider — Finnhub (free) + Alpha Vantage (free).

Finnhub: Company news, analyst recommendations (free: 60 calls/min)
Alpha Vantage: News sentiment scoring (free: 500 calls/day)
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class NewsProviderError(Exception):
    """Raised when news/sentiment fetch fails."""

    pass


class NewsProvider:
    """Fetches company news from Finnhub and sentiment from Alpha Vantage.

    Both are free APIs:
    - Finnhub free tier: 60 calls/min, real-time company news
      Sign up: https://finnhub.io/register
    - Alpha Vantage: 500 calls/day, AI-powered sentiment scoring
      Key already configured in config/.env
    """

    def __init__(
        self,
        finnhub_key: Optional[str] = None,
        av_key: Optional[str] = None,
    ):
        self.finnhub_key = finnhub_key or os.environ.get("FINNHUB_API_KEY")
        self.av_key = av_key or os.environ.get("ALPHA_VANTAGE_API_KEY")

    def get_company_news(self, symbol: str, days: int = 7) -> list[dict]:
        """Fetch recent news articles for a stock.

        Tries Finnhub first, falls back to Alpha Vantage news sentiment.
        Returns up to 20 articles sorted by most recent first.
        Each article: {headline, summary, url, datetime, source, category, image}
        """
        # Try Finnhub first
        if self.finnhub_key:
            news = self._fetch_finnhub_news(symbol, days)
            if news:
                return news

        # Fallback to Alpha Vantage
        if self.av_key:
            return self._fetch_av_news(symbol, days)

        logger.warning(
            "No API key available for news (need FINNHUB_API_KEY or ALPHA_VANTAGE_API_KEY)"
        )
        return []

    def _fetch_av_news(self, symbol: str, days: int) -> list[dict]:
        """Fetch news from Alpha Vantage (News Sentiment endpoint has articles)."""
        try:
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=NEWS_SENTIMENT&tickers={symbol.upper()}"
                f"&apikey={self.av_key}&limit=20"
            )
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

            if "Note" in data or "Information" in data:
                logger.warning(
                    f"Alpha Vantage rate limit or info: {data.get('Note') or data.get('Information')}"
                )
                return []

            articles = []
            for article in data.get("feed", [])[:20]:
                articles.append(
                    {
                        "headline": article.get("title", ""),
                        "summary": article.get("summary", ""),
                        "url": article.get("url", ""),
                        "datetime": article.get("time_published", "")[:8],
                        "source": article.get("source", ""),
                        "category": article.get("topics", [{}])[0].get("topic", "")
                        if article.get("topics")
                        else "",
                        "image": article.get("banner_image", ""),
                    }
                )

            return articles
        except Exception as e:
            logger.warning(f"Failed to fetch Alpha Vantage news for {symbol}: {e}")
            return []

    def _fetch_finnhub_news(self, symbol: str, days: int) -> list[dict]:
        """Fetch news from Finnhub."""
        try:
            end = datetime.today().strftime("%Y-%m-%d")
            start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")

            url = (
                f"https://finnhub.io/api/v1/company-news"
                f"?symbol={symbol.upper()}&from={start}&to={end}"
                f"&token={self.finnhub_key}"
            )
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            articles = response.json()

            if not isinstance(articles, list):
                logger.warning(f"Unexpected Finnhub response: {type(articles)}")
                return []

            # Normalize and sort by datetime (most recent first)
            normalized = []
            for article in sorted(articles, key=lambda x: x.get("datetime", 0), reverse=True)[:20]:
                ts = article.get("datetime", 0)
                normalized.append(
                    {
                        "headline": article.get("headline", ""),
                        "summary": article.get("summary", ""),
                        "url": article.get("url", ""),
                        "datetime": datetime.fromtimestamp(ts).isoformat() if ts else "",
                        "source": article.get("source", ""),
                        "category": article.get("category", ""),
                        "image": article.get("image", ""),
                    }
                )
            return normalized

        except Exception as e:
            logger.warning(f"Failed to fetch news for {symbol}: {e}")
            return []

    def get_sentiment(self, symbol: str) -> dict:
        """Get aggregated news sentiment from Alpha Vantage.

        Returns:
            {
                avg_sentiment: float (-1.0 to 1.0),
                label: "Bullish" | "Bearish" | "Neutral",
                article_count: int,
                confidence: float (0-1),
            }
        """
        if not self.av_key:
            logger.warning("ALPHA_VANTAGE_API_KEY not set — skipping sentiment fetch")
            return self._neutral_sentiment()

        try:
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=NEWS_SENTIMENT&tickers={symbol.upper()}"
                f"&apikey={self.av_key}&limit=20"
            )
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit hit: {data['Note']}")
                return self._neutral_sentiment()

            scores = []
            relevance_scores = []
            for article in data.get("feed", []):
                for ts in article.get("ticker_sentiment", []):
                    if ts.get("ticker", "").upper() == symbol.upper():
                        score = float(ts.get("ticker_sentiment_score", 0))
                        relevance = float(ts.get("relevance_score", 0))
                        scores.append(score)
                        relevance_scores.append(relevance)

            if not scores:
                return self._neutral_sentiment()

            avg_score = sum(scores) / len(scores)
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

            if avg_score > 0.15:
                label = "Bullish"
            elif avg_score < -0.15:
                label = "Bearish"
            else:
                label = "Neutral"

            return {
                "avg_sentiment": round(avg_score, 4),
                "label": label,
                "article_count": len(scores),
                "confidence": round(avg_relevance, 3),
            }

        except Exception as e:
            logger.warning(f"Failed to fetch sentiment for {symbol}: {e}")
            return self._neutral_sentiment()

    def get_analyst_recommendations(self, symbol: str) -> list[dict]:
        """Fetch analyst recommendation trends from Finnhub.

        Returns monthly aggregated buy/hold/sell counts.
        """
        if not self.finnhub_key:
            return []

        try:
            url = (
                f"https://finnhub.io/api/v1/stock/recommendation"
                f"?symbol={symbol.upper()}&token={self.finnhub_key}"
            )
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                return []

            # Return last 6 months of recommendations
            return [
                {
                    "period": rec.get("period", ""),
                    "strong_buy": rec.get("strongBuy", 0),
                    "buy": rec.get("buy", 0),
                    "hold": rec.get("hold", 0),
                    "sell": rec.get("sell", 0),
                    "strong_sell": rec.get("strongSell", 0),
                }
                for rec in data[:6]
            ]

        except Exception as e:
            logger.warning(f"Failed to fetch analyst recs for {symbol}: {e}")
            return []

    def _neutral_sentiment(self) -> dict:
        """Default neutral sentiment when data is unavailable."""
        return {
            "avg_sentiment": 0.0,
            "label": "Neutral",
            "article_count": 0,
            "confidence": 0.0,
        }
