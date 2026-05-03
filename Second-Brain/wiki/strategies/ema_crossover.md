# EMA Crossover Strategy

## Definition
A momentum strategy that generates buy signals when a fast Exponential Moving Average (EMA) crosses above a slow EMA, and sell signals on the inverse cross.

**Core thesis:** Price trends persist, and EMA crossovers capture trend changes earlier than simple moving averages.

## Why It Matters
- **Trend following foundation**: Teaches core concepts applicable to all momentum strategies
- **Parameter sensitivity**: Easy to optimize and understand failure modes
- **Benchmark strategy**: Serves as a baseline for comparing more complex strategies
- **Production use**: Actually profitable on certain assets/timeframes (not just educational)

## In My System

**Location:** `src/strategies/momentum/ema_crossover.py::EMACrossoverStrategy`

**Registration:**
```python
@register_strategy("ema_crossover")
class EMACrossoverStrategy(BaseStrategy):
```

**Strategy metadata:**
- **Name:** "EMA Crossover"
- **Version:** "1.0.0"
- **Type:** "momentum"
- **Data requirements:** `["close"]` only (minimal dependency)

---

## Implementation Details

### Default Parameters
```python
def _set_default_parameters(self) -> None:
    self._params = {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
    }
```

**Why these values?**
- 12/26: Standard MACD settings (reflect weekly/bi-weekly cycles)
- 9: Common signal line period

**Valid ranges:**
- `fast_period`: 5-50
- `slow_period`: 20-200
- Constraint: `fast_period < slow_period` (enforced in validation)

---

### Signal Generation
```python
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    
    fast_period = int(self._params["fast_period"])
    slow_period = int(self._params["slow_period"])
    
    # Calculate EMAs
    df["ema_fast"] = df["close"].ewm(span=fast_period, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=slow_period, adjust=False).mean()
    
    # Crossover detection
    df["crossover"] = df["ema_fast"] - df["ema_slow"]
    df["prev_crossover"] = df["crossover"].shift(1)
    
    df["signal"] = 0
    df.loc[(df["crossover"] > 0) & (df["prev_crossover"] <= 0), "signal"] = 1   # Buy
    df.loc[(df["crossover"] < 0) & (df["prev_crossover"] >= 0), "signal"] = -1  # Sell
    
    # Signal strength: normalized crossover magnitude
    df["signal_strength"] = np.abs(df["crossover"] / df["close"])
    
    return df
```

**Key implementation notes:**

1. **`adjust=False`**: Uses span-based EMA (standard in trading), not center-of-mass
2. **Crossover detection**: Checks sign change, not just absolute values
3. **Signal strength**: Provides confidence metric for potential position sizing

---

### Entry/Exit Conditions

**Inherited from BaseStrategy** (`src/strategies/base.py:105-117`):

```python
def entry_conditions(self, data: pd.DataFrame, idx: int) -> bool:
    signals = self.generate_signals(data)
    if idx >= len(signals):
        return False
    row = signals.iloc[idx]
    return row.get("signal", 0) == 1

def exit_conditions(self, data: pd.DataFrame, idx: int) -> bool:
    signals = self.generate_signals(data)
    if idx >= len(signals):
        return False
    row = signals.iloc[idx]
    return row.get("signal", 0) == -1
```

**Behavior:**
- Entry: `signal == 1` (bullish cross)
- Exit: `signal == -1` (bearish cross) — reverses position if shorting enabled

---

## Parameter Sensitivity

### Fast Period
| Value | Behavior | Trade-off |
|-------|----------|-----------|
| 5-8 | Very reactive, many whipsaws | High win rate needed |
| 12 (default) | Balanced | Good starting point |
| 20-50 | Smooth, fewer signals | Miss early trend moves |

### Slow Period
| Value | Behavior | Trade-off |
|-------|----------|-----------|
| 20-26 | Short-term trend | Good for swing trading |
| 50-100 | Medium-term trend | Captures bigger moves |
| 200 | Long-term trend | Very few signals, high conviction |

### Common Combinations
| Fast | Slow | Use Case |
|------|------|----------|
| 8 | 21 | Scalping (intraday) |
| 12 | 26 | Swing trading (default) |
| 20 | 50 | Position trading |
| 50 | 200 | "Golden cross / Death cross" |

---

## Failure Cases & Edge Cases

### 1. Whipsaw in Ranging Markets
**Symptom:** Rapid consecutive losses (5-10 trades)

**Cause:** EMA crosses back and forth in sideways price action

**Detection:**
```python
# Count signal reversals
reversals = (signals["signal"].diff() != 0).sum()
if reversals > threshold:
    # Market is chopping - reduce position size or stand down
```

**Mitigation:**
- Add ADX filter: Only trade when ADX > 25 (trending market)
- Add volume confirmation: Require above-average volume on crossover
- Use wider EMA spacing: 20/50 instead of 12/26

---

### 2. Lag on Sharp Reversals
**Symptom:** Strategy gives exit signal after significant drawdown

**Cause:** EMA is inherently lagging (uses historical data)

