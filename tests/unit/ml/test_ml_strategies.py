import pytest
import pandas as pd
import numpy as np
from src.ml.strategies.ml_strategies import MLRandomForestStrategy, MLGradientBoostingStrategy


class TestMLRandomForestStrategy:
    def test_initialization(self):
        strategy = MLRandomForestStrategy(
            n_estimators=100, max_depth=5, lookback=50, prediction_horizon=5
        )

        assert strategy.name == "ml_random_forest"
        assert strategy.version == "1.0.0"
        assert strategy.strategy_type == "ml"
        assert strategy._n_estimators == 100
        assert strategy._max_depth == 5
        assert strategy._lookback == 50
        assert strategy._prediction_horizon == 5

    def test_default_parameters(self):
        strategy = MLRandomForestStrategy()

        assert "n_estimators" in strategy._params
        assert "max_depth" in strategy._params
        assert "lookback" in strategy._params
        assert "prediction_horizon" in strategy._params

        assert strategy._params["n_estimators"].value == 100
        assert strategy._params["max_depth"].value == 5
        assert strategy._params["lookback"].value == 50
        assert strategy._params["prediction_horizon"].value == 5

    def test_get_requirements(self):
        strategy = MLRandomForestStrategy()
        requirements = strategy.get_requirements()

        assert isinstance(requirements, list)
        assert "open" in requirements
        assert "high" in requirements
        assert "low" in requirements
        assert "close" in requirements
        assert "volume" in requirements

    def test_before_backtest_insufficient_data(self, sample_ohlcv_data):
        strategy = MLRandomForestStrategy(lookback=100, prediction_horizon=20)

        result = strategy.before_backtest(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert not strategy._is_fitted

    def test_before_backtest_with_sufficient_data(self, sample_ohlcv_data_large):
        strategy = MLRandomForestStrategy(
            n_estimators=10, max_depth=3, lookback=50, prediction_horizon=5
        )

        result = strategy.before_backtest(sample_ohlcv_data_large)

        assert isinstance(result, pd.DataFrame)

    def test_generate_signals_not_fitted(self, sample_ohlcv_data):
        strategy = MLRandomForestStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert "signal" in signals.columns
        assert "close" in signals.columns
        assert (signals["signal"] == 0).all()

    def test_generate_signals_after_fit(self, sample_ohlcv_data_large):
        strategy = MLRandomForestStrategy(
            n_estimators=10, max_depth=3, lookback=50, prediction_horizon=5
        )

        strategy.before_backtest(sample_ohlcv_data_large)
        signals = strategy.generate_signals(sample_ohlcv_data_large)

        assert "signal" in signals.columns

    def test_generate_features(self, sample_ohlcv_data):
        strategy = MLRandomForestStrategy()
        features = strategy._generate_features(sample_ohlcv_data)

        assert isinstance(features, pd.DataFrame)
        assert len(features) > 0

    def test_generate_labels(self, sample_ohlcv_data):
        strategy = MLRandomForestStrategy(prediction_horizon=5)
        labels = strategy._generate_labels(sample_ohlcv_data)

        assert isinstance(labels, pd.Series)
        assert len(labels) == len(sample_ohlcv_data)
        assert set(labels.dropna().unique()).issubset({-1, 0, 1})

    def test_strategy_registered(self):
        from src.strategies.registry import StrategyRegistry

        registry = StrategyRegistry()
        strategy = registry.create("ml_random_forest")

        assert strategy is not None
        assert strategy.name == "ml_random_forest"


class TestMLGradientBoostingStrategy:
    def test_initialization(self):
        strategy = MLGradientBoostingStrategy(
            n_estimators=100, max_depth=3, learning_rate=0.1, lookback=50, prediction_horizon=5
        )

        assert strategy.name == "ml_gradient_boosting"
        assert strategy.version == "1.0.0"
        assert strategy.strategy_type == "ml"
        assert strategy._n_estimators == 100
        assert strategy._max_depth == 3
        assert strategy._learning_rate == 0.1
        assert strategy._lookback == 50
        assert strategy._prediction_horizon == 5

    def test_default_parameters(self):
        strategy = MLGradientBoostingStrategy()

        assert "n_estimators" in strategy._params
        assert "max_depth" in strategy._params
        assert "learning_rate" in strategy._params
        assert "lookback" in strategy._params
        assert "prediction_horizon" in strategy._params

        assert strategy._params["n_estimators"].value == 100
        assert strategy._params["max_depth"].value == 3
        assert strategy._params["learning_rate"].value == 0.1
        assert strategy._params["lookback"].value == 50
        assert strategy._params["prediction_horizon"].value == 5

    def test_get_requirements(self):
        strategy = MLGradientBoostingStrategy()
        requirements = strategy.get_requirements()

        assert isinstance(requirements, list)
        assert "open" in requirements
        assert "high" in requirements
        assert "low" in requirements
        assert "close" in requirements
        assert "volume" in requirements

    def test_before_backtest_insufficient_data(self, sample_ohlcv_data):
        strategy = MLGradientBoostingStrategy(lookback=100, prediction_horizon=20)

        result = strategy.before_backtest(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert not strategy._is_fitted

    def test_before_backtest_with_sufficient_data(self, sample_ohlcv_data_large):
        strategy = MLGradientBoostingStrategy(
            n_estimators=10, max_depth=2, learning_rate=0.1, lookback=50, prediction_horizon=5
        )

        result = strategy.before_backtest(sample_ohlcv_data_large)

        assert isinstance(result, pd.DataFrame)

    def test_generate_signals_not_fitted(self, sample_ohlcv_data):
        strategy = MLGradientBoostingStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert "signal" in signals.columns
        assert "close" in signals.columns
        assert (signals["signal"] == 0).all()

    def test_generate_signals_after_fit(self, sample_ohlcv_data_large):
        strategy = MLGradientBoostingStrategy(
            n_estimators=10, max_depth=2, learning_rate=0.1, lookback=50, prediction_horizon=5
        )

        strategy.before_backtest(sample_ohlcv_data_large)
        signals = strategy.generate_signals(sample_ohlcv_data_large)

        assert "signal" in signals.columns

    def test_generate_features(self, sample_ohlcv_data):
        strategy = MLGradientBoostingStrategy()
        features = strategy._generate_features(sample_ohlcv_data)

        assert isinstance(features, pd.DataFrame)
        assert len(features) > 0

    def test_generate_labels(self, sample_ohlcv_data):
        strategy = MLGradientBoostingStrategy(prediction_horizon=5)
        labels = strategy._generate_labels(sample_ohlcv_data)

        assert isinstance(labels, pd.Series)
        assert len(labels) == len(sample_ohlcv_data)
        assert set(labels.dropna().unique()).issubset({-1, 0, 1})

    def test_strategy_in_registry(self):
        from src.strategies.registry import StrategyRegistry

        strategy = StrategyRegistry.create("ml_gradient_boosting")

        assert strategy is not None
        assert isinstance(strategy, MLGradientBoostingStrategy)

    def test_different_learning_rates(self, sample_ohlcv_data_large):
        for lr in [0.01, 0.05, 0.2, 0.5]:
            strategy = MLGradientBoostingStrategy(
                n_estimators=10, max_depth=2, learning_rate=lr, lookback=50, prediction_horizon=5
            )

            result = strategy.before_backtest(sample_ohlcv_data_large)
            assert isinstance(result, pd.DataFrame)
