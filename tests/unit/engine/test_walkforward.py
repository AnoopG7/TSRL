import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from src.engine.walkforward.walkforward import (
    WalkForwardAnalysis,
    WalkForwardResult,
    WalkForwardWindow,
)
from src.strategies.momentum.ema_crossover import EMACrossoverStrategy
from src.engine.backtest.engine import BacktestConfig


class TestWalkForwardAnalysis:
    """Tests for WalkForwardAnalysis"""

    def _make_data(self, periods: int) -> pd.DataFrame:
        """Helper to create OHLCV data for walkforward tests"""
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(periods) * 0.5)
        return pd.DataFrame(
            {
                "open": prices + np.random.randn(periods) * 0.1,
                "high": prices + np.abs(np.random.randn(periods)) * 0.5,
                "low": prices - np.abs(np.random.randn(periods)) * 0.5,
                "close": prices,
                "volume": np.random.randint(500000, 5000000, periods).astype(float),
            },
            index=pd.date_range("2022-01-01", periods=periods),
        )

    def test_analyzer_creation(self):
        analyzer = WalkForwardAnalysis()

        assert analyzer.engine is not None

    def test_run_analysis(self):
        """Test full walk-forward analysis"""
        analyzer = WalkForwardAnalysis()
        data = self._make_data(100)

        param_grid = {
            "fast_period": [5, 10],
            "slow_period": [20, 30],
        }
        result = analyzer.run(
            EMACrossoverStrategy,
            data,
            param_grid,
            train_days=50,
            test_days=20,
            step_days=20,
        )

        assert result is not None
        assert isinstance(result, WalkForwardResult)

    def test_run_analysis_with_custom_step(self):
        """Test walk-forward with custom step days"""
        analyzer = WalkForwardAnalysis()
        data = self._make_data(150)

        param_grid = {
            "fast_period": [5],
            "slow_period": [20],
        }
        result = analyzer.run(
            EMACrossoverStrategy,
            data,
            param_grid,
            train_days=50,
            test_days=25,
            step_days=25,
        )

        assert result is not None

    def test_insufficient_data(self):
        """Test with insufficient data for walk-forward"""
        analyzer = WalkForwardAnalysis()
        data = self._make_data(30)

        param_grid = {
            "fast_period": [5],
            "slow_period": [20],
        }

        with pytest.raises(ValueError, match="Insufficient data"):
            analyzer.run(
                EMACrossoverStrategy,
                data,
                param_grid,
                train_days=50,
                test_days=20,
            )

    def test_run_expanding_window(self):
        """Test expanding window walk-forward analysis"""
        analyzer = WalkForwardAnalysis()
        data = self._make_data(150)

        param_grid = {
            "fast_period": [5, 10],
            "slow_period": [20],
        }
        result = analyzer.run_expanding_window(
            EMACrossoverStrategy,
            data,
            param_grid,
            initial_train_days=50,
            test_days=25,
        )

        assert isinstance(result, WalkForwardResult)
        assert result.execution_time_ms >= 0
        assert len(result.windows) >= 2

    def test_run_rolling_window(self):
        """Test rolling window walk-forward analysis"""
        analyzer = WalkForwardAnalysis()
        data = self._make_data(150)

        param_grid = {
            "fast_period": [5, 10],
            "slow_period": [20],
        }
        result = analyzer.run_rolling_window(
            EMACrossoverStrategy,
            data,
            param_grid,
            train_days=50,
            test_days=25,
        )

        assert isinstance(result, WalkForwardResult)
        assert result.execution_time_ms >= 0
        assert len(result.windows) >= 2

    def test_to_dataframe(self):
        """Test converting WalkForwardResult to DataFrame"""
        analyzer = WalkForwardAnalysis()
        data = self._make_data(150)

        param_grid = {
            "fast_period": [5],
            "slow_period": [20],
        }
        result = analyzer.run(
            EMACrossoverStrategy,
            data,
            param_grid,
            train_days=50,
            test_days=25,
            step_days=25,
        )

        df = analyzer.to_dataframe(result)

        assert isinstance(df, pd.DataFrame)
        assert "train_start" in df.columns
        assert "train_end" in df.columns
        assert "test_start" in df.columns
        assert "test_end" in df.columns
        assert "test_return" in df.columns
        assert "test_trades" in df.columns

    def test_to_dataframe_empty(self):
        """Test to_dataframe with empty result"""
        analyzer = WalkForwardAnalysis()
        result = WalkForwardResult()

        df = analyzer.to_dataframe(result)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_evaluate_with_params_error_handling(self):
        """Test _evaluate_with_params handles strategy errors gracefully"""
        analyzer = WalkForwardAnalysis()
        data = self._make_data(50)

        class BadStrategy:
            def __init__(self, **kwargs):
                raise RuntimeError("Bad params")

        result = analyzer._evaluate_with_params(
            BadStrategy, {"bad_param": 999}, data, BacktestConfig()
        )

        assert result["success"] is False
        assert "error" in result
        assert result["total_return"] == 0.0
        assert result["total_trades"] == 0

    def test_aggregate_results_with_windows(self):
        """Test _aggregate_results with populated windows"""
        analyzer = WalkForwardAnalysis()

        windows = [
            WalkForwardWindow(
                train_start=datetime(2023, 1, 1),
                train_end=datetime(2023, 6, 1),
                test_start=datetime(2023, 6, 2),
                test_end=datetime(2023, 9, 1),
                best_params={"fast_period": 5, "slow_period": 20},
                train_metrics={"total_return": 0.1, "sharpe_ratio": 1.2},
                test_metrics={"total_return": 0.05, "sharpe_ratio": 0.8},
                test_return=0.05,
                test_trades=10,
            ),
            WalkForwardWindow(
                train_start=datetime(2023, 3, 1),
                train_end=datetime(2023, 9, 1),
                test_start=datetime(2023, 9, 2),
                test_end=datetime(2023, 12, 31),
                best_params={"fast_period": 10, "slow_period": 30},
                train_metrics={"total_return": 0.15, "sharpe_ratio": 1.5},
                test_metrics={"total_return": 0.08, "sharpe_ratio": 1.1},
                test_return=0.08,
                test_trades=15,
            ),
        ]

        result = analyzer._aggregate_results(windows)

        assert len(result.windows) == 2
        assert result.total_train_return == pytest.approx(0.25, rel=0.01)
        assert result.total_test_return == pytest.approx(0.13, rel=0.01)
        assert result.avg_train_sharpe == pytest.approx(1.35, rel=0.01)
        assert result.avg_test_sharpe == pytest.approx(0.95, rel=0.01)
        assert result.stability_score != 0.0
        assert result.combined_train_metrics["avg_return"] == pytest.approx(0.125, rel=0.01)
        assert result.combined_test_metrics["win_rate"] == pytest.approx(1.0, rel=0.01)


class TestWalkForwardResult:
    """Tests for WalkForwardResult"""

    def test_default_values(self):
        result = WalkForwardResult()

        assert result.windows == []
        assert result.total_train_return == 0.0
        assert result.total_test_return == 0.0
        assert result.stability_score == 0.0

    def test_combined_metrics_defaults(self):
        result = WalkForwardResult()

        assert result.combined_train_metrics == {}
        assert result.combined_test_metrics == {}
        assert result.avg_train_sharpe == 0.0
        assert result.avg_test_sharpe == 0.0
        assert result.execution_time_ms == 0.0


class TestWalkForwardWindow:
    """Tests for WalkForwardWindow dataclass"""

    def test_window_creation(self):
        window = WalkForwardWindow(
            train_start=datetime(2023, 1, 1),
            train_end=datetime(2023, 6, 1),
            test_start=datetime(2023, 6, 2),
            test_end=datetime(2023, 9, 1),
        )

        assert window.best_params == {}
        assert window.train_metrics == {}
        assert window.test_metrics == {}
        assert window.test_return == 0.0
        assert window.test_trades == 0
