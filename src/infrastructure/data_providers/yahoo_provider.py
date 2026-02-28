import time
import logging
from datetime import datetime
from typing import Optional

import pandas as pd
import yfinance as yf

from src.infrastructure.data_providers.base import BaseDataProvider, DataProviderError

logger = logging.getLogger(__name__)


class YahooFinanceProvider(BaseDataProvider):
    def __init__(self, max_retries: int = 5, retry_delay: float = 2.0):
        super().__init__(max_retries, retry_delay)

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                wait_time = self.retry_delay * (2**attempt)

                if attempt > 0:
                    logger.info(
                        f"Retry {attempt + 1}/{self.max_retries} for {symbol} after {wait_time:.1f}s"
                    )
                    time.sleep(wait_time)

                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=timeframe,
                    auto_adjust=False,
                    repair=True,
                    timeout=30,
                )

                if df.empty:
                    raise DataProviderError(f"No data returned for symbol: {symbol}")

                df = self.normalize_columns(df)
                df = self.handle_missing_values(df)
                df = self.remove_duplicates(df)
                df = self.validate_ohlcv(df)

                df["symbol"] = symbol.upper()
                df = df.sort_index()

                logger.info(f"Successfully fetched {len(df)} rows for {symbol}")
                return df

            except DataProviderError:
                raise
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()

                if "429" in error_msg or "too many requests" in error_msg:
                    logger.warning(f"Rate limited for {symbol}, attempt {attempt + 1}")
                    continue
                elif "no timezone" in error_msg or "delisted" in error_msg:
                    raise DataProviderError(f"Symbol {symbol} may be delisted or invalid: {e}")
                else:
                    logger.warning(f"Error fetching {symbol}: {type(e).__name__}: {e}")
                    if attempt < self.max_retries - 1:
                        continue

        raise DataProviderError(
            f"Failed to fetch data for {symbol} after {self.max_retries} attempts: {last_exception}"
        )

    def get_symbol_info(self, symbol: str) -> dict:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                raise DataProviderError(f"No info available for symbol: {symbol}")

            return {
                "symbol": symbol.upper(),
                "name": info.get("shortName", info.get("longName", "")),
                "exchange": info.get("exchange", ""),
                "currency": info.get("currency", "USD"),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap"),
                "price": info.get("currentPrice"),
                "volume": info.get("volume"),
            }
        except DataProviderError:
            raise
        except Exception as e:
            raise DataProviderError(f"Failed to get symbol info for {symbol}: {str(e)}")

    def get_recent_price(self, symbol: str) -> Optional[float]:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", auto_adjust=False, timeout=10)
            if df.empty:
                return None
            return float(df["Close"].iloc[-1])
        except Exception as e:
            logger.warning(f"Failed to get recent price for {symbol}: {e}")
            return None
