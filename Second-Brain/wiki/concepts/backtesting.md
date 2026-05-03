# Backtesting

## Definition
Backtesting simulates a trading strategy on historical data to evaluate its performance before deploying real capital. It answers: "Would this strategy have made money in the past?"

## Why It Matters
- **Avoid costly mistakes**: A strategy that looks good in theory can fail spectacularly on real data
- **Parameter tuning**: Find optimal parameters without risking capital
- **Expectation setting**: Understand drawdown patterns, win rates, and return profiles
- **Regime analysis**: See how strategies behave in bull/bear/sideways markets

## In My System

TSRL implements **three backtest engines**, each with trade-offs:

### 1. Event-Driven Engine (`src/engine/backtest/engine.py::BacktestEngine`)

```
Bar-by-bar simulation with realistic order execution
```

**How it works:**
1. Processes OHLCV bars sequentially
2. Calls `strategy.generate_signals(data)` at each bar
3. Emits events: `SignalEvent → OrderEvent → FillEvent`
4. Applies commission/slippage at execution
5. Tracks position state (long/short/flat)

**Key implementation detail** — Look-ahead bias fix (`engine.py:198-201`):
```python
# Set pending signal for next bar - DO NOT enter immediately
# This fixes look-ahead bias: signal is known at close,
# but entry happens at next bar's open
pending_signal = signal
```

**When to use:**
- Single-symbol strategies
- Strategies requiring realistic execution simulation
- Final validation before deployment

**Performance:** ~100-500ms per backtest (depends on data length)

---

### 2. Vectorized Engine (`src/engine/backtest/engine.py::VectorizedBacktestEngine`)

```
Matrix operations for fast parameter scanning
```

**How it works:**
1. Computes all signals at once via pandas operations
2. Uses `shift(1)` to prevent look-ahead bias
3. Applies commission as a direct cost subtraction
4. Computes equity curve via `cumprod()`

**Key implementation:**
```python
# Vectorized return calculation
positions = (signals["signal"] != 0).astype(int)
strategy_returns = positions.shift(1).fillna(0) * returns
commission_cost = abs(position_changes) * cfg.commission
strategy_returns = strategy_returns - commission_cost
```

**When to use:**
- Parameter optimization (grid/random search)
- Quick strategy prototyping
- Multi-strategy comparison

**Performance:** ~10-50ms per backtest (10x faster than event-driven)

**Trade-offs:**
- ❌ Cannot model complex order execution
- ❌ No position-by-position tracking
- ✅ Fast enough for genetic algorithms

---

### 3. Portfolio Engine (`src/engine/backtest/portfolio_engine.py::EnhancedPortfolioBacktestEngine`)

```
Multi-symbol backtesting with capital allocation and rebalancing
```

**How it works:**
1. Allocates capital by weight: `allocated_capital = initial_capital * weight`
2. Runs independent backtests per symbol
3. Combines equity curves: `combined["total"] = combined.sum(axis=1)`
4. Optionally rebalances when drift exceeds threshold

**Rebalancing logic** (`portfolio_engine.py:486-519`):
```python
if date in rebalance_dates:
    should_rebalance = True
    reason = "periodic"

if cfg.rebalance_threshold:
    max_drift = max(abs(current_weights[s] - target_weights[s]))
    if max_drift > cfg.rebalance_threshold:
        should_rebalance = True
        reason = f"threshold ({max_drift:.2%} drift)"
```

**When to use:**
- Multi-symbol portfolio strategies
- Testing allocation weights
- Analyzing correlation benefits

---

## Execution Flow

```
DataService.fetch_data() → OHLCV DataFrame
       ↓
Strategy.generate_signals() → Signal DataFrame
       ↓
BacktestEngine.run() → Trade[] + Equity Curve
       ↓
RiskMetrics.calculate() → Sharpe, Sortino, MaxDD, etc.
       ↓
BacktestRepository.persist() → SQLite
```

**Orchestrated by:** `BacktestService.run_backtest()` (`src/application/services/backtest_service.py:64-135`)

---

## Key Configuration (`BacktestConfig`)

| Parameter | Default | Impact |
|-----------|---------|--------|
| `initial_capital` | 100,000 | Base for position sizing |
| `commission` | 0.001 (0.1%) | Direct P&L reduction |
| `slippage` | 0.0005 (0.05%) | Execution cost model |
| `risk_per_trade` | 0.02 (2%) | Position size limiter |
| `max_position_size` | 0.2 (20%) | Concentration cap |
| `allow_shorting` | True | Enables short strategies |

---

## Failure Cases & Edge Cases

### 1. Look-Ahead Bias
**Symptom:** Unrealistically high Sharpe ratios (>3)

