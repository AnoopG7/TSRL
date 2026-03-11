import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.engine.backtest.portfolio_engine import (
    PortfolioBacktestEngine,
    MultiStrategyPortfolioEngine,
    PortfolioConfig,
    PortfolioResult,
    PortfolioMetricsMixin,
)
from src.engine.backtest.engine import BacktestResult
from src.strategies.base import BaseStrategy


class SimpleUpStrategy(BaseStrategy):
    """Strategy that buys and holds — for testing portfolio engine."""

    @property
    def name(self) -> str:
        return "simple_up"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Simple buy and hold"

    @property
    def strategy_type(self) -> str:
        return "test"

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        signals = data.copy()
        signals["signal"] = 0
        signals.loc[signals.index[2], "signal"] = 1
        signals.loc[signals.index[-2], "signal"] = -1
        return signals


class SimpleDownStrategy(BaseStrategy):
    """Strategy that shorts — for testing multi-strategy engine."""

    @property
    def name(self) -> str:
        return "simple_down"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Simple short"

    @property
    def strategy_type(self) -> str:
        return "test"

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        signals = data.copy()
        signals["signal"] = 0
        signals.loc[signals.index[3], "signal"] = -1
        signals.loc[signals.index[-3], "signal"] = 1
        return signals


@pytest.fixture
def sample_symbols_data():
    """Create OHLCV data for two symbols."""
    np.random.seed(42)

    def make_data(base_price, periods=50):
        prices = base_price + np.cumsum(np.random.randn(periods) * 0.5)
        return pd.DataFrame(
            {
                "open": prices + np.random.randn(periods) * 0.1,
                "high": prices + np.abs(np.random.randn(periods)) * 0.5,
                "low": prices - np.abs(np.random.randn(periods)) * 0.5,
                "close": prices,
                "volume": np.random.randint(500000, 5000000, periods).astype(float),
            },
            index=pd.date_range("2023-01-01", periods=periods),
        )

    return {
        "AAPL": make_data(150),
        "GOOGL": make_data(100),
    }


class TestPortfolioConfig:
    def test_default_config(self):
        config = PortfolioConfig()

        assert config.initial_capital == 100000.0
        assert config.max_position_size == 0.2
        assert config.max_positions == 5
        assert config.commission == 0.001
        assert config.slippage == 0.0005
        assert config.rebalance_frequency == "daily"

    def test_custom_config(self):
        config = PortfolioConfig(
            initial_capital=50000.0,
            max_position_size=0.3,
            max_positions=10,
            commission=0.002,
        )

        assert config.initial_capital == 50000.0
        assert config.max_position_size == 0.3
        assert config.max_positions == 10
        assert config.commission == 0.002


class TestPortfolioResult:
    def test_default_result(self):
        result = PortfolioResult()

        assert result.symbols == []
        assert result.results == {}
        assert result.total_return == 0.0
        assert result.total_trades == 0
        assert result.sharpe_ratio == 0.0
        assert result.max_drawdown == 0.0
        assert result.win_rate == 0.0
        assert result.execution_time_ms == 0.0


class TestPortfolioMetricsMixin:
    def test_combine_equity_curves_empty(self):
        mixin = PortfolioMetricsMixin()
        result = mixin._combine_equity_curves({})

        assert result.empty

    def test_calculate_total_return_empty(self):
        mixin = PortfolioMetricsMixin()
        result = mixin._calculate_total_return(pd.DataFrame(), 100000)

        assert result == 0.0

    def test_calculate_sharpe_empty(self):
        mixin = PortfolioMetricsMixin()
        result = mixin._calculate_sharpe(pd.DataFrame())

        assert result == 0.0

    def test_calculate_max_drawdown_empty(self):
        mixin = PortfolioMetricsMixin()
        result = mixin._calculate_max_drawdown(pd.DataFrame())

        assert result == 0.0

    def test_calculate_win_rate_no_trades(self):
        mixin = PortfolioMetricsMixin()
        result = mixin._calculate_win_rate([])

        assert result == 0.0

    def test_calculate_sharpe_with_data(self):
        mixin = PortfolioMetricsMixin()
        equity = pd.DataFrame(
            {"total": [100000, 101000, 102000, 101500, 103000]},
            index=pd.date_range("2023-01-01", periods=5),
        )
        sharpe = mixin._calculate_sharpe(equity)

        assert isinstance(sharpe, float)

    def test_calculate_max_drawdown_with_data(self):
        mixin = PortfolioMetricsMixin()
        equity = pd.DataFrame(
            {"total": [100000, 110000, 105000, 100000, 108000]},
            index=pd.date_range("2023-01-01", periods=5),
        )
        dd = mixin._calculate_max_drawdown(equity)

        assert dd > 0
        assert dd <= 1.0


