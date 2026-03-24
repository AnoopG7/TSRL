"""Rebalancing event entity for portfolio backtesting."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RebalanceEvent:
    """Tracks a single portfolio rebalancing event."""

    timestamp: datetime
    reason: str  # "periodic" or "threshold"

    # Pre-rebalance state
    pre_weights: dict[str, float] = field(default_factory=dict)
    pre_values: dict[str, float] = field(default_factory=dict)

    # Post-rebalance state
    target_weights: dict[str, float] = field(default_factory=dict)
    post_values: dict[str, float] = field(default_factory=dict)

    # Trades executed for rebalancing
    trades_executed: int = 0
    total_cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": (
                self.timestamp.isoformat()
                if hasattr(self.timestamp, "isoformat")
                else str(self.timestamp)
            ),
            "reason": self.reason,
            "pre_weights": self.pre_weights,
            "pre_values": self.pre_values,
            "target_weights": self.target_weights,
            "post_values": self.post_values,
            "trades_executed": self.trades_executed,
            "total_cost": self.total_cost,
        }

    @property
    def drift(self) -> dict[str, float]:
        """Calculate weight drift for each asset."""
        return {
            symbol: abs(self.pre_weights.get(symbol, 0) - self.target_weights.get(symbol, 0))
            for symbol in set(self.pre_weights) | set(self.target_weights)
        }

    @property
    def max_drift(self) -> float:
        """Maximum weight drift across all assets."""
        drifts = self.drift.values()
        return max(drifts) if drifts else 0.0
