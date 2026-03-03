from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Position:
    symbol: str
    entry_time: datetime
    entry_price: float
    quantity: float
    side: PositionSide
    current_price: Optional[float] = None

    def __post_init__(self):
        if self.entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

    @property
    def market_value(self) -> float:
        if self.current_price is None:
            return self.entry_price * self.quantity
        return self.current_price * self.quantity

    @property
    def cost_basis(self) -> float:
        return self.entry_price * self.quantity

    @property
    def unrealized_pnl(self) -> Optional[float]:
        if self.current_price is None:
            return None
        if self.side == PositionSide.LONG:
            return (self.current_price - self.entry_price) * self.quantity
        return (self.entry_price - self.current_price) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> Optional[float]:
        if self.current_price is None:
            return None
        if self.side == PositionSide.LONG:
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        return ((self.entry_price - self.current_price) / self.entry_price) * 100

    @property
    def is_profitable(self) -> Optional[bool]:
        if self.unrealized_pnl is None:
            return None
        return self.unrealized_pnl > 0

    def update_price(self, price: float) -> None:
        self.current_price = price

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "entry_time": self.entry_time,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "side": self.side.value,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
        }