class TestPortfolioBacktestEngine:
    def test_engine_creation(self):
        engine = PortfolioBacktestEngine()

        assert engine.config.initial_capital == 100000.0

    def test_engine_with_custom_config(self):
        config = PortfolioConfig(initial_capital=50000)
        engine = PortfolioBacktestEngine(config)

        assert engine.config.initial_capital == 50000.0

    def test_run_single_symbol(self, sample_symbols_data):
        engine = PortfolioBacktestEngine()
        data = {"AAPL": sample_symbols_data["AAPL"]}

        result = engine.run(SimpleUpStrategy(), data)

        assert isinstance(result, PortfolioResult)
        assert result.symbols == ["AAPL"]
        assert "AAPL" in result.results
        assert result.execution_time_ms >= 0

    def test_run_multiple_symbols(self, sample_symbols_data):
        engine = PortfolioBacktestEngine()

        result = engine.run(SimpleUpStrategy(), sample_symbols_data)

        assert isinstance(result, PortfolioResult)
        assert len(result.symbols) == 2
        assert "AAPL" in result.results
        assert "GOOGL" in result.results
        assert not result.combined_equity.empty
        assert "total" in result.combined_equity.columns

    def test_capital_split_across_symbols(self, sample_symbols_data):
        config = PortfolioConfig(initial_capital=100000)
        engine = PortfolioBacktestEngine(config)

        result = engine.run(SimpleUpStrategy(), sample_symbols_data)

        assert isinstance(result, PortfolioResult)
        assert len(result.results) == 2

    def test_run_with_custom_config(self, sample_symbols_data):
        config = PortfolioConfig(initial_capital=200000, commission=0.002)
        engine = PortfolioBacktestEngine()

        result = engine.run(SimpleUpStrategy(), sample_symbols_data, config=config)

        assert isinstance(result, PortfolioResult)


class TestMultiStrategyPortfolioEngine:
    def test_engine_creation(self):
        engine = MultiStrategyPortfolioEngine()

        assert engine.config.initial_capital == 100000.0

    def test_run_single_strategy_single_symbol(self, sample_symbols_data):
        engine = MultiStrategyPortfolioEngine()
        strategies = {"up": SimpleUpStrategy()}
        data = {"AAPL": sample_symbols_data["AAPL"]}

        result = engine.run(strategies, data)

        assert isinstance(result, PortfolioResult)
        assert "up_AAPL" in result.results

    def test_run_multiple_strategies_multiple_symbols(self, sample_symbols_data):
        engine = MultiStrategyPortfolioEngine()
        strategies = {
            "up": SimpleUpStrategy(),
            "down": SimpleDownStrategy(),
        }

        result = engine.run(strategies, sample_symbols_data)

        assert isinstance(result, PortfolioResult)
        assert len(result.results) == 4  # 2 strategies × 2 symbols
        assert "up_AAPL" in result.results
        assert "up_GOOGL" in result.results
        assert "down_AAPL" in result.results
        assert "down_GOOGL" in result.results
        assert not result.combined_equity.empty
        assert "total" in result.combined_equity.columns
        assert result.execution_time_ms >= 0

    def test_run_with_custom_config(self, sample_symbols_data):
        config = PortfolioConfig(initial_capital=50000, commission=0.005)
        engine = MultiStrategyPortfolioEngine(config)
        strategies = {"up": SimpleUpStrategy()}

        result = engine.run(strategies, sample_symbols_data)

        assert isinstance(result, PortfolioResult)
