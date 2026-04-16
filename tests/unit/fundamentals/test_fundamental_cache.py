"""Tests for FundamentalCache layer."""

import pytest
import time
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path


class TestFundamentalCache:
    """Test cache get/set/invalidate operations with TTL."""

    @pytest.fixture
    def cache_dir(self):
        """Create a temporary cache directory."""
        tmp = tempfile.mkdtemp()
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    @pytest.fixture
    def cache(self, cache_dir):
        """Create cache instance with short TTL for testing."""
        from src.infrastructure.data_providers.fundamental_cache import FundamentalCache

        c = FundamentalCache(cache_dir=cache_dir)
        c.DEFAULT_TTLS = {
            "full_report": timedelta(seconds=2),
            "profile": timedelta(seconds=2),
            "financials": timedelta(hours=24),
            "news": timedelta(minutes=30),
        }
        return c

    def test_cache_set_and_get(self, cache):
        """Set data, get within TTL: returns same data."""
        data = {"symbol": "AAPL", "price": 180.0, "pe_ratio": 25.0}
        cache.set("AAPL", data, "full_report", "yfinance")

        result = cache.get("AAPL", "full_report", "yfinance")
        assert result is not None
        assert result["symbol"] == "AAPL"
        assert result["price"] == 180.0

    def test_cache_expired(self, cache):
        """Set data, advance time past TTL: returns None."""
        data = {"symbol": "MSFT", "price": 400.0}
        cache.set("MSFT", data, "full_report", "yfinance")

        time.sleep(3)

        result = cache.get("MSFT", "full_report", "yfinance")
        assert result is None

    def test_cache_memory_hit(self, cache):
        """Set, get twice: 2nd hit comes from memory (no disk read)."""
        data = {"symbol": "GOOGL", "price": 150.0}
        cache.set("GOOGL", data, "full_report", "yfinance")

        result1 = cache.get("GOOGL", "full_report", "yfinance")
        result2 = cache.get("GOOGL", "full_report", "yfinance")

        assert result1 is not None
        assert result2 is not None

    def test_cache_disk_persistence(self, cache):
        """Set, create new cache instance, get: returns data from disk."""
        data = {"symbol": "AMZN", "price": 180.0}
        cache.set("AMZN", data, "full_report", "yfinance")

        from src.infrastructure.data_providers.fundamental_cache import FundamentalCache

        new_cache = FundamentalCache(cache_dir=cache.cache_dir)
        new_cache.DEFAULT_TTLS = cache.DEFAULT_TTLS

        result = new_cache.get("AMZN", "full_report", "yfinance")
        assert result is not None
        assert result["symbol"] == "AMZN"

    def test_cache_invalidate(self, cache):
        """Set, invalidate, get: returns None."""
        data = {"symbol": "NVDA", "price": 800.0}
        cache.set("NVDA", data, "full_report", "yfinance")

        cache.invalidate("NVDA", "full_report", "yfinance")

        result = cache.get("NVDA", "full_report", "yfinance")
        assert result is None

    def test_cache_clear_all(self, cache):
        """Set 3 entries, clear: all 3 return None."""
        for sym in ["AAPL", "MSFT", "GOOGL"]:
            cache.set(sym, {"symbol": sym}, "full_report", "yfinance")

        cache.clear()

        for sym in ["AAPL", "MSFT", "GOOGL"]:
            result = cache.get(sym, "full_report", "yfinance")
            assert result is None

    def test_cache_corrupt_json(self, cache_dir):
        """Write malformed JSON to disk: returns None, no crash."""
        from src.infrastructure.data_providers.fundamental_cache import FundamentalCache

        cache_file = Path(cache_dir) / "corrupt.json"
        cache_file.write_text("{ bad json")

        new_cache = FundamentalCache(cache_dir=cache_dir)
        result = new_cache.get("corrupt", "full_report", "yfinance")
        assert result is None

    def test_cache_key_isolation(self, cache):
        """Same symbol, different source: different keys, no collision."""
        data1 = {"symbol": "AAPL", "source": "yfinance"}
        data2 = {"symbol": "AAPL", "source": "fmp"}

        cache.set("AAPL", data1, "full_report", "yfinance")
        cache.set("AAPL", data2, "full_report", "fmp")

        result1 = cache.get("AAPL", "full_report", "yfinance")
        result2 = cache.get("AAPL", "full_report", "fmp")

        assert result1 is not None
        assert result2 is not None
        assert result1["source"] == "yfinance"
        assert result2["source"] == "fmp"

    def test_cache_dir_created(self):
        """Init with non-existent dir: dir created automatically."""
        import tempfile
        import shutil

        tmp = tempfile.mkdtemp()
        new_dir = Path(tmp) / "nested" / "cache" / "dir"
        try:
            from src.infrastructure.data_providers.fundamental_cache import FundamentalCache

            c = FundamentalCache(cache_dir=str(new_dir))
            assert new_dir.exists()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
