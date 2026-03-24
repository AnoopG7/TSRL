import pytest
import pandas as pd
import numpy as np
from src.analytics.risk_metrics import RiskMetricsCalculator, DrawdownAnalyzer


class TestRiskMetricsCalculator:
    """Tests for RiskMetricsCalculator"""

    def test_calculate_total_return_basic(self):
        result = RiskMetricsCalculator.calculate_total_return(100000, 110000)
        assert result == 0.1

    def test_calculate_total_return_negative(self):
        result = RiskMetricsCalculator.calculate_total_return(100000, 90000)
        assert result == -0.1

    def test_calculate_total_return_zero_initial(self):
        result = RiskMetricsCalculator.calculate_total_return(0, 100000)
        assert result == 0.0

    def test_calculate_cagr_basic(self):
        result = RiskMetricsCalculator.calculate_cagr(100000, 110000, 252)
        assert abs(result - 0.1) < 0.01

    def test_calculate_cagr_zero_initial(self):
        result = RiskMetricsCalculator.calculate_cagr(0, 100000, 252)
        assert result == 0.0

    def test_calculate_cagr_zero_days(self):
        result = RiskMetricsCalculator.calculate_cagr(100000, 110000, 0)
        assert result == 0.0

    def test_calculate_sharpe_ratio_basic(self):
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
        result = RiskMetricsCalculator.calculate_sharpe_ratio(returns)
        assert isinstance(result, float)

    def test_calculate_sharpe_ratio_zero_std(self):
        returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        result = RiskMetricsCalculator.calculate_sharpe_ratio(returns)
        assert result == 0.0

    def test_calculate_sharpe_ratio_single_value(self):
        returns = pd.Series([0.01])
        result = RiskMetricsCalculator.calculate_sharpe_ratio(returns)
        assert result == 0.0

    def test_calculate_sortino_ratio_basic(self):
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
        result = RiskMetricsCalculator.calculate_sortino_ratio(returns)
        assert isinstance(result, float)

    def test_calculate_sortino_ratio_no_downside(self):
        returns = pd.Series([0.01, 0.02, 0.015, 0.01])
        result = RiskMetricsCalculator.calculate_sortino_ratio(returns)
        assert result == 0.0

    def test_calculate_sortino_ratio_single_value(self):
        returns = pd.Series([0.01])
        result = RiskMetricsCalculator.calculate_sortino_ratio(returns)
        assert result == 0.0

    def test_calculate_max_drawdown_basic(self):
        equity = pd.Series([100, 110, 105, 95, 98, 100])
        max_dd, start, end = RiskMetricsCalculator.calculate_max_drawdown(equity)
        assert max_dd > 0
        assert max_dd < 0.2

    def test_calculate_max_drawdown_single_point(self):
        equity = pd.Series([100])
        max_dd, start, end = RiskMetricsCalculator.calculate_max_drawdown(equity)
        assert max_dd == 0.0

    def test_calculate_win_rate_all_winning(self):
        trades = [
            {"pnl": 100},
            {"pnl": 50},
            {"pnl": 75},
        ]
        result = RiskMetricsCalculator.calculate_win_rate(trades)
        assert result == 1.0

    def test_calculate_win_rate_all_losing(self):
        trades = [
            {"pnl": -100},
            {"pnl": -50},
            {"pnl": -75},
        ]
        result = RiskMetricsCalculator.calculate_win_rate(trades)
        assert result == 0.0

    def test_calculate_win_rate_mixed(self):
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 75},
            {"pnl": -25},
        ]
        result = RiskMetricsCalculator.calculate_win_rate(trades)
        assert result == 0.5

    def test_calculate_win_rate_empty(self):
        trades = []
        result = RiskMetricsCalculator.calculate_win_rate(trades)
        assert result == 0.0

    def test_calculate_profit_factor_with_wins_and_losses(self):
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 75},
            {"pnl": -25},
        ]
        result = RiskMetricsCalculator.calculate_profit_factor(trades)
        assert result == 1.75 / 0.75

    def test_calculate_profit_factor_no_losses(self):
        trades = [
            {"pnl": 100},
            {"pnl": 50},
            {"pnl": 75},
        ]
        result = RiskMetricsCalculator.calculate_profit_factor(trades)
        # Capped at 100.0 to avoid infinity propagation in downstream calculations
        assert result == 100.0

    def test_calculate_profit_factor_no_wins(self):
        trades = [
            {"pnl": -100},
            {"pnl": -50},
            {"pnl": -75},
        ]
        result = RiskMetricsCalculator.calculate_profit_factor(trades)
        assert result == 0.0

    def test_calculate_profit_factor_empty(self):
        trades = []
        result = RiskMetricsCalculator.calculate_profit_factor(trades)
        assert result == 0.0

    def test_calculate_expectancy_basic(self):
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 75},
            {"pnl": -25},
        ]
        result = RiskMetricsCalculator.calculate_expectancy(trades)
        # (100 - 50 + 75 - 25) / 4 = 25
        assert result == 25.0

    def test_calculate_expectancy_empty(self):
        trades = []
        result = RiskMetricsCalculator.calculate_expectancy(trades)
        assert result == 0.0

    def test_calculate_calmar_ratio_basic(self):
        result = RiskMetricsCalculator.calculate_calmar_ratio(0.2, 0.1)
        assert result == 2.0

    def test_calculate_calmar_ratio_zero_drawdown(self):
        result = RiskMetricsCalculator.calculate_calmar_ratio(0.2, 0.0)
        assert result == 0.0

    def test_calculate_rolling_sharpe(self):
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        returns = pd.Series(np.random.randn(100) * 0.02, index=dates)
        result = RiskMetricsCalculator.calculate_rolling_sharpe(returns, window=20)
        assert len(result) == 100

    def test_calculate_rolling_max_drawdown(self):
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        equity = pd.Series(100 + np.random.randn(100).cumsum(), index=dates)
        result = RiskMetricsCalculator.calculate_rolling_max_drawdown(equity, window=20)
        assert len(result) == 100

    def test_calculate_monthly_returns(self):
        dates = pd.date_range(start="2023-01-01", periods=365, freq="D")
        returns = pd.Series(np.random.randn(365) * 0.02, index=dates)
        result = RiskMetricsCalculator.calculate_monthly_returns(returns)
        assert isinstance(result, pd.DataFrame)

    def test_calculate_monthly_returns_empty(self):
        returns = pd.Series([])
        result = RiskMetricsCalculator.calculate_monthly_returns(returns)
        assert result.empty

    def test_calculate_trade_statistics_basic(self):
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 75},
            {"pnl": -25},
        ]
        result = RiskMetricsCalculator.calculate_trade_statistics(trades)

        assert result["total_trades"] == 4
        assert result["winning_trades"] == 2
        assert result["losing_trades"] == 2
        assert result["win_rate"] == 0.5

    def test_calculate_trade_statistics_empty(self):
        trades = []
        result = RiskMetricsCalculator.calculate_trade_statistics(trades)
        assert result == {}

    def test_calculate_trade_statistics_all_winners(self):
        trades = [{"pnl": 100}, {"pnl": 50}, {"pnl": 75}]
        result = RiskMetricsCalculator.calculate_trade_statistics(trades)

        assert result["winning_trades"] == 3
        assert result["losing_trades"] == 0
        assert result["largest_win"] == 100

    def test_calculate_trade_statistics_all_losers(self):
        trades = [{"pnl": -100}, {"pnl": -50}, {"pnl": -75}]
        result = RiskMetricsCalculator.calculate_trade_statistics(trades)

        assert result["winning_trades"] == 0
        assert result["losing_trades"] == 3
        assert result["largest_loss"] == -100


