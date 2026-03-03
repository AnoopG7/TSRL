import pandas as pd
import numpy as np
from typing import Dict, Any

from src.strategies.base import BaseStrategy, StrategyParameter
from src.strategies.registry import register_strategy


@register_strategy("ma_ribbon")
class MovingAverageRibbonStrategy(BaseStrategy):
    def __init__(
        self, fast_period: int = 5, medium_period: int = 20, slow_period: int = 50, **kwargs
    ):
        self._fast_period = fast_period
        self._medium_period = medium_period
        self._slow_period = slow_period
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "ma_ribbon"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Moving Average Ribbon strategy - trade based on alignment of multiple MAs"

    @property
    def strategy_type(self) -> str:
        return "momentum"

    def _set_default_parameters(self) -> None:
        self._params = {
            "fast_period": StrategyParameter(
                name="fast_period",
                value=5,
                min_value=2,
                max_value=20,
                step=1,
                description="Fast MA period",
            ),
            "medium_period": StrategyParameter(
                name="medium_period",
                value=20,
                min_value=10,
                max_value=50,
                step=1,
                description="Medium MA period",
            ),
            "slow_period": StrategyParameter(
                name="slow_period",
                value=50,
                min_value=20,
                max_value=200,
                step=5,
                description="Slow MA period",
            ),
        }

    def _validate_parameters(self) -> bool:
        if self._fast_period >= self._medium_period:
            raise ValueError("fast_period must be less than medium_period")
        if self._medium_period >= self._slow_period:
            raise ValueError("medium_period must be less than slow_period")
        return True

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]

        ma_fast = close.ewm(span=self._fast_period, adjust=False).mean()
        ma_medium = close.ewm(span=self._medium_period, adjust=False).mean()
        ma_slow = close.ewm(span=self._slow_period, adjust=False).mean()

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["ma_fast"] = ma_fast
        signals["ma_medium"] = ma_medium
        signals["ma_slow"] = ma_slow
        signals["signal"] = 0

        bullish = (ma_fast > ma_medium) & (ma_medium > ma_slow)
        bearish = (ma_fast < ma_medium) & (ma_medium < ma_slow)

        bullish = bullish.fillna(False)
        bearish = bearish.fillna(False)

        prev_bullish = bullish.shift(1).fillna(False)
        prev_bearish = bearish.shift(1).fillna(False)

        golden_cross = bullish & ~prev_bullish
        death_cross = bearish & ~prev_bearish

        signals.loc[golden_cross, "signal"] = 1
        signals.loc[death_cross, "signal"] = -1

        return signals

    def get_requirements(self) -> list[str]:
        return ["close"]


@register_strategy("triple_ma")
class TripleMAStrategy(BaseStrategy):
    def __init__(
        self, fast_period: int = 10, medium_period: int = 30, slow_period: int = 50, **kwargs
    ):
        self._fast_period = fast_period
        self._medium_period = medium_period
        self._slow_period = slow_period
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "triple_ma"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Triple Moving Average crossover strategy"

    @property
    def strategy_type(self) -> str:
        return "momentum"

    def _set_default_parameters(self) -> None:
        self._params = {
            "fast_period": StrategyParameter(
                name="fast_period",
                value=10,
                min_value=2,
                max_value=30,
                step=1,
                description="Fast MA period",
            ),
            "medium_period": StrategyParameter(
                name="medium_period",
                value=30,
                min_value=10,
                max_value=60,
                step=1,
                description="Medium MA period",
            ),
            "slow_period": StrategyParameter(
                name="slow_period",
                value=50,
                min_value=20,
                max_value=200,
                step=5,
                description="Slow MA period",
            ),
        }

    def _validate_parameters(self) -> bool:
        if self._fast_period >= self._medium_period:
            raise ValueError("fast_period must be less than medium_period")
        if self._medium_period >= self._slow_period:
            raise ValueError("medium_period must be less than slow_period")
        return True

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]

        ma_fast = close.rolling(window=self._fast_period).mean()
        ma_medium = close.rolling(window=self._medium_period).mean()
        ma_slow = close.rolling(window=self._slow_period).mean()

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["ma_fast"] = ma_fast
        signals["ma_medium"] = ma_medium
        signals["ma_slow"] = ma_slow
        signals["signal"] = 0

        golden_cross_condition = (
            (ma_fast > ma_medium) & (ma_medium > ma_slow) & (ma_fast.shift(1) <= ma_medium.shift(1))
        )
        death_cross_condition = (
            (ma_fast < ma_medium) & (ma_medium < ma_slow) & (ma_fast.shift(1) >= ma_medium.shift(1))
        )

        golden_cross = golden_cross_condition.fillna(False)
        death_cross = death_cross_condition.fillna(False)

        signals.loc[golden_cross, "signal"] = 1
        signals.loc[death_cross, "signal"] = -1

        return signals

    def get_requirements(self) -> list[str]:
        return ["close"]
