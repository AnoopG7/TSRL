import pandas as pd
import numpy as np
from typing import Dict, Any

from src.strategies.base import BaseStrategy, StrategyParameter
from src.strategies.registry import register_strategy


@register_strategy("bollinger_bands")
class BollingerBandsStrategy(BaseStrategy):
    def __init__(self, period: int = 20, std_dev: float = 2.0, **kwargs):
        self._period = period
        self._std_dev = std_dev
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "bollinger_bands"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Bollinger Bands mean reversion strategy"

    @property
    def strategy_type(self) -> str:
        return "mean_reversion"

    def _set_default_parameters(self) -> None:
        self._params = {
            "period": StrategyParameter(
                name="period",
                value=20,
                min_value=5,
                max_value=100,
                step=1,
                description="Bollinger Bands period",
            ),
            "std_dev": StrategyParameter(
                name="std_dev",
                value=2.0,
                min_value=0.5,
                max_value=4.0,
                step=0.5,
                description="Standard deviation multiplier",
            ),
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]

        sma = close.rolling(window=self._params["period"].value).mean()
        std = close.rolling(window=self._params["period"].value).std()

        upper_band = sma + (std * self._params["std_dev"].value)
        lower_band = sma - (std * self._params["std_dev"].value)

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["sma"] = sma
        signals["upper_band"] = upper_band
        signals["lower_band"] = lower_band
        signals["signal"] = 0

        signals.loc[close < lower_band, "signal"] = 1
        signals.loc[close > upper_band, "signal"] = -1

        signals.loc[(close > sma) & (close.shift(1) <= lower_band.shift(1)), "signal"] = 1
        signals.loc[(close < sma) & (close.shift(1) >= upper_band.shift(1)), "signal"] = -1

        return signals

    def get_requirements(self) -> list[str]:
        return ["close"]


@register_strategy("bbands")
class BollingerBandsBreakoutStrategy(BaseStrategy):
    def __init__(self, period: int = 20, std_dev: float = 2.0, **kwargs):
        self._period = period
        self._std_dev = std_dev
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "bbands"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Bollinger Bands breakout strategy"

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
                description="Bollinger Bands period",
            ),
            "std_dev": StrategyParameter(
                name="std_dev",
                value=2.0,
                min_value=0.5,
                max_value=4.0,
                step=0.5,
                description="Standard deviation multiplier",
            ),
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]

        sma = close.rolling(window=self._params["period"].value).mean()
        std = close.rolling(window=self._params["period"].value).std()

        upper_band = sma + (std * self._params["std_dev"].value)
        lower_band = sma - (std * self._params["std_dev"].value)

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["sma"] = sma
        signals["upper_band"] = upper_band
        signals["lower_band"] = lower_band
        signals["signal"] = 0

        # Buy: price breaks above upper band (first bar of breakout)
        breakout_up = (close > upper_band) & (close.shift(1) <= upper_band.shift(1))
        signals.loc[breakout_up, "signal"] = 1

        # Sell: price falls back below SMA after being above upper band
        fall_below_sma = (close < sma) & (close.shift(1) >= sma.shift(1))
        signals.loc[fall_below_sma, "signal"] = -1

        return signals

    def get_requirements(self) -> list[str]:
        return ["close"]
