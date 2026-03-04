import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from src.engine.backtest.engine import BacktestConfig, BacktestResult, BacktestEngine, VectorizedBacktestEngine
from src.strategies.base import BaseStrategy
from src.domain.entities.trade import TradeSide, TradeStatus
from src.domain.entities.position import PositionSide


class MockStrategy(BaseStrategy):
    """Mock strategy for testing backtest engine"""

    @property
    def name(self) -> str:
        return "Mock Strategy"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Mock strategy for testing"

    @property
    def strategy_type(self) -> str:
        return "test"

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        signals = data.copy()
        signals["signal"] = 0
        return signals


class TestBacktestConfig:
    """Tests for BacktestConfig"""

    def test_default_values(self):
        config = BacktestConfig()

        assert config.initial_capital == 100000.0
        assert config.commission == 0.001
        assert config.slippage == 0.0005
        assert config.risk_per_trade == 0.02
        assert config.max_position_size == 0.2
        assert config.allow_shorting is True
        assert config.verbose is False

    def test_custom_values(self):
        config = BacktestConfig(
            initial_capital=50000.0,
            commission=0.002,
            slippage=0.001,
            risk_per_trade=0.01,
            max_position_size=0.3,
            allow_shorting=False,
            verbose=True,
        )

        assert config.initial_capital == 50000.0
        assert config.commission == 0.002
        assert config.slippage == 0.001
        assert config.risk_per_trade == 0.01
        assert config.max_position_size == 0.3
        assert config.allow_shorting is False
        assert config.verbose is True


class TestBacktestResult:
    """Tests for BacktestResult"""

    def test_default_values(self):
        result = BacktestResult()

        assert result.trades == []
        assert result.equity_curve.empty
        assert result.final_capital == 0.0
        assert result.total_return == 0.0
        assert result.execution_time_ms == 0.0

    def test_to_dict(self):
        from src.domain.entities.metrics import RiskMetrics

        result = BacktestResult(
            final_capital=110000.0,
            total_return=0.1,
            execution_time_ms=100.0,
            metrics=RiskMetrics(total_return=0.1),
        )

        d = result.to_dict()

        assert d["final_capital"] == 110000.0
        assert d["total_return"] == 0.1
        assert d["execution_time_ms"] == 100.0


