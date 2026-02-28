import hashlib
import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataCache:
    def __init__(self, cache_dir: str = "data/cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self._memory_cache: dict[str, tuple[Any, datetime]] = {}

    def _make_key(
        self,
        provider: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str,
    ) -> str:
        data = {
            "provider": provider,
            "symbol": symbol.upper(),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "timeframe": timeframe,
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def get(
        self,
        provider: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> Optional[pd.DataFrame]:
        key = self._make_key(provider, symbol, start_date, end_date, timeframe)

        if key in self._memory_cache:
            data, cached_at = self._memory_cache[key]
            if datetime.now() - cached_at < self.ttl:
                logger.debug(f"Cache hit (memory): {provider}:{symbol}")
                return pickle.loads(data)
            else:
                del self._memory_cache[key]

        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime < self.ttl:
                try:
                    with open(cache_file, "rb") as f:
                        data = pickle.load(f)
                    self._memory_cache[key] = (pickle.dumps(data), datetime.now())
                    logger.debug(f"Cache hit (disk): {provider}:{symbol}")
                    return data
                except Exception as e:
                    logger.warning(f"Failed to load cache: {e}")

        return None

    def set(
        self,
        provider: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        dataframe: pd.DataFrame,
        timeframe: str = "1d",
    ) -> None:
        key = self._make_key(provider, symbol, start_date, end_date, timeframe)

        try:
            with open(self.cache_dir / f"{key}.pkl", "wb") as f:
                pickle.dump(dataframe, f)
            self._memory_cache[key] = (pickle.dumps(dataframe), datetime.now())
            logger.debug(f"Cached: {provider}:{symbol}")
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")

    def invalidate(
        self,
        provider: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> None:
        key = self._make_key(provider, symbol, start_date, end_date, timeframe)
        self._memory_cache.pop(key, None)
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            cache_file.unlink()
        logger.debug(f"Invalidated cache: {provider}:{symbol}")

    def clear(self) -> None:
        self._memory_cache.clear()
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
        logger.info("Cache cleared")


_data_cache: Optional[DataCache] = None


def get_cache() -> DataCache:
    global _data_cache
    if _data_cache is None:
        _data_cache = DataCache()
    return _data_cache
