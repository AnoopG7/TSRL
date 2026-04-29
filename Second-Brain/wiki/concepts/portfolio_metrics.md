# Portfolio Metrics

Portfolio-level metrics are calculated by `src/analytics/portfolio_metrics.py` via the `PortfolioMetricsCalculator` class.

## Metrics Produced

| Metric | Description | Formula |
|--------|-------------|---------|
| **Correlation Matrix** | Pairwise asset correlations | `returns.corr()` |
| **Average Correlation** | Mean off-diagonal correlation | `mean(corr matrix)` |
| **Portfolio Return** | Weighted asset returns | `Σ(weight × return)` |
| **Portfolio Volatility** | Weighted portfolio std | `√(w' × Σ × w)` |
| **Beta** | Market sensitivity | `cov(port, bench) / var(bench)` |
| **Alpha** | Excess return | `port_return - β × bench_return` |
| **Tracking Error** | Active return deviation | `std(port - bench)` |
| **Information Ratio** | Alpha / tracking error | `α / TE` |
| **Risk Contribution** | Marginal risk per asset | `weight × marginal_var` |

## Calculation

```python
from src.analytics.portfolio_metrics import PortfolioMetricsCalculator

metrics = PortfolioMetricsCalculator.calculate_all(
    asset_returns={"AAPL": returns_aapl, "MSFT": returns_msft},
    weights={"AAPL": 0.5, "MSFT": 0.5},
    benchmark_returns=benchmark_returns,  # Optional
    risk_free_rate=0.0,
)
```

## Output Fields

```python
@dataclass
class PortfolioMetrics:
    correlation_matrix: dict       # {symbol: {symbol: correlation}}
    avg_correlation: float        # Mean off-diagonal correlation
    portfolio_return: float       # Annualized return
    portfolio_volatility: float   # Annualized std deviation
    beta: float                  # Market beta
    alpha: float                # Jensen's alpha
    tracking_error: float       # Active return std
    information_ratio: float    # Alpha / tracking error
    risk_contribution: dict     # Per-asset risk contribution
    risk_parity_weights: dict   # Equal risk contribution weights
```

## Usage in Backtests

Multi-symbol portfolio backtests use the PortfolioEngine (`src/engine/backtest/portfolio_engine.py`):

```python
result = portfolio_engine.run(
    strategies={"AAPL": ema_strategy, "MSFT": macd_strategy},
    data=ohlcv_data,
    config=PortfolioConfig(
        initial_capital=100000,
        weights={"AAPL": 0.5, "MSFT": 0.5},
        rebalance_frequency=...,  # daily/weekly/monthly/quarterly
    ),
)
```

## Related

- [[Risk Metrics]] — Individual position metrics
- [[Backtesting]] — Portfolio engine overview
- [[Bollinger Bands]] — Example strategy