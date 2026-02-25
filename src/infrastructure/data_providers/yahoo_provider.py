import time
from datetime import datetime
from typing import Optional

import pandas as pd
import yfinance as yf

from src.infrastructure.data_providers.base import BaseDataProvider, DataProviderError


class YahooFinanceProvider(BaseDataProvider):
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        super().__init__(max_retries, retry_delay)

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        for attempt in range(self.max_retries):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=timeframe,
                    auto_adjust=False,
                    repair=True,
                )

                if df.empty:
                    raise DataProviderError(f"No data returned for symbol: {symbol}")

                df = df.dropna()

                df = self.normalize_columns(df)
                df = self.handle_missing_values(df)
                df = self.remove_duplicates(df)
                df = self.validate_ohlcv(df)

                df["symbol"] = symbol

                return df

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise DataProviderError(f"Failed to fetch data for {symbol}: {str(e)}")

    def get_symbol_info(self, symbol: str) -> dict:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "name": info.get("shortName", info.get("longName", "")),
                "exchange": info.get("exchange", ""),
                "currency": info.get("currency", "USD"),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap"),
                "price": info.get("currentPrice"),
                "volume": info.get("volume"),
            }
        except Exception as e:
            raise DataProviderError(f"Failed to get symbol info for {symbol}: {str(e)}")

    def get_recent_price(self, symbol: str) -> Optional[float]:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", auto_adjust=False)
            if df.empty:
                return None
            return float(df["Close"].iloc[-1])
        except Exception:
            return None
