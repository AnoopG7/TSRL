from dataclasses import dataclass
from enum import Enum


class Timeframe(str, Enum):
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1mo"

    @property
    def minutes(self) -> int:
        mapping = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
            "1mo": 43200,
        }
        return mapping.get(self.value, 0)

    @property
    def pandas_freq(self) -> str:
        return self.value

    @classmethod
    def from_minutes(cls, minutes: int) -> "Timeframe":
        mapping = {
            1: cls.MINUTE_1,
            5: cls.MINUTE_5,
            15: cls.MINUTE_15,
            30: cls.MINUTE_30,
            60: cls.HOUR_1,
            240: cls.HOUR_4,
            1440: cls.DAILY,
            10080: cls.WEEKLY,
            43200: cls.MONTHLY,
        }
        return mapping.get(minutes, cls.DAILY)


@dataclass(frozen=True)
class Symbol:
    ticker: str
    name: str = ""
    exchange: str = ""
    currency: str = "USD"

    def __post_init__(self):
        if not self.ticker:
            raise ValueError("Ticker cannot be empty")

    def __str__(self) -> str:
        if self.exchange:
            return f"{self.ticker}.{self.exchange}"
        return self.ticker

    @property
    def full_ticker(self) -> str:
        return str(self)

    @property
    def yahoo_ticker(self) -> str:
        if self.exchange == "NS":
            return f"{self.ticker}.NS"
        if self.exchange == "BO":
            return f"{self.ticker}.BO"
        return self.ticker
