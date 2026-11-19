"""The equity curve must reflect open positions every bar, not only on exit days."""

import numpy as np
import pandas as pd

from src.engine.backtest.engine import BacktestConfig, BacktestEngine
from src.strategies.base import BaseStrategy


class _OneLongTrade(BaseStrategy):
    """Buys on bar 5 and sells on bar 15."""

    @property
    def name(self):
        return "one_long"

    @property
    def version(self):
        return "1"

    @property
    def description(self):
        return "test"

    @property
    def strategy_type(self):
        return "test"

    def _set_default_parameters(self):
        self._params = {}

    def generate_signals(self, data):
        sig = pd.DataFrame(index=data.index)
        sig["signal"] = 0
        sig.iloc[5, 0] = 1
        sig.iloc[15, 0] = -1
        return sig

    def get_requirements(self):
        return ["close"]


def _rising_prices(n=30):
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    close = np.linspace(100, 130, n)
    return pd.DataFrame({"open": close, "high": close, "low": close, "close": close, "volume": 1e6}, index=idx)


def test_equity_moves_while_position_is_open():
    data = _rising_prices()
    result = BacktestEngine(BacktestConfig(commission=0, slippage=0)).run(_OneLongTrade(), data)
    eq = result.equity_curve["equity"]
    held = eq.iloc[6:15]
    # Prices rise every bar, so marked-to-market equity must rise every bar too
    assert (held.diff().dropna() > 0).all()


def test_equity_ends_at_final_capital():
    data = _rising_prices()
    result = BacktestEngine(BacktestConfig(commission=0, slippage=0)).run(_OneLongTrade(), data)
    eq = result.equity_curve["equity"]
    # Every position is closed on the last bar, so the curve must end at final capital
    assert abs(eq.iloc[-1] - result.final_capital) < 1e-6
