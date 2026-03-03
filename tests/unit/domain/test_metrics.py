import pytest
import pandas as pd
import numpy as np
from src.domain.entities.metrics import RiskMetrics


class TestRiskMetrics:
    """Tests for RiskMetrics dataclass"""

    def test_risk_metrics_default_values(self):
        metrics = RiskMetrics()

        assert metrics.total_return == 0.0
        assert metrics.cagr == 0.0
        assert metrics.sharpe_ratio == 0.0
        assert metrics.sortino_ratio == 0.0
        assert metrics.max_drawdown == 0.0
        assert metrics.win_rate == 0.0

    def test_risk_metrics_is_profitable_positive(self):
        metrics = RiskMetrics(total_return=0.1)
        assert metrics.is_profitable is True

    def test_risk_metrics_is_profitable_negative(self):
        metrics = RiskMetrics(total_return=-0.1)
        assert metrics.is_profitable is False

    def test_risk_metrics_is_profitable_zero(self):
        metrics = RiskMetrics(total_return=0.0)
        assert metrics.is_profitable is False

    def test_risk_metrics_avg_win_pct_with_winners(self):
        metrics = RiskMetrics(winning_trades=5, avg_win=100.0)
        assert metrics.avg_win_pct == 100.0

    def test_risk_metrics_avg_win_pct_no_winners(self):
        metrics = RiskMetrics(winning_trades=0)
        assert metrics.avg_win_pct == 0.0

    def test_risk_metrics_avg_loss_pct_with_losers(self):
        metrics = RiskMetrics(losing_trades=5, avg_loss=-50.0)
        assert metrics.avg_loss_pct == -50.0

    def test_risk_metrics_avg_loss_pct_no_losers(self):
        metrics = RiskMetrics(losing_trades=0)
        assert metrics.avg_loss_pct == 0.0

    def test_risk_metrics_risk_of_ruin_zero_trades(self):
        metrics = RiskMetrics(total_trades=0, win_rate=0.5, profit_factor=2.0)
        assert metrics.risk_of_ruin == 0.0

    def test_risk_metrics_risk_of_ruin_zero_win_rate(self):
        metrics = RiskMetrics(total_trades=10, win_rate=0.0, profit_factor=2.0)
        assert metrics.risk_of_ruin == 1.0

    def test_risk_metrics_risk_of_ruin_perfect_win_rate(self):
        metrics = RiskMetrics(total_trades=10, win_rate=1.0, profit_factor=2.0)
        assert metrics.risk_of_ruin == 0.0

    def test_risk_metrics_risk_of_ruin_profit_factor_1(self):
        metrics = RiskMetrics(total_trades=10, win_rate=0.5, profit_factor=1.0)
        assert metrics.risk_of_ruin == 1.0

    def test_risk_metrics_return_to_drawdown(self):
        metrics = RiskMetrics(total_return=0.2, max_drawdown=0.1)
        assert metrics.return_to_drawdown == 2.0

    def test_risk_metrics_return_to_drawdown_no_drawdown(self):
        metrics = RiskMetrics(total_return=0.2, max_drawdown=0.0)
        assert metrics.return_to_drawdown == 0.0

    def test_risk_metrics_recovery_factor(self):
        metrics = RiskMetrics(total_return=0.2, max_drawdown=0.1)
        assert metrics.recovery_factor == 2.0

    def test_risk_metrics_recovery_factor_no_drawdown(self):
        metrics = RiskMetrics(total_return=0.2, max_drawdown=0.0)
        assert metrics.recovery_factor == 0.0

    def test_risk_metrics_to_dict(self):
        metrics = RiskMetrics(
            total_return=0.1,
            cagr=0.08,
            sharpe_ratio=1.5,
            max_drawdown=0.05,
            win_rate=0.6,
        )

        d = metrics.to_dict()

        assert d["total_return"] == 0.1
        assert d["cagr"] == 0.08
        assert d["sharpe_ratio"] == 1.5
        assert d["max_drawdown"] == 0.05
        assert d["win_rate"] == 0.6

    def test_risk_metrics_risk_adjusted_return(self):
        metrics = RiskMetrics(total_return=0.2, volatility=0.15)
        assert metrics.risk_adjusted_return == pytest.approx(1.333, rel=0.01)

    def test_risk_metrics_risk_adjusted_return_zero_volatility(self):
        metrics = RiskMetrics(total_return=0.2, volatility=0.0)
        assert metrics.risk_adjusted_return == 0.0

    def test_risk_metrics_win_loss_ratio(self):
        metrics = RiskMetrics(avg_win=100.0, avg_loss=-50.0)
        assert metrics.win_loss_ratio == 2.0

    def test_risk_metrics_win_loss_ratio_zero_loss(self):
        metrics = RiskMetrics(avg_win=100.0, avg_loss=0.0)
        assert metrics.win_loss_ratio == 0.0

    def test_risk_metrics_from_trades_empty(self):
        trades = []
        returns = pd.Series([0.01, -0.005, 0.02])
        metrics = RiskMetrics.from_trades(trades, 100000, returns)

        assert metrics.total_trades == 0

    def test_risk_metrics_from_trades_with_winners_and_losers(self):
        trades = [
            {"pnl": 100.0},
            {"pnl": -50.0},
            {"pnl": 75.0},
            {"pnl": -25.0},
        ]
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        returns = pd.Series(np.random.randn(100) * 0.02, index=dates)

        metrics = RiskMetrics.from_trades(trades, 100000, returns)

        assert metrics.total_trades == 4
        assert metrics.winning_trades == 2
        assert metrics.losing_trades == 2
        assert metrics.win_rate == 0.5

    def test_risk_metrics_from_trades_all_winners(self):
        trades = [
            {"pnl": 100.0},
            {"pnl": 50.0},
            {"pnl": 75.0},
        ]
        returns = pd.Series([0.01] * 100)

        metrics = RiskMetrics.from_trades(trades, 100000, returns)

        assert metrics.winning_trades == 3
        assert metrics.losing_trades == 0
        assert metrics.win_rate == 1.0

    def test_risk_metrics_from_trades_all_losers(self):
        trades = [
            {"pnl": -100.0},
            {"pnl": -50.0},
            {"pnl": -75.0},
        ]
        returns = pd.Series([-0.01] * 100)

        metrics = RiskMetrics.from_trades(trades, 100000, returns)

        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 3
        assert metrics.win_rate == 0.0
