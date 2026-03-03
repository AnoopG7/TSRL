import pytest
from src.strategies.registry import StrategyRegistry, register_strategy
from src.strategies.base import BaseStrategy


class MockTestStrategy(BaseStrategy):
    """Mock strategy for testing registry"""

    @property
    def name(self) -> str:
        return "Mock Test Strategy"

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

    def generate_signals(self, data):
        import pandas as pd

        signals = data.copy()
        signals["signal"] = 0
        return signals


class TestStrategyRegistry:
    """Tests for StrategyRegistry class"""

    def setup_method(self):
        """Clear registry before each test"""
        StrategyRegistry._strategies = {}
        StrategyRegistry._initialized = False

    def test_register_strategy(self):
        StrategyRegistry.register("mock_test", MockTestStrategy)

        assert "mock_test" in StrategyRegistry.list_strategies()

    def test_get_strategy(self):
        StrategyRegistry.register("mock_test", MockTestStrategy)

        strategy_class = StrategyRegistry.get("mock_test")

        assert strategy_class is MockTestStrategy

    def test_get_strategy_not_found(self):
        result = StrategyRegistry.get("nonexistent")

        assert result is None

    def test_create_strategy(self):
        StrategyRegistry.register("mock_test", MockTestStrategy)

        strategy = StrategyRegistry.create("mock_test")

        assert isinstance(strategy, MockTestStrategy)
        assert strategy.name == "Mock Test Strategy"

    def test_create_strategy_with_params(self):
        StrategyRegistry.register("mock_test", MockTestStrategy)

        strategy = StrategyRegistry.create("mock_test", param1=50)

        assert strategy.get_parameter("param1") == 50

    def test_create_strategy_not_found(self):
        result = StrategyRegistry.create("nonexistent")

        assert result is None

    def test_list_strategies(self):
        StrategyRegistry.register("strategy1", MockTestStrategy)
        StrategyRegistry.register("strategy2", MockTestStrategy)

        strategies = StrategyRegistry.list_strategies()

        assert "strategy1" in strategies
        assert "strategy2" in strategies

    def test_list_strategies_empty(self):
        strategies = StrategyRegistry.list_strategies()

        assert len(strategies) == 0

    def test_get_strategy_info(self):
        StrategyRegistry.register("mock_test", MockTestStrategy)

        info = StrategyRegistry.get_strategy_info("mock_test")

        assert info is not None
        assert info["name"] == "Mock Test Strategy"
        assert info["version"] == "1.0.0"
        assert info["type"] == "test"

    def test_get_strategy_info_not_found(self):
        info = StrategyRegistry.get_strategy_info("nonexistent")

        assert info is None

    def test_get_all_strategy_info(self):
        StrategyRegistry.register("strategy1", MockTestStrategy)
        StrategyRegistry.register("strategy2", MockTestStrategy)

        all_info = StrategyRegistry.get_all_strategy_info()

        assert len(all_info) == 2

    def test_validate_parameters_valid(self):
        StrategyRegistry.register("mock_test", MockTestStrategy)

        valid, error = StrategyRegistry.validate_parameters(
            "mock_test", {"param1": 10, "param2": "test"}
        )

        assert valid is True
        assert error is None

    def test_validate_parameters_strategy_not_found(self):
        valid, error = StrategyRegistry.validate_parameters("nonexistent", {})

        assert valid is False
        assert "not found" in error

    def test_auto_discover_not_initialized(self):
        StrategyRegistry._initialized = False

        StrategyRegistry.auto_discover()

        assert StrategyRegistry._initialized is True

    def test_auto_discover_already_initialized(self):
        StrategyRegistry._initialized = True
        initial_count = len(StrategyRegistry._strategies)

        StrategyRegistry.auto_discover()

        assert len(StrategyRegistry._strategies) == initial_count


class TestRegisterStrategyDecorator:
    """Tests for register_strategy decorator"""

    def setup_method(self):
        StrategyRegistry._strategies = {}
        StrategyRegistry._initialized = False

    def test_register_decorator(self):
        @register_strategy("decorated_strategy")
        class DecoratedStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "Decorated Strategy"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Test decorated strategy"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data):
                import pandas as pd

                signals = data.copy()
                signals["signal"] = 0
                return signals

        assert "decorated_strategy" in StrategyRegistry.list_strategies()

    def test_register_decorator_with_version(self):
        @register_strategy("versioned_strategy", version="2.0.0")
        class VersionedStrategy(BaseStrategy):
            @property
            def name(self) -> str:
                return "Versioned Strategy"

            @property
            def version(self) -> str:
                return "2.0.0"

            @property
            def description(self) -> str:
                return "Test versioned strategy"

            @property
            def strategy_type(self) -> str:
                return "test"

            def generate_signals(self, data):
                import pandas as pd

                signals = data.copy()
                signals["signal"] = 0
                return signals

        strategy_class = StrategyRegistry.get("versioned_strategy")
        strategy = strategy_class()
        assert strategy.version == "2.0.0"
