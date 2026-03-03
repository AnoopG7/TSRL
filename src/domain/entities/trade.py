from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TradeSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


@dataclass
class Trade:
    symbol: str
    entry_time: datetime
    entry_price: float
    quantity: float
    side: TradeSide
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    status: TradeStatus = TradeStatus.OPEN
    commission: float = 0.0
    slippage: float = 0.0

    def __post_init__(self):
        if self.entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

    @property
    def pnl(self) -> Optional[float]:
        if self.exit_price is None:
            return None
        if self.side == TradeSide.LONG:
            return (
                (self.exit_price - self.entry_price) * self.quantity
                - self.commission
                - self.slippage
            )
        return (
            (self.entry_price - self.exit_price) * self.quantity - self.commission - self.slippage
        )

    @property
    def pnl_pct(self) -> Optional[float]:
        if self.exit_price is None or self.pnl is None:
            return None
        if self.trade_value == 0:
            return 0.0
        return (self.pnl / self.trade_value) * 100

    @property
    def is_winning(self) -> Optional[bool]:
        if self.pnl is None:
            return None
        return self.pnl > 0

    @property
    def is_closed(self) -> bool:
        return self.status == TradeStatus.CLOSED

    @property
    def is_open(self) -> bool:
        return self.status == TradeStatus.OPEN

    @property
    def trade_value(self) -> float:
        return self.entry_price * self.quantity

    def close(self, exit_price: float, exit_time: datetime) -> None:
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.status = TradeStatus.CLOSED

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "entry_time": self.entry_time,
            "entry_price": self.entry_price,
            "exit_time": self.exit_time,
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "side": self.side.value,
            "status": self.status.value,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "commission": self.commission,
            "slippage": self.slippage,
        }
