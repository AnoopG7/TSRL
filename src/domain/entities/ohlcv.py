from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
import pandas as pd


@dataclass(frozen=True)
class OHLCV:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def is_bullish(self) -> bool:
        return self.close >= self.open

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OHLCV":
        return cls(
            symbol=data["symbol"],
            timestamp=pd.to_datetime(data["timestamp"]),
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            close=float(data["close"]),
            volume=float(data["volume"]),
        )

    @classmethod
    def from_pandas_row(cls, row: pd.Series, symbol: str) -> "OHLCV":
        return cls(
            symbol=symbol,
            timestamp=pd.to_datetime(row.name) if hasattr(row.name, "__iter__") else row.name,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )
