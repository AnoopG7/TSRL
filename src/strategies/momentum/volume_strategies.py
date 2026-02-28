import pandas as pd
import numpy as np
from typing import Dict, Any

from src.strategies.base import BaseStrategy, StrategyParameter
from src.strategies.registry import register_strategy


@register_strategy("volume_profile")
class VolumeProfileStrategy(BaseStrategy):
    def __init__(self, lookback: int = 20, volume_threshold: float = 1.5, **kwargs):
        self._lookback = lookback
        self._volume_threshold = volume_threshold
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "volume_profile"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Volume breakout strategy based on unusual volume"

    @property
    def strategy_type(self) -> str:
        return "momentum"

    def _set_default_parameters(self) -> None:
        self._params = {
            "lookback": StrategyParameter(
                name="lookback",
                value=20,
                min_value=5,
                max_value=100,
                step=1,
                description="Lookback period for average volume",
            ),
            "volume_threshold": StrategyParameter(
                name="volume_threshold",
                value=1.5,
                min_value=1.0,
                max_value=5.0,
                step=0.1,
                description="Volume multiplier for breakout signal",
            ),
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]
        volume = data["volume"]

        avg_volume = volume.rolling(window=self._params["lookback"].value).mean()

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["volume"] = volume
        signals["avg_volume"] = avg_volume
        signals["signal"] = 0

        volume_spike = volume > (avg_volume * self._params["volume_threshold"].value)
        price_up = close > close.shift(1)

        signals.loc[volume_spike & price_up, "signal"] = 1

        volume_drop = volume < (avg_volume * 0.5)
        price_down = close < close.shift(1)
        signals.loc[volume_drop & price_down, "signal"] = -1

        return signals

    def get_requirements(self) -> list[str]:
        return ["close", "volume"]


@register_strategy("volume_breakout")
class VolumeBreakoutStrategy(BaseStrategy):
    def __init__(self, period: int = 20, volume_ma_period: int = 20, **kwargs):
        self._period = period
        self._volume_ma_period = volume_ma_period
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "volume_breakout"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Price and volume breakout strategy"

    @property
    def strategy_type(self) -> str:
        return "breakout"

    def _set_default_parameters(self) -> None:
        self._params = {
            "period": StrategyParameter(
                name="period",
                value=20,
                min_value=5,
                max_value=100,
                step=1,
                description="Lookback period for breakout",
            ),
            "volume_ma_period": StrategyParameter(
                name="volume_ma_period",
                value=20,
                min_value=5,
                max_value=50,
                step=1,
                description="Volume moving average period",
            ),
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]
        volume = data["volume"]

        high = close.rolling(window=self._params["period"].value).max()
        volume_ma = volume.rolling(window=self._params["volume_ma_period"].value).mean()

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["high"] = high
        signals["volume_ma"] = volume_ma
        signals["signal"] = 0

        breakout = (close > high.shift(1)) & (volume > volume_ma)
        signals.loc[breakout, "signal"] = 1

        breakdown = (close < close.shift(1)) & (volume > volume_ma)
        signals.loc[breakdown, "signal"] = -1

        return signals

    def get_requirements(self) -> list[str]:
        return ["close", "volume"]