class TestBacktestEngine:
    """Tests for BacktestEngine"""

    def test_engine_creation_default_config(self):
        engine = BacktestEngine()

        assert engine.config.initial_capital == 100000.0

    def test_engine_creation_custom_config(self):
        config = BacktestConfig(initial_capital=50000.0)
        engine = BacktestEngine(config)

        assert engine.config.initial_capital == 50000.0

    def test_run_with_empty_data(self):
        engine = BacktestEngine()
        strategy = MockStrategy()

        data = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        result = engine.run(strategy, data)

        assert result.final_capital == 100000.0
        assert result.total_return == 0.0
        assert len(result.trades) == 0

    def test_run_with_single_bar(self):
        engine = BacktestEngine()
        strategy = MockStrategy()

        data = pd.DataFrame(
            {"open": [100], "high": [105], "low": [95], "close": [102], "volume": [1000000]},
            index=[datetime(2023, 1, 1)],
        )

        result = engine.run(strategy, data)

        assert result.final_capital == 100000.0
        assert len(result.trades) == 0

    def test_run_with_all_buy_signals(self):
        """Test when strategy generates continuous buy signals - should only enter once"""

        class BuyOnceStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "Buy Once"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Buy once then hold"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = 0
                signals.loc[signals.index[5], "signal"] = 1  # Buy at index 5
                return signals

        engine = BacktestEngine()
        strategy = BuyOnceStrategy()

        data = pd.DataFrame(
            {
                "open": list(range(100, 120)),
                "high": list(range(101, 121)),
                "low": list(range(99, 119)),
                "close": list(range(100, 120)),
                "volume": [1000000] * 20,
            },
            index=pd.date_range("2023-01-01", periods=20),
        )

        result = engine.run(strategy, data)

        assert len(result.trades) == 1
        assert result.trades[0].side == TradeSide.LONG
        assert result.trades[0].status == TradeStatus.CLOSED

    def test_run_with_short_signals(self):
        """Test short selling when allowed"""

        class ShortStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "Short Strategy"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Short then cover"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = 0
                signals.loc[signals.index[5], "signal"] = -1  # Short at index 5
                signals.loc[signals.index[10], "signal"] = 1  # Cover at index 10
                return signals

        engine = BacktestEngine(BacktestConfig(allow_shorting=True))
        strategy = ShortStrategy()

        data = pd.DataFrame(
            {
                "open": list(range(100, 120)),
                "high": list(range(101, 121)),
                "low": list(range(99, 119)),
                "close": list(range(100, 120)),
                "volume": [1000000] * 20,
            },
            index=pd.date_range("2023-01-01", periods=20),
        )

        result = engine.run(strategy, data)

        assert len(result.trades) >= 1
        assert result.trades[0].side == TradeSide.SHORT

    def test_run_without_shorting(self):
        """Test short selling disabled"""

        class ShortStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "Short Strategy"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Try to short"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = -1  # Try to short
                return signals

        engine = BacktestEngine(BacktestConfig(allow_shorting=False))
        strategy = ShortStrategy()

        data = pd.DataFrame(
            {
                "open": list(range(100, 110)),
                "high": list(range(101, 111)),
                "low": list(range(99, 109)),
                "close": list(range(100, 110)),
                "volume": [1000000] * 10,
            },
            index=pd.date_range("2023-01-01", periods=10),
        )

        result = engine.run(strategy, data)

        assert len(result.trades) == 0  # No shorts allowed

    def test_run_with_commission(self):
        """Test that commission is applied"""

        class SimpleStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "Simple"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Simple"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = 0
                signals.loc[signals.index[5], "signal"] = 1
                signals.loc[signals.index[10], "signal"] = -1
                return signals

        config = BacktestConfig(commission=0.01)  # 1% commission
        engine = BacktestEngine(config)
        strategy = SimpleStrategy()

        data = pd.DataFrame(
            {
                "open": list(range(100, 120)),
                "high": list(range(101, 121)),
                "low": list(range(99, 119)),
                "close": list(range(100, 120)),
                "volume": [1000000] * 20,
            },
            index=pd.date_range("2023-01-01", periods=20),
        )

        result = engine.run(strategy, data)

        # Commission should reduce profits
        trade = result.trades[0]
        assert trade.commission > 0

    def test_run_with_slippage(self):
        """Test that slippage is applied"""

        class SimpleStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "Simple"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Simple"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = 0
                signals.loc[signals.index[5], "signal"] = 1
                signals.loc[signals.index[10], "signal"] = -1
                return signals

        config = BacktestConfig(slippage=0.01)  # 1% slippage
        engine = BacktestEngine(config)
        strategy = SimpleStrategy()

        data = pd.DataFrame(
            {
                "open": list(range(100, 120)),
                "high": list(range(101, 121)),
                "low": list(range(99, 119)),
                "close": list(range(100, 120)),
                "volume": [1000000] * 20,
            },
            index=pd.date_range("2023-01-01", periods=20),
        )

        result = engine.run(strategy, data)

        trade = result.trades[0]
        assert trade.slippage > 0

    def test_before_backtest_hook(self):
        """Test that before_backtest hook is called"""

        class HookStrategy(BaseStrategy):
            def __init__(self):
                super().__init__()
                self.before_backtest_called = False

            @property
            def name(self) -> str:
                return "Hook Strategy"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Test hook"

            @property
            def strategy_type(self) -> str:
                return "test"

            def before_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
                self.before_backtest_called = True
                return data

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = 0
                return signals

        engine = BacktestEngine()
        strategy = HookStrategy()

        data = pd.DataFrame(
            {"open": [100], "high": [105], "low": [95], "close": [102], "volume": [1000000]},
            index=[datetime(2023, 1, 1)],
        )

        engine.run(strategy, data)

        assert strategy.before_backtest_called is True


