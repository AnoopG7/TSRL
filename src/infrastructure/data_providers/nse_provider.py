import time
from datetime import datetime
from typing import Optional

import pandas as pd

from src.infrastructure.data_providers.base import BaseDataProvider, DataProviderError


class NSEProvider(BaseDataProvider):
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        super().__init__(max_retries, retry_delay)
        self._nse = None

    @property
    def nse(self):
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
        if timeframe != "1d":
            raise DataProviderError(f"NSE provider only supports daily timeframe, got {timeframe}")

        for attempt in range(self.max_retries):
            try:
                from nsetools import Nse

                nse = Nse()

                nse_symbol = symbol.upper().replace(".NS", "").replace(".BO", "")

                df = nse.get_historical_quotes(
                    nse_symbol, start_date.strftime("%d-%m-%Y"), end_date.strftime("%d-%m-%Y")
                )

                if not df:
                    raise DataProviderError(f"No data returned for symbol: {symbol}")

                df = pd.DataFrame(df)

                df = df.rename(
                    columns={
                        "CH_SYMBOL": "symbol",
                        "CH_TIMESTAMP": "timestamp",
                        "CH_OPEN": "open",
                        "CH_HIGH": "high",
                        "CH_LOW": "low",
                        "CH_CLOSE": "close",
                        "CH_TOT_QTY": "volume",
                    }
                )

                df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d-%b-%Y")
                df = df.set_index("timestamp")
                df = df.sort_index()

                for col in ["open", "high", "low", "close"]:
                    df[col] = df[col].astype(float)
                df["volume"] = df["volume"].astype(float)

                df = df[["symbol", "open", "high", "low", "close", "volume"]]
                df["symbol"] = symbol

                df = self.handle_missing_values(df)
                df = self.remove_duplicates(df)
                df = self.validate_ohlcv(df)

                return df

            except ImportError:
                raise DataProviderError(
                    "nsetools package is required for NSE data. Install with: pip install nsetools"
                )
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise DataProviderError(f"Failed to fetch data for {symbol}: {str(e)}")

    def get_symbol_info(self, symbol: str) -> dict:
        try:
            from nsetools import Nse

            nse = Nse()

            nse_symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
            quote = nse.get_quote(nse_symbol)

            return {
                "symbol": nse_symbol,
                "name": quote.get("companyName", ""),
                "exchange": "NSE",
                "currency": "INR",
                "sector": quote.get("sector", ""),
                "industry": quote.get("industry", ""),
                "market_cap": quote.get("marketCapFull"),
                "price": quote.get("lastPrice"),
                "volume": quote.get("quantityTraded"),
                "high": quote.get("dayHigh"),
                "low": quote.get("dayLow"),
                "open": quote.get("open"),
                "previous_close": quote.get("previousClose"),
            }
        except ImportError:
            raise DataProviderError("nsetools package is required for NSE data")
        except Exception as e:
            raise DataProviderError(f"Failed to get symbol info for {symbol}: {str(e)}")

    def get_recent_price(self, symbol: str) -> Optional[float]:
        try:
            info = self.get_symbol_info(symbol)
            return info.get("price")
        except Exception:
            return None
