# Breakout Strategy

## Definition
A strategy that enters when price breaks above a recent high (long) or below a recent low (short), betting that the breakout marks the start of a new trend. Uses ATR for volatility-aware signal strength.

**Core thesis:** Consolidation precedes expansion. When price escapes a range with conviction, a trend follows.

## Why It Matters
- **Catches big moves**: Breakouts capture the start of trends that EMA crossovers detect later
- **Defined risk**: Entry at breakout level → stop below the range = clear risk/reward
- **Regime-dependent**: Excellent after squeezes, terrible in noisy markets

## In My System

**Location:** `src/strategies/momentum/ema_crossover.py::BreakoutStrategy`
**Re-exported:** `src/strategies/breakout/__init__.py`

**Registration:**
```python
@register_strategy("breakout")
class BreakoutStrategy(BaseStrategy):
```

**Strategy metadata:**
- **Name:** "Breakout Strategy"
- **Version:** "1.0.0"
- **Type:** "breakout"
- **Data requirements:** `["open", "high", "low", "close"]` — needs OHLC, not just close

---

## Implementation Details

### Default Parameters
```python
def _set_default_parameters(self):
    self._params = {
        "lookback_period": 20,      # Channel width (trading days)
        "atr_period": 14,           # ATR for signal strength
        "atr_multiplier": 2.0,      # ATR scaling for strength metric
        "use_trailing_stop": True,   # Flag (not yet wired to engine)
    }
```

**Why 20-day lookback?** Roughly one trading month. Captures meaningful support/resistance levels without being so long that breakouts are rare.

---

### Signal Generation (`ema_crossover.py:170-196`)

```python
def generate_signals(self, data):
    df = data.copy()
    lookback = int(self._params["lookback_period"])
    
    # Build the channel
    df["highest"] = df["high"].rolling(window=lookback).max()
    df["lowest"] = df["low"].rolling(window=lookback).min()
    
    # Shift to avoid look-ahead (use previous bar's channel)
    df["high_prev"] = df["highest"].shift(1)
    df["low_prev"] = df["lowest"].shift(1)
    
    # Breakout detection: new high/low that WASN'T a new high/low yesterday
    df["breakout_up"] = (high > df["high_prev"]) & (high.shift(1) <= df["high_prev"].shift(1))
    df["breakout_down"] = (low < df["low_prev"]) & (low.shift(1) >= df["low_prev"].shift(1))
    
    df["signal"] = 0
    df.loc[df["breakout_up"], "signal"] = 1
    df.loc[df["breakout_down"], "signal"] = -1
    
    # ATR-based signal strength
    df["atr"] = self._calculate_atr(df, atr_period)
    df["signal_strength"] = df["atr"] / df["close"] * atr_multiplier
```

**Key implementation notes:**

1. **Channel uses high/low**, not close. This makes breakouts harder to trigger (must exceed intraday extremes, not just closing prices).

2. **Double shift**: `high > high_prev` AND `high.shift(1) <= high_prev.shift(1)`. This ensures the breakout is a *new* event, not a continuation of yesterday's breakout.

3. **Signal strength = ATR/Price × Multiplier**: Higher ATR relative to price = more volatile = stronger breakout conviction. This can be used for position sizing.

---

## Comparison: Breakout vs Volume Breakout

| Aspect | Breakout | Volume Breakout |
|--------|----------|----------------|
| Trigger | Price breaks channel | Price breaks channel + above-avg volume |
| False positive rate | Higher | Lower (volume confirms) |
| Signal frequency | More signals | Fewer signals |
| Data requirement | OHLC | OHLCV (needs volume) |
| Win rate (typical) | 35-45% | 40-50% |
| Profit factor | 2.0-3.0 | 1.5-2.5 |

---

## Failure Cases & Edge Cases

### 1. False Breakouts (Fakeouts)
**Symptom:** Price breaks above channel, immediately reverses

**Frequency:** 50-60% of all breakouts are false in ranging markets

**Detection:**
```python
# Volume confirmation (not in current implementation)
volume_above_avg = volume > volume.rolling(20).mean() * 1.5
confirmed_breakout = breakout_up & volume_above_avg
```

**Mitigation:** Use [[Volume Strategies]] as a filter. Only take breakouts with above-average volume.

### 2. Parameter-Period Mismatch
**Symptom:** 20-day lookback misses weekly cycles in hourly data

**Cause:** Lookback is in bars, not calendar time. 20 bars on hourly = 3 trading days, not 1 month.

**Fix:** Adjust lookback per timeframe:
- Daily: 20 (1 month)
- Hourly: 130 (1 month of trading hours)
- 15-min: 520 (1 month)

### 3. Trailing Stop Not Wired
**Symptom:** `use_trailing_stop=True` has no effect on backtesting

**Cause:** The parameter exists in `_params` but the base engine doesn't support trailing stops. Only `advanced_engine.py` has trailing stop logic.

**Impact:** Strategy trades without a trailing stop regardless of this parameter. Must use the advanced engine for actual trailing stop behavior.

### 4. Gap Breakouts
**Symptom:** Stock gaps above the channel at open — backtest shows entry at channel level

**Reality:** You can't buy at the breakout level if the stock gaps 5% above it

**Impact:** Backtest overestimates entry quality. Live slippage will be worse than modeled.

---

## Key Insights

### Breakouts Are Right-Tailed
Unlike momentum strategies (symmetric wins and losses), breakouts have asymmetric payoffs:
- Small losses (quick stop on false breakout)
- Large wins (trend continuation)
- Low win rate (35-45%) compensated by large payoff ratio

This means **loss streaks are expected and normal**. 7-8 consecutive losses is not unusual.

### ATR Signal Strength Is Underutilized
The `signal_strength` field provides a natural position sizing signal: high ATR = high conviction breakout = larger position. This is the opposite of what most traders do (smaller position in volatile markets).

### Colocation Problem
The `BreakoutStrategy` class lives in `ema_crossover.py` (a momentum file), re-exported from `breakout/__init__.py`. This is a code smell — it should be moved to its own file for clarity.

---

## Related Strategies
- [[Volume Strategies]] — Volume confirmation for breakouts
- [[EMA Crossover]] — Momentum approach (enters later, smoother)
- [[Bollinger Bands]] — Squeeze detection → breakout timing

## Related Concepts
- [[Regime Detection]] — Breakouts work best after consolidation (squeeze)
- [[Position Sizing]] — ATR-based sizing pairs naturally with breakout strategy
- [[Event System]] — How the engine processes breakout signals

## Implementation References
- `src/strategies/momentum/ema_crossover.py:144-213` — BreakoutStrategy class
- `src/strategies/breakout/__init__.py` — Re-export
- `src/engine/backtest/advanced_engine.py:39-49` — Trailing stop config