class TestDrawdownAnalyzer:
    """Tests for DrawdownAnalyzer"""

    def test_get_drawdown_periods_basic(self):
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        equity = pd.Series(
            [100, 110, 105, 95, 98, 100, 112, 108, 115, 120], index=dates
        )

        periods = DrawdownAnalyzer.get_drawdown_periods(equity)

        assert len(periods) > 0
        for p in periods:
            assert "start" in p
            assert "end" in p
            assert "duration" in p
            assert "drawdown" in p
            assert p["drawdown"] > 0

    def test_get_drawdown_periods_empty(self):
        equity = pd.Series([100])
        periods = DrawdownAnalyzer.get_drawdown_periods(equity)
        assert periods == []

    def test_get_drawdown_periods_no_drawdown(self):
        dates = pd.date_range(start="2023-01-01", periods=5, freq="D")
        equity = pd.Series([100, 101, 102, 103, 104], index=dates)

        periods = DrawdownAnalyzer.get_drawdown_periods(equity)

        assert periods == []

    def test_calculate_recovery_time_basic(self):
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        equity = pd.Series(
            [100, 110, 105, 95, 98, 100, 105, 110, 115, 120], index=dates
        )

        # Drawdown starts at peak (110 on Jan 2), recovery back to 110 on Jan 8
        result = DrawdownAnalyzer.calculate_recovery_time(equity, dates[1])
        assert result is not None
        assert result > 0

    def test_calculate_recovery_time_no_recovery(self):
        dates = pd.date_range(start="2023-01-01", periods=5, freq="D")
        equity = pd.Series([100, 110, 90, 85, 80], index=dates)

        # Start at peak 110, never recovers
        result = DrawdownAnalyzer.calculate_recovery_time(equity, dates[1])
        assert result is None

    def test_calculate_recovery_time_not_in_index(self):
        dates = pd.date_range(start="2023-01-01", periods=5, freq="D")
        equity = pd.Series([100, 110, 90, 85, 80], index=dates)

        result = DrawdownAnalyzer.calculate_recovery_time(
            equity, pd.Timestamp("2024-01-01")
        )
        assert result is None