**Example:**
```
Day 1: Price crashes 10% → EMA barely moves
Day 2: EMA still hasn't crossed → Still long
Day 3: Cross finally happens → Exit at much worse price
```

**Mitigation:**
- Add stop-loss based on ATR (not implemented in base strategy)
- Use price-based exit: Exit if price drops X% below entry
- Hybrid approach: EMA for entry, price for exit

---

### 3. Parameter Overfitting
**Symptom:** 12/26 works great on AAPL 2020-2023, fails on 2024

**Cause:** Parameters tuned to specific market regime

**Detection:**
```python
# Walk-forward test
results = {}
for period in ["2020", "2021", "2022", "2023", "2024"]:
    results[period] = backtest(strategy, data[period])

# If Sharpe varies wildly (2.0 → 0.5), parameters are overfitted
```

**Mitigation:**
- Use parameter ranges, not point values: Test 10-15 fast, 20-30 slow
- Walk-forward optimization: Re-optimize quarterly
- Ensemble: Average signals from multiple parameter sets

---

### 4. Gap Risk
**Symptom:** Backtest shows clean exit, live trading gaps through stop

**Cause:** Daily bars don't capture intraday price action

**Example:**
```
Day 1 close: $100 → EMA says hold
Day 2 opens: $80 (earnings crash) → Backtest exits at $80
Reality: You can't exit at $80 if bid is $75
```

**Mitigation:**
- Model gap risk in backtest: Apply 2-5% slippage on news days
- Avoid earnings: Filter out stocks with upcoming earnings
- Use options for defined-risk exposure

---

## Performance Characteristics

### Typical Metrics (S&P 500, 2010-2023)
| Metric | Value |
|--------|-------|
| Win Rate | 45-55% |
| Profit Factor | 1.2-1.8 |
| Sharpe Ratio | 0.8-1.2 |
| Max Drawdown | 15-25% |
| Avg Trade Duration | 10-30 days |
| Trades per Year | 10-20 |

**Note:** Varies significantly by asset and market regime

---

### Regime Dependence
| Market Regime | Performance |
|---------------|-------------|
| Strong uptrend | Excellent (captures full move) |
| Strong downtrend | Excellent (shorts full move) |
| Sideways/choppy | Poor (whipsaw losses) |
| Volatile transitions | Poor (lag causes large drawdowns) |

---

## Usage Examples

### CLI
```bash
# Basic backtest
PYTHONPATH=. python -m src.cli backtest \
  --strategy ema_crossover \
  --symbol AAPL \
  --start-date 2020-01-01 \
  --end-date 2024-01-01

# With custom parameters
PYTHONPATH=. python -m src.cli backtest \
  --strategy ema_crossover \
  --strategy-params '{"fast_period": 20, "slow_period": 50}' \
  --symbol SPY
```

### API
```python
POST /api/v1/backtests/run
{
  "strategy_name": "ema_crossover",
  "symbol": "AAPL",
  "start_date": "2020-01-01",
  "end_date": "2024-01-01",
  "parameters": {"fast_period": 12, "slow_period": 26}
}
```

### Python
```python
from src.strategies.registry import StrategyRegistry
from src.engine.backtest.engine import BacktestEngine, BacktestConfig

# Create strategy
strategy = StrategyRegistry.create("ema_crossover", fast_period=12, slow_period=26)

# Run backtest
config = BacktestConfig(initial_capital=100000)
engine = BacktestEngine(config)
result = engine.run(strategy, ohlcv_data)

# Access metrics
print(f"Sharpe: {result.metrics.sharpe_ratio:.2f}")
print(f"Max DD: {result.metrics.max_drawdown:.2%}")
```

---

## Key Insights

### The 12/26 Convention
> "Everyone uses 12/26 because everyone uses 12/26."

**Self-fulfilling prophecy:** Widespread use creates temporary effectiveness as traders react to the same signals

**Implication:** Consider using non-standard parameters (e.g., 15/35) to avoid crowd behavior

---

### EMA vs SMA
| Aspect | EMA | SMA |
|--------|-----|-----|
| Lag | Less (recent data weighted more) | More |
| Whipsaws | More frequent | Less frequent |
| Trend capture | Faster entry/exit | Slower but smoother |
| Best for | Momentum strategies | Support/resistance levels |

---

### Signal Strength Matters
The `signal_strength` field in my implementation isn't just decorative:

```python
df["signal_strength"] = np.abs(df["crossover"] / df["close"])
```

**Use cases:**
- Position sizing: Larger position when crossover is decisive
- Filtering: Ignore signals below strength threshold
- Confidence scoring: Combine with other indicators

---

## Related Strategies
- [[MACD Strategy]] — EMA-based but with signal line and histogram
- [[MA Ribbon]] — Multiple EMAs for trend visualization
- [[Triple MA]] — Adds a third MA for confirmation
- [[RSI Mean Reversion]] — Opposite philosophy (mean reversion vs momentum)

## Implementation References
- `src/strategies/momentum/ema_crossover.py` — Full implementation
- `src/strategies/base.py` — Base class interface
- `src/strategies/registry.py` — Auto-discovery via `@register_strategy`
- `src/engine/backtest/engine.py` — Execution engine
