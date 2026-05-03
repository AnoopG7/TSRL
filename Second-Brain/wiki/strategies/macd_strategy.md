# MACD Strategy

## Definition
A momentum strategy using the MACD (Moving Average Convergence Divergence) indicator to identify trend changes through signal line crossovers, centerline crosses, and divergences.

**Core thesis:** MACD captures both trend direction and momentum acceleration, providing earlier signals than simple moving average crossovers.

## Why It Matters
- **Multi-signal indicator**: Three distinct signal types (crossover, centerline, divergence)
- **Momentum + trend**: Combines both in one indicator
- **Histogram insight**: Visualizes momentum acceleration/deceleration
- **Widely followed**: Self-fulfilling prophecy due to popularity

## In My System

**Location:** `src/strategies/momentum/macd_strategy.py::MACDStrategy`

**Registration:**
```python
@register_strategy("macd")
class MACDStrategy(BaseStrategy):
```

**Strategy metadata:**
- **Name:** "macd"
- **Type:** "momentum"
- **Data requirements:** `["close"]` only

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

**Same as EMA crossover** — MACD is built from EMAs with these standard settings.

---

### MACD Calculation
```python
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    
    # MACD Line = Fast EMA - Slow EMA
    ema_fast = df["close"].ewm(span=self._fast_period).mean()
    ema_slow = df["close"].ewm(span=self._slow_period).mean()
    df["macd"] = ema_fast - ema_slow
    
    # Signal Line = EMA of MACD Line
    df["signal"] = df["macd"].ewm(span=self._signal_period).mean()
    
    # Histogram = MACD - Signal (momentum acceleration)
    # (Not explicitly stored but derivable)
    
    # Crossover signals
    df.loc[(df["macd"] > df["signal"]) & (df["macd"].shift(1) <= df["signal"].shift(1)), "signal"] = 1
    df.loc[(df["macd"] < df["signal"]) & (df["macd"].shift(1) >= df["signal"].shift(1)), "signal"] = -1
    
    return df
```

**Three components:**

| Component | Formula | Interpretation |
|-----------|---------|----------------|
| **MACD Line** | EMA(12) - EMA(26) | Trend direction |
| **Signal Line** | EMA(9) of MACD | Trigger for trades |
| **Histogram** | MACD - Signal | Momentum acceleration |

---

## Signal Types

### 1. Signal Line Crossover (Implemented)
```python
# Buy: MACD crosses above signal line
df.loc[(df["macd"] > df["signal"]) & (df["macd"].shift(1) <= df["signal"].shift(1)), "signal"] = 1

# Sell: MACD crosses below signal line
df.loc[(df["macd"] < df["signal"]) & (df["macd"].shift(1) >= df["signal"].shift(1)), "signal"] = -1
```

**Characteristics:**
- Most common signal type
- Works in trending markets
- Prone to whipsaws in ranging markets

---

### 2. Centerline Crossover (Not Implemented)
```python
# Buy: MACD crosses above zero (bullish momentum)
bullish = (df["macd"] > 0) & (df["macd"].shift(1) <= 0)

# Sell: MACD crosses below zero (bearish momentum)
bearish = (df["macd"] < 0) & (df["macd"].shift(1) >= 0)
```

**Characteristics:**
- Slower but more reliable than signal line cross
- Indicates trend change, not just momentum shift
- Fewer signals, higher conviction

---

### 3. Divergence (Not Implemented)
```python
# Bullish divergence: Price makes lower low, MACD makes higher low
# Bearish divergence: Price makes higher high, MACD makes lower high

# Requires peak/trough detection
from scipy.signal import argrelextrema

peaks = argrelextrema(df["close"].values, np.less)[0]
troughs = argrelextrema(df["close"].values, np.greater)[0]
```

**Characteristics:**
- Leading indicator (predicts reversals)
- Subjective (requires swing identification)
- Highest risk/reward signal type

---

## Parameter Sensitivity

### Fast Period (12 default)
| Value | Effect |
|-------|--------|
| 6-8 | Very sensitive, many false signals |
| 12 | Balanced (standard) |
| 15-21 | Smoother, fewer signals |

### Slow Period (26 default)
| Value | Effect |
|-------|--------|
| 15-20 | Shorter-term trend |
| 26 | Balanced (standard) |
| 30-50 | Longer-term trend |

### Signal Period (9 default)
| Value | Effect |
|-------|--------|
| 5-7 | Faster triggers, more whipsaws |
| 9 | Balanced (standard) |
| 12-15 | Slower, more reliable |

### Alternative Settings
| Fast | Slow | Signal | Use Case |
|------|------|--------|----------|
| 12 | 26 | 9 | Standard (default) |
| 8 | 17 | 9 | Faster trading |
| 21 | 52 | 9 | Longer-term trends |
| 5 | 13 | 5 | Scalping (intraday) |

---

## Failure Cases & Edge Cases

### 1. Whipsaw in Ranging Markets
**Symptom:** 5+ consecutive losing trades

**Cause:** MACD oscillates around signal line with no clear trend

**Detection:**
```python
# Count crossovers in rolling window
crossovers = (signals["signal"].diff() != 0).rolling(20).sum()
if crossovers > 6:  # More than 6 signals in 20 days
    # Market is chopping - stand down
```

