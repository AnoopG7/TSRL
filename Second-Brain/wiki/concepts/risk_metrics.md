# Risk Metrics

Risk metrics are calculated by `src/analytics/risk_metrics.py` via the `RiskMetricsCalculator` class.

## Metrics Produced

| Metric | Description | Formula |
|--------|-------------|---------|
| **Total Return** | % gain/loss | `(final - initial) / initial` |
| **CAGR** | Compounded Annual Growth Rate | `(final/initial)^(1/years) - 1` |
| **Sharpe Ratio** | Risk-adjusted return | `√n × (mean - rf) / std` |
| **Sortino Ratio** | Downside-adjusted return | `√n × mean / downside_std` |
| **Max Drawdown** | Largest peak-to-trough | `min((peak - current) / peak)` |
| **Calmar Ratio** | Return / Max DD | `CAGR / max_drawdown` |
| **Win Rate** | % profitable trades | `wins / total_trades` |
| **Profit Factor** | Gross profit / gross loss | `Σ gains / Σ losses` |
| **Expectancy** | Average P&L | `total_pnl / n_trades` |
| **VaR 95%** | Value at Risk | `percentile(returns, 5)` |
| **CVaR 95%** | Conditional VaR | `mean(returns < VaR)` |
| **Kelly %** | Kelly Criterion | `W - (1-W)/R` |

## Calculation

```python
from src.analytics.risk_metrics import RiskMetricsCalculator

# From equity curve
returns = equity_curve.pct_change().dropna()
sharpe = RiskMetricsCalculator.calculate_sharpe_ratio(returns)
sortino = RiskMetricsCalculator.calculate_sortino_ratio(returns)
max_dd, peak, trough = RiskMetricsCalculator.calculate_max_drawdown(equity_curve)

# From trades
win_rate = RiskMetricsCalculator.calculate_win_rate(trades)
profit_factor = RiskMetricsCalculator.calculate_profit_factor(trades)
trade_stats = RiskMetricsCalculator.calculate_trade_statistics(trades)
```

## Time-Varying Metrics

| Metric | Window | Description |
|--------|--------|-------------|
| Rolling Sharpe | 60-day | Time-varying Sharpe |
| Rolling Max DD | 60-day | Rolling drawdown |

## Monthly Returns

```python
monthly = RiskMetricsCalculator.calculate_monthly_returns(returns)
# Returns DataFrame: rows=years, columns=months (1-12)
```

## Trade Statistics

```python
stats = {
    "total_trades": int,
    "winning_trades": int,
    "losing_trades": int,
    "win_rate": float,
    "avg_win": float,
    "avg_loss": float,
    "largest_win": float,
    "largest_loss": float,
    "max_consecutive_wins": int,
    "max_consecutive_losses": int,
}
```

## Related

- [[Portfolio Metrics]] — Portfolio-level metrics
- [[Backtesting]] — How metrics are produced
- [[EMA Crossover]] — Strategy that produces these metrics