class TestVectorizedBacktestEngine:
    """Tests for VectorizedBacktestEngine"""

    def test_engine_creation(self):
        engine = VectorizedBacktestEngine()

        assert engine.config.initial_capital == 100000.0

    def test_run_with_buy_sell_signals(self):
        """Test vectorized engine with buy and sell signals"""

        class BuySellStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "BuySell"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Buy then sell"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = 0
                signals.loc[signals.index[5], "signal"] = 1
                signals.loc[signals.index[15], "signal"] = -1
                return signals

        engine = VectorizedBacktestEngine()
        data = pd.DataFrame(
            {
                "open": list(range(100, 120)),
                "high": list(range(101, 121)),
                "low": list(range(99, 119)),
                "close": list(range(100, 120)),
                "volume": [1000000] * 20,
            },
            index=pd.date_range("2023-01-01", periods=20),
        )

        result = engine.run(BuySellStrategy(), data)

        assert isinstance(result, BacktestResult)
        assert result.execution_time_ms >= 0
        assert "equity" in result.equity_curve.columns
        assert "returns" in result.equity_curve.columns
        assert "drawdown" in result.equity_curve.columns

    def test_run_with_short_signals(self):
        """Test vectorized engine with short signals"""

        class ShortStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "Short"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Short then cover"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = 0
                signals.loc[signals.index[3], "signal"] = -1
                signals.loc[signals.index[8], "signal"] = 1
                return signals

        engine = VectorizedBacktestEngine()
        data = pd.DataFrame(
            {
                "open": list(range(100, 115)),
                "high": list(range(101, 116)),
                "low": list(range(99, 114)),
                "close": list(range(100, 115)),
                "volume": [1000000] * 15,
            },
            index=pd.date_range("2023-01-01", periods=15),
        )

        result = engine.run(ShortStrategy(), data)

        assert isinstance(result, BacktestResult)
        assert any(t.side == TradeSide.SHORT for t in result.trades)

    def test_extract_trades_from_signals(self):
        """Test that trades are correctly extracted from signal changes"""

        class MultiTradeStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "MultiTrade"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Multiple trades"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = 0
                signals.loc[signals.index[2], "signal"] = 1   # Buy
                signals.loc[signals.index[5], "signal"] = -1  # Sell / Short
                signals.loc[signals.index[8], "signal"] = 1   # Cover / Buy
                return signals

        engine = VectorizedBacktestEngine()
        data = pd.DataFrame(
            {
                "open": list(range(100, 115)),
                "high": list(range(101, 116)),
                "low": list(range(99, 114)),
                "close": list(range(100, 115)),
                "volume": [1000000] * 15,
            },
            index=pd.date_range("2023-01-01", periods=15),
        )

        result = engine.run(MultiTradeStrategy(), data)

        assert len(result.trades) >= 2
        assert result.trades[0].side == TradeSide.LONG
        assert result.trades[1].side == TradeSide.SHORT

    def test_equity_curve_has_cumulative_and_drawdown(self):
        """Test equity curve columns"""

        engine = VectorizedBacktestEngine()
        strategy = MockStrategy()

        data = pd.DataFrame(
            {
                "open": list(range(100, 120)),
                "high": list(range(101, 121)),
                "low": list(range(99, 119)),
                "close": list(range(100, 120)),
                "volume": [1000000] * 20,
            },
            index=pd.date_range("2023-01-01", periods=20),
        )

        result = engine.run(strategy, data)

        assert "cumulative" in result.equity_curve.columns
        assert "running_max" in result.equity_curve.columns
        assert "drawdown" in result.equity_curve.columns

    def test_run_no_signals(self):
        """Test vectorized engine when strategy generates no signals"""
        engine = VectorizedBacktestEngine()
        strategy = MockStrategy()

        data = pd.DataFrame(
            {
                "open": list(range(100, 110)),
                "high": list(range(101, 111)),
                "low": list(range(99, 109)),
                "close": list(range(100, 110)),
                "volume": [1000000] * 10,
            },
            index=pd.date_range("2023-01-01", periods=10),
        )

        result = engine.run(strategy, data)

        assert isinstance(result, BacktestResult)
        assert len(result.trades) == 0
        assert result.final_capital == pytest.approx(100000.0, rel=0.01)

    def test_commission_applied(self):
        """Test that commission reduces returns in vectorized engine"""

        class BuyStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "Buy"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Buy"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
                signals = data.copy()
                signals["signal"] = 0
                signals.loc[signals.index[2], "signal"] = 1
                signals.loc[signals.index[8], "signal"] = -1
                return signals

        config_no_comm = BacktestConfig(commission=0.0)
        config_high_comm = BacktestConfig(commission=0.05)

        data = pd.DataFrame(
            {
                "open": list(range(100, 115)),
                "high": list(range(101, 116)),
                "low": list(range(99, 114)),
                "close": list(range(100, 115)),
                "volume": [1000000] * 15,
            },
            index=pd.date_range("2023-01-01", periods=15),
        )

        result_no = VectorizedBacktestEngine(config_no_comm).run(BuyStrategy(), data)
        result_hi = VectorizedBacktestEngine(config_high_comm).run(BuyStrategy(), data)

        # Higher commission should reduce final capital
        assert result_hi.final_capital < result_no.final_capital

