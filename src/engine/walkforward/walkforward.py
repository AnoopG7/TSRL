import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Type

import pandas as pd
import numpy as np

from src.strategies.base import BaseStrategy
from src.engine.backtest.engine import BacktestEngine, BacktestConfig
from src.engine.optimizer.optimizer import GridSearchOptimizer, OptimizationResult

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardWindow:
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    best_params: dict = field(default_factory=dict)
    train_metrics: dict = field(default_factory=dict)
    test_metrics: dict = field(default_factory=dict)
    test_return: float = 0.0
    test_trades: int = 0


@dataclass
class WalkForwardResult:
    windows: list[WalkForwardWindow] = field(default_factory=list)
    combined_train_metrics: dict = field(default_factory=dict)
    combined_test_metrics: dict = field(default_factory=dict)
    total_train_return: float = 0.0
    total_test_return: float = 0.0
    avg_train_sharpe: float = 0.0
    avg_test_sharpe: float = 0.0
    stability_score: float = 0.0
    execution_time_ms: float = 0.0


class WalkForwardAnalysis:
    def __init__(self):
        self.engine = BacktestEngine()

    def run(
        self,
        strategy_class: Type[BaseStrategy],
        data: pd.DataFrame,
        param_grid: dict,
        train_days: int = 252,
        test_days: int = 63,
        step_days: Optional[int] = None,
        config: Optional[BacktestConfig] = None,
    ) -> WalkForwardResult:
        start_time = datetime.now()
        cfg = config or BacktestConfig()

        if step_days is None:
            step_days = test_days

        if len(data) < train_days:
            raise ValueError(f"Insufficient data: need {train_days} days for training")

        windows = []
        train_start_idx = 0
        test_start_idx = train_days

        iteration = 0
        while test_start_idx + test_days <= len(data):
            train_start = data.index[train_start_idx]
            train_end = data.index[train_start_idx + train_days - 1]
            test_start = data.index[test_start_idx]
            test_end = data.index[min(test_start_idx + test_days - 1, len(data) - 1)]

            train_slice = data.loc[train_start:train_end].copy()
            test_slice = data.loc[test_start:test_end].copy()

            logger.info(
                f"WFA Iteration {iteration + 1}: Train {train_start.date()} to {train_end.date()}, Test {test_start.date()} to {test_end.date()}"
            )

            optimizer = GridSearchOptimizer()
            optimizer.config.verbose = False

            opt_result = optimizer.optimize(strategy_class(), train_slice, param_grid, cfg)

            best_params = opt_result.best_params
            train_result = optimizer._evaluate_params(strategy_class, best_params, train_slice, cfg)

            test_result = self._evaluate_with_params(strategy_class, best_params, test_slice, cfg)

            window = WalkForwardWindow(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                best_params=best_params,
                train_metrics=train_result.get("metrics", {}),
                test_metrics=test_result.get("metrics", {}),
                test_return=test_result.get("total_return", 0.0),
                test_trades=test_result.get("total_trades", 0),
            )
            windows.append(window)

            train_start_idx += step_days
            test_start_idx += step_days
            iteration += 1

        result = self._aggregate_results(windows)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        result.execution_time_ms = execution_time

        return result

    def run_expanding_window(
        self,
        strategy_class: Type[BaseStrategy],
        data: pd.DataFrame,
        param_grid: dict,
        initial_train_days: int = 252,
        test_days: int = 63,
        config: Optional[BacktestConfig] = None,
    ) -> WalkForwardResult:
        start_time = datetime.now()
        cfg = config or BacktestConfig()

        windows = []
        train_start_idx = 0
        test_start_idx = initial_train_days

        iteration = 0
        while test_start_idx + test_days <= len(data):
            train_start = data.index[train_start_idx]
            train_end = data.index[test_start_idx - 1]
            test_start = data.index[test_start_idx]
            test_end = data.index[min(test_start_idx + test_days - 1, len(data) - 1)]

            train_slice = data.loc[train_start:train_end].copy()
            test_slice = data.loc[test_start:test_end].copy()

            logger.info(
                f"Expanding WFA {iteration + 1}: Train {train_start.date()} to {train_end.date()}, Test {test_start.date()} to {test_end.date()}"
            )

            optimizer = GridSearchOptimizer()
            optimizer.config.verbose = False

            opt_result = optimizer.optimize(strategy_class(), train_slice, param_grid, cfg)

            best_params = opt_result.best_params
            train_result = optimizer._evaluate_params(strategy_class, best_params, train_slice, cfg)

            test_result = self._evaluate_with_params(strategy_class, best_params, test_slice, cfg)

            window = WalkForwardWindow(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                best_params=best_params,
                train_metrics=train_result.get("metrics", {}),
                test_metrics=test_result.get("metrics", {}),
                test_return=test_result.get("total_return", 0.0),
                test_trades=test_result.get("total_trades", 0),
            )
            windows.append(window)

            test_start_idx += test_days
            iteration += 1

        result = self._aggregate_results(windows)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        result.execution_time_ms = execution_time

        return result

    def run_rolling_window(
        self,
        strategy_class: Type[BaseStrategy],
        data: pd.DataFrame,
        param_grid: dict,
        train_days: int = 252,
        test_days: int = 63,
        config: Optional[BacktestConfig] = None,
    ) -> WalkForwardResult:
        start_time = datetime.now()
        cfg = config or BacktestConfig()

        windows = []
        train_start_idx = 0

        iteration = 0
        while train_start_idx + train_days + test_days <= len(data):
            train_start = data.index[train_start_idx]
            train_end = data.index[train_start_idx + train_days - 1]
            test_start = data.index[train_start_idx + train_days]
            test_end = data.index[train_start_idx + train_days + test_days - 1]

            train_slice = data.loc[train_start:train_end].copy()
            test_slice = data.loc[test_start:test_end].copy()

            logger.info(
                f"Rolling WFA {iteration + 1}: Train {train_start.date()} to {train_end.date()}, Test {test_start.date()} to {test_end.date()}"
            )

            optimizer = GridSearchOptimizer()
            optimizer.config.verbose = False

            opt_result = optimizer.optimize(strategy_class(), train_slice, param_grid, cfg)

            best_params = opt_result.best_params
            train_result = optimizer._evaluate_params(strategy_class, best_params, train_slice, cfg)

            test_result = self._evaluate_with_params(strategy_class, best_params, test_slice, cfg)

            window = WalkForwardWindow(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                best_params=best_params,
                train_metrics=train_result.get("metrics", {}),
                test_metrics=test_result.get("metrics", {}),
                test_return=test_result.get("total_return", 0.0),
                test_trades=test_result.get("total_trades", 0),
            )
            windows.append(window)

            train_start_idx += test_days
            iteration += 1

        result = self._aggregate_results(windows)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        result.execution_time_ms = execution_time

        return result

    def _evaluate_with_params(
        self,
        strategy_class: type,
        params: dict,
        data: pd.DataFrame,
        config: BacktestConfig,
    ) -> dict:
        try:
            strategy = strategy_class(**params)
            result = self.engine.run(strategy, data, config)
            return {
                "metrics": result.metrics.to_dict(),
                "total_return": result.total_return,
                "total_trades": len(result.trades),
                "success": True,
            }
        except Exception as e:
            logger.warning(f"Failed to evaluate params {params}: {e}")
            return {
                "metrics": {},
                "total_return": 0.0,
                "total_trades": 0,
                "success": False,
                "error": str(e),
            }

    def _aggregate_results(self, windows: list[WalkForwardWindow]) -> WalkForwardResult:
        if not windows:
            return WalkForwardResult()

        train_returns = [w.train_metrics.get("total_return", 0) for w in windows]
        test_returns = [w.test_return for w in windows]
        train_sharpes = [w.train_metrics.get("sharpe_ratio", 0) for w in windows]
        test_sharpes = [w.test_metrics.get("sharpe_ratio", 0) for w in windows]

        test_returns_arr = np.array(test_returns)
        stability = 1.0 - np.std(test_returns_arr) / (np.abs(np.mean(test_returns_arr)) + 1e-8)

        combined_train = {
            "avg_return": np.mean(train_returns),
            "total_return": np.sum(train_returns),
            "avg_sharpe": np.mean(train_sharpes),
        }

        combined_test = {
            "avg_return": np.mean(test_returns),
            "total_return": np.sum(test_returns),
            "avg_sharpe": np.mean(test_sharpes),
            "win_rate": sum(1 for r in test_returns if r > 0) / len(test_returns)
            if test_returns
            else 0,
        }

        return WalkForwardResult(
            windows=windows,
            combined_train_metrics=combined_train,
            combined_test_metrics=combined_test,
            total_train_return=np.sum(train_returns),
            total_test_return=np.sum(test_returns),
            avg_train_sharpe=np.mean(train_sharpes),
            avg_test_sharpe=np.mean(test_sharpes),
            stability_score=stability,
        )

    def to_dataframe(self, result: WalkForwardResult) -> pd.DataFrame:
        rows = []
        for w in result.windows:
            rows.append(
                {
                    "train_start": w.train_start,
                    "train_end": w.train_end,
                    "test_start": w.test_start,
                    "test_end": w.test_end,
                    "test_return": w.test_return,
                    "test_trades": w.test_trades,
                    "train_sharpe": w.train_metrics.get("sharpe_ratio", 0),
                    "test_sharpe": w.test_metrics.get("sharpe_ratio", 0),
                    "train_return": w.train_metrics.get("total_return", 0),
                    "test_max_dd": w.test_metrics.get("max_drawdown_pct", 0),
                    **w.best_params,
                }
            )
        return pd.DataFrame(rows)
