import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from src.strategies.base import BaseStrategy, StrategyParameter, RiskManagementResult


class TestStrategyParameter:
    """Tests for StrategyParameter dataclass"""

    def test_strategy_parameter_creation(self):
        param = StrategyParameter(
            name="fast_period",
            value=12,
            min_value=1,
            max_value=100,
            step=1,
            description="Fast EMA period",
        )

        assert param.name == "fast_period"
        assert param.value == 12
        assert param.min_value == 1
        assert param.max_value == 100
        assert param.step == 1
        assert param.description == "Fast EMA period"

    def test_strategy_parameter_defaults(self):
        param = StrategyParameter(name="test", value=10)

        assert param.name == "test"
        assert param.value == 10
        assert param.min_value is None
        assert param.max_value is None
        assert param.step is None
        assert param.description == ""


class TestRiskManagementResult:
    """Tests for RiskManagementResult dataclass"""

    def test_risk_management_result_defaults(self):
        result = RiskManagementResult()

        assert result.should_stop_loss is False
        assert result.should_take_profit is False
        assert result.should_trailing_stop is False
        assert result.stop_loss_price is None
        assert result.take_profit_price is None
        assert result.position_size_multiplier == 1.0

    def test_risk_management_result_with_values(self):
        result = RiskManagementResult(
            should_stop_loss=True,
            stop_loss_price=95.0,
            position_size_multiplier=0.5,
        )

        assert result.should_stop_loss is True
        assert result.stop_loss_price == 95.0
        assert result.position_size_multiplier == 0.5


class MockStrategy(BaseStrategy):
    """Mock strategy for testing BaseStrategy"""

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

    def _set_default_parameters(self) -> None:
        self._params = {
            "param1": 10,
            "param2": "default",
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0
        return signals


class TestBaseStrategy:
    """Tests for BaseStrategy abstract class"""

    def test_strategy_initialization(self):
        strategy = MockStrategy()

        assert strategy.name == "Mock Strategy"
        assert strategy.version == "1.0.0"
        assert strategy.description == "Mock strategy for testing"
        assert strategy.strategy_type == "test"

    def test_get_parameters(self):
        strategy = MockStrategy()
        params = strategy.get_parameters()

        assert "param1" in params
        assert params["param1"] == 10

    def test_get_parameter(self):
        strategy = MockStrategy()

        assert strategy.get_parameter("param1") == 10
        assert strategy.get_parameter("param2") == "default"
        assert strategy.get_parameter("nonexistent", "fallback") == "fallback"

    def test_set_parameters(self):
        strategy = MockStrategy()
        strategy.set_parameters(param1=20, param2="custom")

        assert strategy.get_parameter("param1") == 20
        assert strategy.get_parameter("param2") == "custom"

    def test_set_parameters_partial(self):
        strategy = MockStrategy()
        strategy.set_parameters(param1=30)

        assert strategy.get_parameter("param1") == 30
        assert strategy.get_parameter("param2") == "default"

    def test_validate_parameters(self):
        strategy = MockStrategy()
        assert strategy.validate_parameters() is True

    def test_get_requirements_default(self):
        strategy = MockStrategy()
        requirements = strategy.get_requirements()

        assert requirements == ["open", "high", "low", "close", "volume"]

    def test_calculate_position_size_basic(self):
        strategy = MockStrategy()

        size = strategy.calculate_position_size(
            capital=100000,
            risk_per_trade=0.02,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        # risk_amount = 100000 * 0.02 = 2000
        # price_risk = 100 - 95 = 5
        # position_size = 2000 / 5 = 400
        assert size == 400

    def test_calculate_position_size_zero_entry(self):
        strategy = MockStrategy()

        size = strategy.calculate_position_size(
            capital=100000,
            risk_per_trade=0.02,
            entry_price=0.0,
            stop_loss_price=95.0,
        )

        assert size == 0

    def test_calculate_position_size_zero_stop_loss(self):
        strategy = MockStrategy()

        size = strategy.calculate_position_size(
            capital=100000,
            risk_per_trade=0.02,
            entry_price=100.0,
            stop_loss_price=100.0,
        )

        assert size == 0

    def test_calculate_position_size_negative_prices(self):
        strategy = MockStrategy()

        size = strategy.calculate_position_size(
            capital=100000,
            risk_per_trade=0.02,
            entry_price=100.0,
            stop_loss_price=105.0,
        )

        # Negative price risk should still work (abs)
        assert size == 400

    def test_to_dict(self):
        strategy = MockStrategy()
        d = strategy.to_dict()

        assert d["name"] == "Mock Strategy"
        assert d["version"] == "1.0.0"
        assert d["type"] == "test"
        assert "parameters" in d

    def test_from_dict(self):
        data = {
            "name": "Mock Strategy",
            "version": "1.0.0",
            "type": "test",
            "parameters": {"param1": 50, "param2": "from_dict"},
        }

        strategy = MockStrategy.from_dict(data)

        assert strategy.get_parameter("param1") == 50
        assert strategy.get_parameter("param2") == "from_dict"

    def test_repr(self):
        strategy = MockStrategy()
        assert repr(strategy) == "Mock Strategy(v1.0.0)"

    def test_entry_conditions_with_signal(self):
        strategy = MockStrategy()

        data = pd.DataFrame(
            {"close": [100, 101, 102]},
            index=pd.date_range("2023-01-01", periods=3),
        )

        # Override generate_signals for this test
        class TestStrategy(MockStrategy):
            def generate_signals(self, data):
                df = data.copy()
                df["signal"] = [0, 1, 0]
                return df

        test_strategy = TestStrategy()
        assert test_strategy.entry_conditions(data, 1) == True

    def test_entry_conditions_no_signal(self):
        strategy = MockStrategy()

        data = pd.DataFrame(
            {"close": [100, 101, 102]},
            index=pd.date_range("2023-01-01", periods=3),
        )

        assert strategy.entry_conditions(data, 0) == False

    def test_entry_conditions_invalid_index(self):
        strategy = MockStrategy()

        data = pd.DataFrame(
            {"close": [100, 101, 102]},
            index=pd.date_range("2023-01-01", periods=3),
        )

        assert strategy.entry_conditions(data, 10) == False

    def test_exit_conditions_with_signal(self):
        strategy = MockStrategy()

        data = pd.DataFrame(
            {"close": [100, 101, 102]},
            index=pd.date_range("2023-01-01", periods=3),
        )

        # Override generate_signals for this test
        class TestStrategy(MockStrategy):
            def generate_signals(self, data):
                df = data.copy()
                df["signal"] = [0, 0, -1]
                return df

        test_strategy = TestStrategy()
        assert test_strategy.exit_conditions(data, 2) == True

    def test_before_backtest(self):
        strategy = MockStrategy()
        data = pd.DataFrame({"close": [100]})
        result = strategy.before_backtest(data)

        assert result.equals(data)

    def test_after_backtest(self):
        strategy = MockStrategy()
        results = {"total_return": 0.1}
        result = strategy.after_backtest(results)

        assert result == results

    def test_risk_management_default(self):
        strategy = MockStrategy()
        result = strategy.risk_management(None, pd.DataFrame(), 0)

        assert isinstance(result, RiskManagementResult)
        assert result.should_stop_loss is False
