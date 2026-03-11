import pytest
import pandas as pd
import numpy as np
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import List

from src.engine.backtest.engine import BacktestEngine, BacktestConfig
from src.strategies.momentum.ema_crossover import EMACrossoverStrategy
from src.domain.entities.trade import Trade, TradeSide
from src.analytics.risk_metrics import RiskMetricsCalculator


class TestPerformance:
    @pytest.fixture
    def large_ohlcv_data(self):
        np.random.seed(42)
        dates = pd.date_range(start="2020-01-01", periods=5000, freq="D")
        prices = 100 + np.cumsum(np.random.randn(5000) * 0.5)
        
        return pd.DataFrame({
            "open": prices + np.random.randn(5000) * 0.2,
            "high": prices + np.abs(np.random.randn(5000)) * 0.5,
            "low": prices - np.abs(np.random.randn(5000)) * 0.5,
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, 5000).astype(float)
        }, index=dates)

    @pytest.fixture
    def medium_ohlcv_data(self):
        np.random.seed(42)
        dates = pd.date_range(start="2022-01-01", periods=1000, freq="D")
        prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)
        
        return pd.DataFrame({
            "open": prices + np.random.randn(1000) * 0.2,
            "high": prices + np.abs(np.random.randn(1000)) * 0.5,
            "low": prices - np.abs(np.random.randn(1000) * 0.5),
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, 1000).astype(float)
        }, index=dates)

    def test_backtest_5000_bars_performance(self, large_ohlcv_data):
        strategy = EMACrossoverStrategy(fast_period=10, slow_period=30)
        config = BacktestConfig(
            initial_capital=100000,
            commission=0.001,
            slippage=0.0005,
        )
        engine = BacktestEngine(config)
        
        start_time = time.time()
        result = engine.run(strategy, large_ohlcv_data)
        elapsed = time.time() - start_time
        
        assert elapsed < 5.0, f"Backtest took {elapsed:.2f}s, should be < 5s for 5000 bars"
        assert result is not None

    def test_backtest_1000_bars_performance(self, medium_ohlcv_data):
        strategy = EMACrossoverStrategy(fast_period=10, slow_period=30)
        config = BacktestConfig(
            initial_capital=100000,
            commission=0.001,
            slippage=0.0005,
        )
        engine = BacktestEngine(config)
        
        start_time = time.time()
        result = engine.run(strategy, medium_ohlcv_data)
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0, f"Backtest took {elapsed:.2f}s, should be < 1s for 1000 bars"
        assert result is not None

    def test_risk_metrics_calculation_performance(self, large_ohlcv_data):
        returns = large_ohlcv_data["close"].pct_change().dropna()
        
        start_time = time.time()
        
        sharpe = RiskMetricsCalculator.calculate_sharpe_ratio(returns)
        sortino = RiskMetricsCalculator.calculate_sortino_ratio(returns)
        max_dd = RiskMetricsCalculator.calculate_max_drawdown(returns)
        
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0, f"Risk metrics took {elapsed:.2f}s, should be < 1s"
        assert np.isfinite(sharpe)

    def test_trade_creation_performance(self):
        start_time = time.time()
        
        trades = []
        for i in range(10000):
            trade = Trade(
                symbol="TEST",
                entry_time=datetime.now(),
                entry_price=100.0 + np.random.randn() * 10,
                quantity=100,
                side=TradeSide.LONG,
                exit_time=datetime.now(),
                exit_price=100.0 + np.random.randn() * 10,
            )
            trades.append(trade)
        
        elapsed = time.time() - start_time
        
        assert elapsed < 2.0, f"Creating 10000 trades took {elapsed:.2f}s, should be < 2s"
        assert len(trades) == 10000

    def test_memory_usage_backtest(self, large_ohlcv_data):
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024
        
        strategy = EMACrossoverStrategy(fast_period=10, slow_period=30)
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)
        
        result = engine.run(strategy, large_ohlcv_data)
        
        mem_after = process.memory_info().rss / 1024 / 1024
        mem_used = mem_after - mem_before
        
        assert mem_used < 500, f"Memory usage {mem_used:.2f}MB exceeds 500MB limit"

    def test_equity_curve_generation_performance(self, large_ohlcv_data):
        initial_capital = 100000
        returns = large_ohlcv_data["close"].pct_change().dropna()
        
        start_time = time.time()
        
        equity = [initial_capital]
        for r in returns:
            equity.append(equity[-1] * (1 + r))
        
        elapsed = time.time() - start_time
        
        assert elapsed < 0.5, f"Equity curve generation took {elapsed:.2f}s"
        assert len(equity) == len(returns) + 1

    def test_strategy_signal_generation_performance(self, large_ohlcv_data):
        strategy = EMACrossoverStrategy(fast_period=10, slow_period=30)
        
        start_time = time.time()
        
        signals = strategy.generate_signals(large_ohlcv_data)
        
        elapsed = time.time() - start_time
        
        assert elapsed < 2.0, f"Signal generation took {elapsed:.2f}s, should be < 2s"
        assert "signal" in signals.columns

    def test_repeated_backtest_consistency(self, medium_ohlcv_data):
        strategy = EMACrossoverStrategy(fast_period=10, slow_period=30)
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)
        
        results = []
        for _ in range(5):
            result = engine.run(strategy, medium_ohlcv_data)
            results.append(result.total_return)
        
        assert len(set(results)) == 1, "Repeated backtests should give consistent results"