**Cause:** Using future data in signal generation

**Fix in my system:**
```python
# WRONG - uses current bar's close to decide entry
if signal == 1:
    enter_at_close = True

# CORRECT - signal known at close, entry at next open
if signal == 1:
    pending_signal = 1  # Execute next bar
```

### 2. Survivorship Bias
**Symptom:** Backtest works on current S&P 500 constituents but fails on historical data

**Cause:** Testing only on stocks that survived, ignoring delisted companies

**Mitigation:** Use point-in-time constituent lists (not yet implemented)

### 3. Overfitting
**Symptom:** Perfect in-sample performance, catastrophic out-of-sample

**Cause:** Too many parameters relative to data points

**Detection:**
- Walk-forward analysis (`src/engine/walkforward/walkforward.py`)
- Parameter sensitivity charts
- Out-of-sample testing

**Rule of thumb:** ≤ 1 parameter per 100 trades

### 4. Commission Bleed
**Symptom:** Strategy profitable before commission, losing after

**Cause:** High-frequency strategies with small edge per trade

**Example:**
```python
# 1000 trades/year, 0.1% commission each way = 0.2% per round trip
# Edge must exceed 0.2% per trade to be profitable
```

### 5. Slippage Underestimation
**Symptom:** Live performance worse than backtest

**Cause:** Fixed slippage model doesn't capture:
- Low liquidity stocks (wider bid-ask)
- Gap openings (earnings, news)
- Market impact for large orders

---

## Key Insights

### The Backtesting Paradox
> "If your backtest looks too good to be true, it's wrong. If it looks realistic, you still don't know if it will work."

**Why:** Past performance ≠ future results, but past failure modes ≈ future failure modes

### Commission Is the Silent Killer
A strategy with 55% win rate and 1:1 payoff needs:
- Win rate > 50% + commission/(avg_win + avg_loss)

At 0.1% commission, you need ~52% win rate just to break even.

### Drawdown Is Inevitable
Even strategies with positive expectancy will have:
- 5-10 consecutive losses (statistically guaranteed)
- 20%+ drawdown periods (test psychology beforehand)

### Vectorized ≠ Event-Driven
**Critical difference:**
- Vectorized assumes you can trade at the close
- Event-driven simulates order book dynamics

For final validation, always run event-driven.


---

### 4. Advanced Engine (`src/engine/backtest/advanced_engine.py::AdvancedBacktestEngine`)

```
Event-driven with built-in risk management (stop-loss, take-profit, trailing stop)
```

**How it works:**
1. Same bar-by-bar loop as the base engine
2. Adds `RiskManagementConfig` with configurable exit types
3. Priority chain: Stop Loss → Take Profit → Trailing Stop → Signal Exit
4. Tracks `entry_high`/`entry_low` for trailing stop calculations

**Key difference from base engine:**
- Base engine: Only exits on signal reversal
- Advanced engine: Exits on stop/TP/trailing/signal (whichever triggers first)

**Config (`AdvancedBacktestConfig`):**
```python
@dataclass
class RiskManagementConfig:
    enable_stop_loss: bool = True
    stop_loss_pct: float = 0.02      # 2% stop
    enable_take_profit: bool = True
    take_profit_pct: float = 0.04    # 4% target (2:1 R:R)
    enable_trailing_stop: bool = False
    trailing_stop_pct: float = 0.015 # 1.5% trailing
    max_daily_loss: float = 0.05     # 5% daily circuit breaker
```

**When to use:**
- Production-grade backtesting with realistic exits
- Strategies that need defined stop-loss levels
- Risk-adjusted performance comparison

**Trade-off:** Does NOT use `pending_signal` for look-ahead prevention on reversals (see [[Event System]])

---

## Related Concepts
- [[Risk Metrics]] — How performance is measured
- [[Portfolio Metrics]] — Multi-symbol aggregation
- [[Walk-Forward Analysis]] — Out-of-sample validation
- [[Strategy Design]] — Strategy interface contract
- [[EMA Crossover]] — Example strategy implementation
- [[Event System]] — The execution model behind all engines
- [[Trade Lifecycle]] — Signal → Position → Trade → P&L flow
- [[Optimization]] — Uses these engines for parameter search
- [[Position Sizing]] — How capital allocation works per engine

## Implementation References
- `src/engine/backtest/engine.py` — Core engines (Event-Driven + Vectorized)
- `src/engine/backtest/advanced_engine.py` — Advanced with risk management
- `src/engine/backtest/portfolio_engine.py` — Portfolio extension
- `src/application/services/backtest_service.py` — Orchestration layer
- `src/strategies/base.py` — Strategy interface

