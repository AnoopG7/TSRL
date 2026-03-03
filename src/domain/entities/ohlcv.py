from dataclasses import dataclass
from datetime import datetime
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

    def __post_init__(self):
        if self.high < self.low:
            raise ValueError("High price cannot be less than low price")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

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
        timestamp = row.name
        if not isinstance(timestamp, (datetime, pd.Timestamp)):
            timestamp = pd.to_datetime(timestamp)
        return cls(
            symbol=symbol,
            timestamp=timestamp,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )

