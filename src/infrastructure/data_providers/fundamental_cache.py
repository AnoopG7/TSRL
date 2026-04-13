"""JSON-based cache for fundamental analysis data.

Fundamental data is expensive to fetch (multiple API calls per stock)
but changes infrequently — perfect for aggressive caching.

TTL strategy:
    - Company info + ratios: 1 hour (updated intraday)
    - Financial statements: 24 hours (updated quarterly)
    - News articles: 30 minutes (time-sensitive)
    - Sentiment scores: 1 hour
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FundamentalCache:
    """File-backed JSON cache with configurable TTL per data type."""

    # TTL by data category
    DEFAULT_TTLS = {
        "full_report": timedelta(hours=1),
        "profile": timedelta(hours=1),
        "financials": timedelta(hours=24),
        "news": timedelta(minutes=30),
        "sentiment": timedelta(hours=1),
        "analyst": timedelta(hours=6),
    }

    def __init__(self, cache_dir: str = "data/cache/fundamentals"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory: dict[str, tuple[Any, datetime]] = {}

    def _make_key(self, symbol: str, data_type: str, source: str = "") -> str:
        """Create a deterministic cache key."""
        raw = f"{symbol.upper()}:{data_type}:{source}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(
        self,
        symbol: str,
        data_type: str = "full_report",
        source: str = "",
    ) -> Optional[dict]:
        """Retrieve cached data if within TTL.

        Args:
            symbol: Stock ticker (e.g. "AAPL")
            data_type: One of "full_report", "profile", "financials", "news", "sentiment"
            source: Provider name (e.g. "yfinance", "fmp")

        Returns:
            Cached dict or None if expired/missing.
        """
        key = self._make_key(symbol, data_type, source)
        ttl = self.DEFAULT_TTLS.get(data_type, timedelta(hours=1))

        # Check memory cache first
        if key in self._memory:
            data, cached_at = self._memory[key]
            if datetime.now() - cached_at < ttl:
                logger.debug(f"Cache hit (memory): {symbol}:{data_type}")
                return data
            else:
                del self._memory[key]

        # Check disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime < ttl:
                try:
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                    self._memory[key] = (data, datetime.now())
                    logger.debug(f"Cache hit (disk): {symbol}:{data_type}")
                    return data
                except Exception as e:
                    logger.warning(f"Failed to read cache file: {e}")

        return None

    def set(
        self,
        symbol: str,
        data: dict,
        data_type: str = "full_report",
        source: str = "",
    ) -> None:
        """Store data in both memory and disk cache.

        Args:
            symbol: Stock ticker
            data: The data dict to cache (must be JSON-serializable)
            data_type: Category key for TTL lookup
            source: Provider name
        """
        key = self._make_key(symbol, data_type, source)

        try:
            cache_file = self.cache_dir / f"{key}.json"
            with open(cache_file, "w") as f:
                json.dump(data, f, default=str)
            self._memory[key] = (data, datetime.now())
            logger.debug(f"Cached: {symbol}:{data_type}")
        except Exception as e:
            logger.warning(f"Failed to cache {symbol}:{data_type}: {e}")

    def invalidate(self, symbol: str, data_type: str = "full_report", source: str = "") -> None:
        """Remove a specific cache entry."""
        key = self._make_key(symbol, data_type, source)
        self._memory.pop(key, None)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            cache_file.unlink()
        logger.debug(f"Invalidated: {symbol}:{data_type}")

    def clear(self) -> None:
        """Clear all fundamental caches."""
        self._memory.clear()
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
        logger.info("Fundamental cache cleared")


# Module-level singleton
_fundamental_cache: Optional[FundamentalCache] = None


def get_fundamental_cache() -> FundamentalCache:
    global _fundamental_cache
    if _fundamental_cache is None:
        _fundamental_cache = FundamentalCache()
    return _fundamental_cache
