import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """Generate sample OHLCV data for testing"""
    n = 100
    dates = pd.date_range(start="2023-01-01", periods=n, freq="D")

    np.random.seed(42)
    price = 100
    prices = []
    for _ in range(n):
        price += np.random.randn() * 2
        prices.append(price)

    return pd.DataFrame(
        {
            "open": prices,
            "high": [p + abs(np.random.randn()) for p in prices],
            "low": [p - abs(np.random.randn()) for p in prices],
            "close": prices,
            "volume": [int(np.random.uniform(1e6, 5e6)) for _ in prices],
        },
        index=dates,
    )


@pytest.fixture
def sample_ohlcv_bullish() -> pd.DataFrame:
    """Generate bullish OHLCV data for testing"""
    n = 50
    dates = pd.date_range(start="2023-01-01", periods=n, freq="D")

    prices = np.linspace(100, 150, n)
    return pd.DataFrame(
        {
            "open": prices - 1,
            "high": prices + 2,
            "low": prices - 2,
            "close": prices,
            "volume": [int(1e6 + i * 1e5) for i in range(n)],
        },
        index=dates,
    )


@pytest.fixture
def sample_ohlcv_bearish() -> pd.DataFrame:
    """Generate bearish OHLCV data for testing"""
    n = 50
    dates = pd.date_range(start="2023-01-01", periods=n, freq="D")

    prices = np.linspace(150, 100, n)
    return pd.DataFrame(
        {
            "open": prices + 1,
            "high": prices + 2,
            "low": prices - 2,
            "close": prices,
            "volume": [int(1e6 + i * 1e5) for i in range(n)],
        },
        index=dates,
    )


@pytest.fixture
def sample_trades() -> List:
    """List of sample Trade objects"""
    from src.domain.entities.trade import Trade, TradeSide, TradeStatus

    return [
        Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.LONG,
            exit_time=datetime(2023, 1, 5),
            exit_price=110.0,
            status=TradeStatus.CLOSED,
            commission=1.0,
            slippage=0.5,
        ),
        Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 10),
            entry_price=105.0,
            quantity=10,
            side=TradeSide.LONG,
            exit_time=datetime(2023, 1, 15),
            exit_price=102.0,
            status=TradeStatus.CLOSED,
            commission=1.0,
            slippage=0.5,
        ),
        Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 20),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.SHORT,
            exit_time=datetime(2023, 1, 25),
            exit_price=95.0,
            status=TradeStatus.CLOSED,
            commission=1.0,
            slippage=0.5,
        ),
    ]


@pytest.fixture
def sample_trades_dict() -> List[dict]:
    """List of sample trade dictionaries"""
    return [
        {
            "symbol": "AAPL",
            "entry_time": "2023-01-01T00:00:00",
            "entry_price": 100.0,
            "quantity": 10,
            "side": "LONG",
            "exit_time": "2023-01-05T00:00:00",
            "exit_price": 110.0,
            "status": "CLOSED",
            "commission": 1.0,
            "slippage": 0.5,
            "pnl": 98.5,
        },
        {
            "symbol": "AAPL",
            "entry_time": "2023-01-10T00:00:00",
            "entry_price": 105.0,
            "quantity": 10,
            "side": "LONG",
            "exit_time": "2023-01-15T00:00:00",
            "exit_price": 102.0,
            "status": "CLOSED",
            "commission": 1.0,
            "slippage": 0.5,
            "pnl": -31.5,
        },
    ]


@pytest.fixture
def sample_equity_curve() -> pd.DataFrame:
    """Sample equity curve for testing"""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    np.random.seed(42)

    equity = 100000
    values = [equity]
    for _ in range(99):
        equity *= 1 + np.random.randn() * 0.02
        values.append(equity)

    return pd.DataFrame(
        {"equity": values, "returns": pd.Series(values).pct_change().fillna(0)},
        index=dates,
    )


@pytest.fixture
def sample_returns() -> pd.Series:
    """Sample returns series for testing"""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=252, freq="D")
    returns = pd.Series(np.random.randn(252) * 0.02, index=dates)
    return returns


@pytest.fixture
def empty_ohlcv() -> pd.DataFrame:
    """Empty OHLCV DataFrame"""
    return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])


@pytest.fixture
def single_bar_ohlcv() -> pd.DataFrame:
    """Single bar OHLCV DataFrame"""
    return pd.DataFrame(
        {"open": [100], "high": [105], "low": [95], "close": [102], "volume": [1000000]},
        index=[datetime(2023, 1, 1)],
    )


@pytest.fixture
def sample_strategy_params() -> dict:
    """Sample strategy parameters"""
    return {
        "fast_period": 9,
        "slow_period": 21,
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
    }