**Mitigation:**
- Add ADX filter: Only trade when ADX > 25
- Add centerline filter: Only take signal-line crosses in direction of centerline
- Use histogram slope: Wait for histogram to confirm momentum

---

### 2. Late Exit on Sharp Reversals
**Symptom:** Gives back 50%+ of profits before exit signal

**Cause:** Signal line is double-smoothed (EMA of EMA) → significant lag

**Example:**
```
Day 1: Price peaks, MACD at high
Day 2-5: Price drops 15%, MACD falling but still above signal
Day 6: Cross happens → Exit at much lower price
```

**Mitigation:**
- Use price-based trailing stop
- Exit on histogram reversal (earlier than signal line cross)
- Partial exits: Scale out as price moves against position

---

### 3. Histogram Divergence False Signals
**Symptom:** Divergence appears, but price continues in original direction

**Cause:** Divergence can persist through strong trends

**Example:**
```
Price: Higher high
MACD: Lower high (divergence)
Result: Price consolidates briefly, then continues up
```

**Key insight:** Divergence indicates *potential* reversal, not guaranteed

**Mitigation:**
- Wait for confirmation: Price must break recent swing low/high
- Use only as confluence, not standalone signal
- Combine with volume: Divergence + volume spike = higher probability

---

### 4. Parameter Overfitting
**Symptom:** Works on backtest period, fails on out-of-sample

**Detection:**
```python
# Test multiple parameter sets
params = [(12, 26, 9), (8, 17, 9), (21, 52, 9)]
for fast, slow, signal in params:
    result = backtest(MACDStrategy(fast, slow, signal))
    print(f"{fast}/{slow}/{signal}: Sharpe = {result.metrics.sharpe:.2f}")

# If only (12,26,9) works, you're overfitted
```

**Mitigation:**
- Walk-forward optimization
- Use standard parameters (they're standard for a reason)
- Ensemble multiple parameter sets

---

## Performance Characteristics

### Typical Metrics (S&P 500, 2010-2023)
| Metric | Value |
|--------|-------|
| Win Rate | 42-52% |
| Profit Factor | 1.3-1.7 |
| Sharpe Ratio | 0.7-1.1 |
| Max Drawdown | 18-28% |
| Avg Trade Duration | 15-40 days |
| Trades per Year | 8-15 |

**Comparison to EMA Crossover:**
- Slightly fewer trades (signal line adds filter)
- Similar win rate
- Slightly better risk-adjusted returns (when trending)

---

## MACD + RSI Combination Pattern

A common enhancement (not implemented in my system):

```python
# MACD for trend direction
macd_bullish = df["macd"] > df["signal"]

# RSI for entry timing
rsi_oversold = df["rsi"] < 30

# Entry: MACD bullish + RSI oversold
entry = macd_bullish & rsi_oversold
```

**Rationale:**
- MACD says "trend is up"
- RSI says "pullback is ending"
- Combined = higher probability entry

---

## Usage Examples

### CLI
```bash
# Basic backtest
PYTHONPATH=. python -m src.cli backtest \
  --strategy macd \
  --symbol AAPL \
  --start-date 2020-01-01

# Custom parameters
PYTHONPATH=. python -m src.cli backtest \
  --strategy macd \
  --strategy-params '{"fast_period": 8, "slow_period": 17}' \
  --symbol QQQ
```

### API
```python
POST /api/v1/backtests/run
{
  "strategy_name": "macd",
  "symbol": "AAPL",
  "parameters": {"fast_period": 12, "slow_period": 26, "signal_period": 9}
}
```

---

## Key Insights

### The Histogram Leading Indicator
> "The histogram often turns before the MACD line crosses. Watch for slope changes."

**Pattern:**
1. Histogram makes lower high (while MACD still rising)
2. MACD line peaks
3. MACD crosses signal line

**Trading implication:** Histogram slope change = early warning, not entry signal

---

### Why Standard Parameters Work
The 12/26/9 settings aren't arbitrary:
- 12 days ≈ 2.5 trading weeks (short-term cycle)
- 26 days ≈ 1 trading month (medium-term cycle)
- 9 days ≈ 1.5 weeks (signal smoothing)

**Self-fulfilling aspect:** Millions of traders watch these levels → collective reaction

---

### MACD vs EMA Crossover
| Aspect | EMA Crossover | MACD |
|--------|---------------|------|
| Calculation | EMA(fast) - EMA(slow) | Same, but with signal line |
| Signals | Direct cross | Filtered through signal line |
| Lag | Less | More (double smoothing) |
| False signals | More | Fewer (but later) |
| Best for | Early trend entry | Confirmed trend entry |

---

## Related Strategies
- [[EMA Crossover]] — Simpler, faster version
- [[RSI Mean Reversion]] — Complementary (momentum vs mean reversion)
- [[MA Ribbon]] — Visual trend confirmation

## Implementation References
- `src/strategies/momentum/macd_strategy.py` — Full implementation
- `src/strategies/base.py` — Base class interface
- `src/engine/backtest/engine.py` — Execution engine
