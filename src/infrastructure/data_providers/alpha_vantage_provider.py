import logging
import os
import time
from datetime import datetime
from typing import Optional

import pandas as pd
import requests

from src.infrastructure.data_providers.base import BaseDataProvider, DataProviderError
from src.infrastructure.data_providers.cache import get_cache

logger = logging.getLogger(__name__)

TIMEFRAME_MAP = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "60min",
    "1d": "daily",
    "1w": "weekly",
    "1M": "monthly",
}


class AlphaVantageProvider(BaseDataProvider):
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        use_cache: bool = True,
    ):
        super().__init__(max_retries, retry_delay)
        self.api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
        self.use_cache = use_cache
        self.cache = get_cache() if use_cache else None

        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key is required. Set ALPHA_VANTAGE_API_KEY in config/.env"
            )

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        if self.use_cache and self.cache:
            cached = self.cache.get("alpha_vantage", symbol, start_date, end_date, timeframe)
            if cached is not None:
                return cached

        av_timeframe = TIMEFRAME_MAP.get(timeframe, "daily")
        function = "TIME_SERIES_DAILY" if av_timeframe == "daily" else "TIME_SERIES_INTRADAY"

        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    wait_time = self.retry_delay * (2**attempt)
                    logger.info(f"Retry {attempt + 1}/{self.max_retries} after {wait_time:.1f}s")
                    time.sleep(wait_time)

                params = {
                    "function": function,
                    "symbol": symbol.upper(),
                    "outputsize": "full" if (end_date - start_date).days > 100 else "compact",
                    "apikey": self.api_key,
                }

                if av_timeframe != "daily":
                    params["interval"] = av_timeframe

                response = requests.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if "Error Message" in data:
                    raise DataProviderError(f"Alpha Vantage error: {data['Error Message']}")
                if "Note" in data:
                    raise DataProviderError(f"Alpha Vantage rate limit: {data['Note']}")

                time_series_key = self._get_time_series_key(data, av_timeframe)
                if not time_series_key:
                    raise DataProviderError(f"No time series data for {symbol}")

                records = []
                for date_str, values in data[time_series_key].items():
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if start_date <= date <= end_date:
                        records.append(
                            {
                                "timestamp": date,
                                "open": float(values["1. open"]),
                                "high": float(values["2. high"]),
                                "low": float(values["3. low"]),
                                "close": float(values["4. close"]),
                                "volume": int(values["5. volume"]),
                            }
                        )

                if not records:
                    raise DataProviderError(f"No data returned for {symbol}")

                df = pd.DataFrame(records)
                df = df.set_index("timestamp").sort_index()
                df = self.validate_ohlcv(df)
                df["symbol"] = symbol.upper()

                if self.use_cache and self.cache:
                    self.cache.set("alpha_vantage", symbol, start_date, end_date, df, timeframe)

                logger.info(f"Fetched {len(df)} rows from Alpha Vantage for {symbol}")
                return df

            except DataProviderError:
                raise
            except Exception as e:
                logger.warning(f"Error fetching {symbol}: {type(e).__name__}: {e}")
                if attempt == self.max_retries - 1:
                    raise DataProviderError(f"Failed to fetch data for {symbol}: {str(e)}")

        raise DataProviderError(
            f"Failed to fetch data for {symbol} after {self.max_retries} attempts"
        )

    def _get_time_series_key(self, data: dict, timeframe: str) -> Optional[str]:
        prefixes = {
            "daily": "Time Series (Daily)",
            "1min": "Time Series (1min)",
            "5min": "Time Series (5min)",
            "15min": "Time Series (15min)",
            "30min": "Time Series (30min)",
            "60min": "Time Series (60min)",
            "weekly": "Weekly Time Series",
            "monthly": "Monthly Time Series",
        }
        return prefixes.get(timeframe)

    def get_symbol_info(self, symbol: str) -> dict:
        try:
            params = {
                "function": "OVERVIEW",
                "symbol": symbol.upper(),
                "apikey": self.api_key,
            }

            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data or "Symbol" not in data:
                raise DataProviderError(f"No info available for {symbol}")

            return {
                "symbol": data.get("Symbol", symbol.upper()),
                "name": data.get("Name", ""),
                "exchange": data.get("Exchange", ""),
                "currency": data.get("Currency", "USD"),
                "sector": data.get("Sector", ""),
                "industry": data.get("Industry", ""),
                "market_cap": data.get("MarketCapitalization"),
                "price": None,
                "volume": None,
            }
        except DataProviderError:
            raise
        except Exception as e:
            raise DataProviderError(f"Failed to get symbol info for {symbol}: {str(e)}")

    def get_recent_price(self, symbol: str) -> Optional[float]:
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol.upper(),
                "apikey": self.api_key,
            }

            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "Global Quote" in data and "05. price" in data["Global Quote"]:
                return float(data["Global Quote"]["05. price"])
            return None
        except Exception as e:
            logger.warning(f"Failed to get recent price for {symbol}: {e}")
            return None
