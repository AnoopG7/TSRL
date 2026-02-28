import pandas as pd
import numpy as np
from typing import Dict, Any

from src.strategies.base import BaseStrategy, StrategyParameter
from src.strategies.registry import register_strategy


@register_strategy("macd")
class MACDStrategy(BaseStrategy):
    def __init__(
        self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **kwargs
    ):
        self._fast_period = fast_period
        self._slow_period = slow_period
        self._signal_period = signal_period
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "macd"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "MACD (Moving Average Convergence Divergence) crossover strategy"

    @property
    def strategy_type(self) -> str:
        return "momentum"

    def _set_default_parameters(self) -> None:
        self._params = {
            "fast_period": StrategyParameter(
                name="fast_period",
                value=12,
                min_value=5,
                max_value=50,
                step=1,
                description="Fast EMA period",
            ),
            "slow_period": StrategyParameter(
                name="slow_period",
                value=26,
                min_value=10,
                max_value=100,
                step=1,
                description="Slow EMA period",
            ),
            "signal_period": StrategyParameter(
                name="signal_period",
                value=9,
                min_value=5,
                max_value=30,
                step=1,
                description="Signal line period",
            ),
        }

    def _validate_parameters(self) -> bool:
        if self._params["fast_period"].value >= self._params["slow_period"].value:
            raise ValueError("fast_period must be less than slow_period")
        return True

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]

        ema_fast = close.ewm(span=self._params["fast_period"].value, adjust=False).mean()
        ema_slow = close.ewm(span=self._params["slow_period"].value, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self._params["signal_period"].value, adjust=False).mean()
        histogram = macd_line - signal_line

        signals = pd.DataFrame(index=data.index)
        signals["close"] = data["close"]
        signals["macd"] = macd_line
        signals["signal_line"] = signal_line
        signals["histogram"] = histogram

        crossover = (histogram > 0) & (histogram.shift(1) < 0)
        crossunder = (histogram < 0) & (histogram.shift(1) > 0)

        signals["signal"] = 0
        signals.loc[crossover, "signal"] = 1
        signals.loc[crossunder, "signal"] = -1

        return signals

    def get_requirements(self) -> list[str]:
        return ["close"]