class TestScalability:
    def test_linear_scaling_with_data_points(self):
        times = []
        for n_bars in [100, 500, 1000, 2000]:
            np.random.seed(42)
            dates = pd.date_range(start="2020-01-01", periods=n_bars, freq="D")
            prices = 100 + np.cumsum(np.random.randn(n_bars) * 0.5)
            
            data = pd.DataFrame({
                "open": prices + np.random.randn(n_bars) * 0.2,
                "high": prices + np.abs(np.random.randn(n_bars)) * 0.5,
                "low": prices - np.abs(np.random.randn(n_bars)) * 0.5,
                "close": prices,
                "volume": np.random.randint(1000000, 10000000, n_bars).astype(float)
            }, index=dates)
            
            strategy = EMACrossoverStrategy(fast_period=10, slow_period=30)
            config = BacktestConfig(initial_capital=100000)
            engine = BacktestEngine(config)
            
            start_time = time.time()
            engine.run(strategy, data)
            elapsed = time.time() - start_time
            times.append(elapsed)
        
        for i in range(1, len(times)):
            scaling_factor = times[i] / times[i-1]
            assert scaling_factor < 4, f"Time scaling from {times[i-1]:.3f}s to {times[i]:.3f}s is not linear"

    def test_strategy_parameter_scalability(self):
        data_sizes = [100, 500, 1000]
        
        for n_bars in data_sizes:
            np.random.seed(42)
            dates = pd.date_range(start="2020-01-01", periods=n_bars, freq="D")
            prices = 100 + np.cumsum(np.random.randn(n_bars) * 0.5)
            
            data = pd.DataFrame({
                "open": prices + np.random.randn(n_bars) * 0.2,
                "high": prices + np.abs(np.random.randn(n_bars)) * 0.5,
                "low": prices - np.abs(np.random.randn(n_bars) * 0.5),
                "close": prices,
                "volume": np.random.randint(1000000, 10000000, n_bars).astype(float)
            }, index=dates)
            
            strategy = EMACrossoverStrategy(fast_period=10, slow_period=30)
            
            start_time = time.time()
            signals = strategy.generate_signals(data)
            elapsed = time.time() - start_time
            
            assert elapsed < n_bars / 500, f"Signal gen took {elapsed:.2f}s for {n_bars} bars"
