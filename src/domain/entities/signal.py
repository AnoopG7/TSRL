from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    NEUTRAL = "NEUTRAL"


class SignalStrength(float, Enum):
    STRONG_BUY = 1.0
    BUY = 0.75
    SLIGHT_BUY = 0.5
    NEUTRAL = 0.0
    SLIGHT_SELL = -0.5
    SELL = -0.75
    STRONG_SELL = -1.0


@dataclass(frozen=True)
class Signal:
    symbol: str
    timestamp: datetime
    signal_type: SignalType
    strength: float
    price: float
    metadata: Optional[dict] = None

    def __post_init__(self):
        if not -1.0 <= self.strength <= 1.0:
            raise ValueError("Signal strength must be between -1.0 and 1.0")
        if self.price <= 0:
            raise ValueError("Signal price must be positive")

    @property
    def is_buy(self) -> bool:
        return self.signal_type in (SignalType.BUY, SignalType.CLOSE_SHORT)

    @property
    def is_sell(self) -> bool:
        return self.signal_type in (SignalType.SELL, SignalType.CLOSE_LONG)

    @property
    def is_entry(self) -> bool:
        return self.signal_type in (SignalType.BUY, SignalType.SELL)

    @property
    def is_exit(self) -> bool:
        return self.signal_type in (SignalType.CLOSE_LONG, SignalType.CLOSE_SHORT)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "signal_type": self.signal_type.value,
            "strength": self.strength,
            "price": self.price,
            "metadata": self.metadata,
        }

    @classmethod
    def create_buy(
        cls, symbol: str, timestamp: datetime, price: float, strength: float = 1.0, **metadata
    ) -> "Signal":
        return cls(
            symbol=symbol,
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            strength=strength,
            price=price,
            metadata=metadata,
        )

    @classmethod
    def create_sell(
        cls, symbol: str, timestamp: datetime, price: float, strength: float = 1.0, **metadata
    ) -> "Signal":
        return cls(
            symbol=symbol,
            timestamp=timestamp,
            signal_type=SignalType.SELL,
            strength=strength,
            price=price,
            metadata=metadata,
        )
