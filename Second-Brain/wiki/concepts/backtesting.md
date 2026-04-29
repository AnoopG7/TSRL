# Backtesting

## What is Backtesting?

Backtesting is the process of testing a trading strategy on historical data to evaluate its performance before deploying it with real capital.

## How TSRL Implements It

TSRL has multiple backtest engines:

### 1. Event-Driven Engine (`src/engine/backtest/engine.py`)
- Processes bars sequentially
- Emits events: SignalEvent → OrderEvent → FillEvent
- Realistic simulation of order execution
- Suitable for single-symbol strategies

### 2. Portfolio Engine (`src/engine/backtest/portfolio_engine.py`)
- Multi-symbol portfolio management
- Position sizing and rebalancing
- Supports benchmark comparison (beta/alpha)

### 3. Advanced Engine (`src/engine/backtest/advanced_engine.py`)
- Vectorized backtesting (faster)
- For optimization and parameter scanning

## Key Configuration

```python
@dataclass
class BacktestConfig:
    initial_capital: float = 100000.0
    commission: float = 0.001     # 0.1%
    slippage: float = 0.0005     # 0.05%
    risk_per_trade: float = 0.02 # 2%
    max_position_size: float = 0.2 # 20%
    allow_shorting: bool = True
```

## Execution Flow

1. **Fetch Data** → `DataService` → OHLCV DataFrame
2. **Generate Signals** → `Strategy.generate_signals()` → Signal[]
3. **Execute Trades** → `BacktestEngine.run()` → Trade[]
4. **Calculate Metrics** → `RiskMetrics.calculate()` → Metrics

## Metrics Produced (from `src/analytics/risk_metrics.py`)

| Metric | Description |
|--------|-------------|
| Total Return | % gain/loss |
| CAGR | Compounded Annual Growth Rate |
| Sharpe Ratio | Risk-adjusted return |
| Sortino Ratio | Downside risk-adjusted |
| Max Drawdown | Largest peak-to-trough |
| Calmar Ratio | Return / Max DD |
| Win Rate | % profitable trades |
| Profit Factor | Gross profit / gross loss |
| Average Trade | Mean P&L |
| Max Consecutive Wins/Losses | Streak tracking |

## Walk-Forward Extension

For avoiding overfitting: `src/engine/walkforward/walkforward.py`

- Rolling train/test windows (default: 252 days train / 63 days test)
- Walks forward through time
- Tests in-sample vs out-of-sample performance

## Related

- [[EMA Crossover]] — Common strategy to backtest
- [[MACD]] — Another strategy
- [[Portfolio Metrics]] — For multi-symbol backtests
- [[Risk Metrics]] — All available metrics