"""NSE (National Stock Exchange of India) data provider.

Note: nsetools library has known issues. This provider uses multiple fallbacks:
1. Primary: nsetools (unstable, may fail)
2. Fallback: Yahoo Finance with .NS suffix
"""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd
import requests

from src.infrastructure.data_providers.base import BaseDataProvider, DataProviderError

logger = logging.getLogger(__name__)


class NSEProvider(BaseDataProvider):
    """NSE data provider - uses nsetools with Yahoo fallback."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        super().__init__(max_retries, retry_delay)
        self._nse = None

    @property
    def nse(self):
        """Lazy load nsetools."""
        if self._nse is None:
            try:
                from nsetools import Nse

                self._nse = Nse()
            except ImportError:
                raise DataProviderError("nsetools package not installed")
        return self._nse

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        """Fetch OHLCV data for an Indian stock.

        This method attempts to use nsetools first, but since it's unstable,
        it raises an error to trigger Yahoo Finance fallback.
        """
        if timeframe != "1d":
            raise DataProviderError(f"NSE provider only supports daily timeframe, got {timeframe}")

        # Clean the symbol
        nse_symbol = (
            symbol.upper()
            .replace(".NS", "")
            .replace(".BO", "")
            .replace("NSE:", "")
            .replace("BSE:", "")
            .replace("-", "")
        )

        # Try nsetools - it's known to be broken, so we raise to trigger fallback
        try:
            from nsetools import Nse

            nse = Nse()
            quotes = nse.get_historical_quotes(
                nse_symbol, start_date.strftime("%d-%m-%Y"), end_date.strftime("%d-%m-%Y")
            )

            if quotes and len(quotes) > 0:
                df = pd.DataFrame(quotes)
                df = df.rename(
                    columns={
                        "CH_SYMBOL": "symbol",
                        "CH_TIMESTAMP": "timestamp",
                        "CH_OPEN": "open",
                        "CH_HIGH": "high",
                        "CH_LOW": "low",
                        "CH_CLOSE": "close",
                        "CH_NUMBEROFTRADES": "number_of_trades",
                        "CH_TOTLENQUANTITY": "volume",
                        "CH_TOTLENVAL": " turnover",
                    }
                )
                df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d-%b-%Y")
                df = df.set_index("timestamp").sort_index()
                df["close"] = df["close"].astype(float)
                df["open"] = df["open"].astype(float)
                df["high"] = df["high"].astype(float)
                df["low"] = df["low"].astype(float)
                df["volume"] = df["volume"].astype(float)
                df = df[["open", "high", "low", "close", "volume"]]
                df["symbol"] = nse_symbol
                return df
        except Exception as e:
            logger.warning(f"nsetools failed for {symbol}: {e}")
            # Raise to trigger Yahoo fallback
            raise DataProviderError(f"NSE provider unavailable for {symbol}: {e}")

        # If we get here, no data - raise to trigger fallback
        raise DataProviderError(f"No data from NSE for symbol: {symbol}")

    def get_quote(self, symbol: str) -> dict:
        """Get real-time quote from NSE."""
        nse_symbol = symbol.upper().replace(".NS", "").replace(".BO", "")

        try:
            quote = self.nse.get_quote(nse_symbol)
            return {
                "symbol": nse_symbol,
                "price": quote.get("lastPrice"),
                "open": quote.get("open"),
                "high": quote.get("dayHigh"),
                "low": quote.get("dayLow"),
                "volume": quote.get("totalTradedVolume"),
                "turnover": quote.get("totalTurnover"),
            }
        except Exception as e:
            raise DataProviderError(f"Failed to get quote for {symbol}: {e}")

    def get_index_quote(self, index_symbol: str = "NIFTY 50") -> dict:
        """Get NSE index quote (e.g., NIFTY 50, SENSEX)."""
        try:
            index = self.nse.get_index(index_symbol)
            return {
                "symbol": index_symbol,
                "value": index.get("currentValue"),
                "change": index.get("change"),
                "change_pct": index.get("percentChange"),
            }
        except Exception as e:
            raise DataProviderError(f"Failed to get index {index_symbol}: {e}")

    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol info - not supported via nsetools."""
        raise DataProviderError("NSE get_symbol_info not implemented - use Yahoo")

    def get_recent_price(self, symbol: str) -> Optional[float]:
        """Get recent price - not supported via nsetools."""
        return None
