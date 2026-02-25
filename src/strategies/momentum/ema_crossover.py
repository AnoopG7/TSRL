from typing import Dict, Any

import pandas as pd
import numpy as np

from src.strategies.base import BaseStrategy, RiskManagementResult
from src.strategies.registry import register_strategy


@register_strategy("ema_crossover")
class EMACrossoverStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "EMA Crossover"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Strategy that uses EMA crossovers to generate buy/sell signals. Buy when fast EMA crosses above slow EMA, sell when it crosses below."

    @property
    def strategy_type(self) -> str:
        return "momentum"

    def _set_default_parameters(self) -> None:
        self._params = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
        }

    def _validate_parameters(self) -> bool:
        if self._params["fast_period"] >= self._params["slow_period"]:
            raise ValueError("Fast period must be less than slow period")
        if self._params["fast_period"] <= 0 or self._params["slow_period"] <= 0:
            raise ValueError("Periods must be positive")
        return True

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        fast_period = int(self._params["fast_period"])
        slow_period = int(self._params["slow_period"])

        df["ema_fast"] = df["close"].ewm(span=fast_period, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=slow_period, adjust=False).mean()

        df["crossover"] = df["ema_fast"] - df["ema_slow"]
        df["prev_crossover"] = df["crossover"].shift(1)

        df["signal"] = 0

        df.loc[(df["crossover"] > 0) & (df["prev_crossover"] <= 0), "signal"] = 1

        df.loc[(df["crossover"] < 0) & (df["prev_crossover"] >= 0), "signal"] = -1

        df["signal_strength"] = np.abs(df["crossover"] / df["close"])

        return df

    def get_requirements(self) -> list:
        return ["close"]


@register_strategy("rsi_mean_reversion")
class RSIMeanReversionStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "RSI Mean Reversion"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Mean reversion strategy using RSI. Buy when oversold, sell when overbought."

    @property
    def strategy_type(self) -> str:
        return "mean_reversion"

    def _set_default_parameters(self) -> None:
        self._params = {
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70,
            "exit_on_cross": True,
        }

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        rsi_period = int(self._params["rsi_period"])
        oversold = float(self._params["oversold_threshold"])
        overbought = float(self._params["overbought_threshold"])

        df["rsi"] = self._calculate_rsi(df["close"], rsi_period)

        df["signal"] = 0

        df.loc[df["rsi"] < oversold, "signal"] = 1
        df.loc[df["rsi"] > overbought, "signal"] = -1

        if self._params.get("exit_on_cross", True):
            df.loc[
                (df["rsi"] > oversold) & (df["rsi"] < overbought) & (df["rsi"].shift(1) < oversold),
                "signal",
            ] = -1
            df.loc[
                (df["rsi"] < overbought)
                & (df["rsi"] > oversold)
                & (df["rsi"].shift(1) > overbought),
                "signal",
            ] = 1

        df["signal_strength"] = np.where(
            df["rsi"] < oversold,
            (oversold - df["rsi"]) / oversold,
            np.where(df["rsi"] > overbought, (df["rsi"] - overbought) / (100 - overbought), 0),
        )

        return df

    def get_requirements(self) -> list:
        return ["close"]


@register_strategy("breakout")
class BreakoutStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "Breakout Strategy"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Strategy that buys when price breaks above recent high and sells when it breaks below recent low."

    @property
    def strategy_type(self) -> str:
        return "breakout"

    def _set_default_parameters(self) -> None:
        self._params = {
            "lookback_period": 20,
            "atr_period": 14,
            "atr_multiplier": 2.0,
            "use_trailing_stop": True,
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        lookback = int(self._params["lookback_period"])
        atr_period = int(self._params["atr_period"])
        atr_multiplier = float(self._params["atr_multiplier"])

        df["highest"] = df["high"].rolling(window=lookback).max()
        df["lowest"] = df["low"].rolling(window=lookback).min()

        df["high_prev"] = df["highest"].shift(1)
        df["low_prev"] = df["lowest"].shift(1)

        high = df["high"]
        low = df["low"]

        df["breakout_up"] = (high > df["high_prev"]) & (high.shift(1) <= df["high_prev"].shift(1))
        df["breakout_down"] = (low < df["low_prev"]) & (low.shift(1) >= df["low_prev"].shift(1))

        df["signal"] = 0
        df.loc[df["breakout_up"], "signal"] = 1
        df.loc[df["breakout_down"], "signal"] = -1

        df["atr"] = self._calculate_atr(df, atr_period)
        df["signal_strength"] = df["atr"] / df["close"] * atr_multiplier

        return df

    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def get_requirements(self) -> list:
        return ["open", "high", "low", "close"]
