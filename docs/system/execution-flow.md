# Execution Flow

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKTEST EXECUTION FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

  1. DATA FETCH
     └─ DataService → DataProvider → OHLCV DataFrame

  2. STRATEGY SIGNAL GENERATION
     └─ StrategyRegistry.get() → Strategy.generate_signals() → Signals[]

  3. ENGINE EXECUTION
     └─ BacktestEngine.run(strategy, data, config) → Trades[] + Equity Curve

  4. PORTFOLIO MANAGEMENT (optional)
     └─ PortfolioEngine.run(strategies[], data, config) → Positions[]

  5. METRICS CALCULATION
     └─ RiskMetrics.calculate(trades, equity_curve) → RiskMetrics

  6. RESPONSE FORMATION
     └─ BacktestService → BacktestResponse → API Response
```

## Key Files

### Data Flow
- `src/infrastructure/data_providers/yahoo_provider.py` - Yahoo Finance data
- `src/infrastructure/data_providers/nse_provider.py` - NSE India data
- `src/application/services/data_service.py` - Data orchestration

### Strategy → Signal
- `src/strategies/base.py` - BaseStrategy abstract class
- `src/strategies/registry.py` - Auto-discovery mechanism
- `src/strategies/momentum/ema_crossover.py` - Example strategy
- Individual strategy files per family

### Engine Execution
- `src/engine/backtest/engine.py` - Event-driven BacktestEngine
- `src/engine/backtest/advanced_engine.py` - Vectorized engine
- `src/engine/backtest/portfolio_engine.py` - Multi-symbol portfolio

### Optimization
- `src/engine/optimizer/optimizer.py` - Base optimizer
- Grid Search, Random Search, Genetic Algorithm implementations

### Walk-Forward
- `src/engine/walkforward/walkforward.py` - Rolling window validation

### Metrics
- `src/analytics/risk_metrics.py` - Individual trade/position metrics
- `src/analytics/portfolio_metrics.py` - Portfolio-level metrics

## Execution Config

```python
@dataclass
class BacktestConfig:
    initial_capital: float = 100000.0
    commission: float = 0.001        # 0.1%
    slippage: float = 0.0005       # 0.05%
    risk_per_trade: float = 0.02   # 2% per trade
    max_position_size: float = 0.2 # 20% max position
    allow_shorting: bool = True
```

## Output

A backtest returns:
- `trades: List[Trade]` - All executed trades
- `equity_curve: pd.DataFrame` - Portfolio value over time
- `metrics: RiskMetrics` - Performance metrics (Sharpe, Sortino, Drawdown, etc.)
- `final_capital: float` - Ending portfolio value
- `total_return: float` - Percentage return