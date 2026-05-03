# MA Ribbon Strategy

## Definition
A momentum strategy that uses three exponential moving averages (fast, medium, slow) to detect **trend structure alignment**. Signals fire when all three MAs align in bullish or bearish order for the first time.

**Core thesis:** When fast > medium > slow, the trend is strong and accelerating. When this alignment first forms, the trend is beginning — that's the entry.

## Why It Matters
- **Trend confirmation**: Unlike [[EMA Crossover]] (two MAs), the ribbon requires triple alignment — fewer false signals
- **Trend strength visual**: The spacing between MAs shows trend momentum (wide = strong, narrow = weakening)
- **Regime proxy**: MA alignment directly maps to trending/ranging regimes

## In My System

**Location:** `src/strategies/momentum/ma_ribbon.py`

Two strategies in this file:

### MovingAverageRibbonStrategy (`ma_ribbon`)

```python
@register_strategy("ma_ribbon")
class MovingAverageRibbonStrategy(BaseStrategy):
```

**Parameters:**
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `fast_period` | 5 | 2-20 | Short-term trend (weekly) |
| `medium_period` | 20 | 10-50 | Medium-term trend (monthly) |
| `slow_period` | 50 | 20-200 | Long-term trend (quarterly) |

**Validation enforced:**
```python
def _validate_parameters(self):
    if self._fast_period >= self._medium_period:
        raise ValueError("fast_period must be less than medium_period")
    if self._medium_period >= self._slow_period:
        raise ValueError("medium_period must be less than slow_period")
```

---

### Signal Generation

```python
def generate_signals(self, data):
    # Compute three EMAs
    ma_fast = close.ewm(span=self._fast_period, adjust=False).mean()
    ma_medium = close.ewm(span=self._medium_period, adjust=False).mean()
    ma_slow = close.ewm(span=self._slow_period, adjust=False).mean()
    
    # Define alignment states
    bullish = (ma_fast > ma_medium) & (ma_medium > ma_slow)
    bearish = (ma_fast < ma_medium) & (ma_medium < ma_slow)
    
    # Signal on TRANSITION into alignment (not while aligned)
    prev_bullish = bullish.shift(1).fillna(False)
    prev_bearish = bearish.shift(1).fillna(False)
    
    golden_cross = bullish & ~prev_bullish  # Just became bullish
    death_cross = bearish & ~prev_bearish    # Just became bearish
    
    signals.loc[golden_cross, "signal"] = 1
    signals.loc[death_cross, "signal"] = -1
```

**Key implementation detail:** The signal fires on *transition*, not while aligned. This means:
- Day 1: Fast crosses above Medium → no signal (slow still below)
- Day 5: Medium crosses above Slow → **SIGNAL** (full alignment achieved)
- Day 6-100: Still aligned → no signal (already in position)

This prevents signal spam during trends.

---

### TripleMAStrategy (`triple_ma`)

Same concept but uses SMA instead of EMA, with different default periods:

```python
@register_strategy("triple_ma")
class TripleMAStrategy(BaseStrategy):
    # fast=10, medium=30, slow=50
    # Uses .rolling() instead of .ewm()
```

**Difference from MA Ribbon:**
- MA Ribbon: EMA (recent-weighted, faster response)
- Triple MA: SMA (equal-weighted, smoother but laggier)

---

## EMA Crossover vs MA Ribbon vs Triple MA

| Aspect | EMA Crossover | MA Ribbon | Triple MA |
|--------|--------------|-----------|-----------|
| MAs used | 2 (fast/slow) | 3 (fast/med/slow) EMA | 3 (fast/med/slow) SMA |
| Signal count | More frequent | Less frequent | Least frequent |
| Whipsaw risk | Higher | Lower | Lowest |
| Lag | Low | Medium | High |
| Best timeframe | Swing (days-weeks) | Position (weeks-months) | Position (months) |
| Trend confirmation | Weak (any cross) | Strong (triple alignment) | Strongest |

---

## Failure Cases & Edge Cases

### 1. Consolidation Chop
**Symptom:** MAs flatten and weave together, creating rapid false alignment/de-alignment

**Cause:** No trend → MAs converge → tiny moves cause alignment changes

**Detection:** Check MA spacing: if `abs(fast - slow) / close < 0.01`, MAs are too close — stand down

**Impact:** Multiple small losses from false entries and quick stops

### 2. Late Entry on Strong Trends
**Symptom:** By the time triple alignment forms, the trend is already 10-15% in

**Cause:** The slow MA (50-period) takes months to turn. By the time it aligns, the easy money is made.

**Trade-off:** This is the cost of higher confidence. Shorter slow periods (30-40) enter earlier but produce more false signals.

### 3. No Exit Signal in Weakening Trends
**Symptom:** Strategy holds through a 20% drawdown before MAs finally de-align

**Cause:** Exit requires bearish alignment (fast < medium < slow). In a slow decline, this takes weeks.

**Mitigation:** Combine with ATR-based stop loss or RSI divergence for earlier exit. The strategy excels at entry but is weak at exit.

---

## Key Insights

### The Ribbon As Regime Detector
MA alignment is the simplest regime classifier:
- **Bullish:** fast > medium > slow (trending up)
- **Bearish:** fast < medium < slow (trending down)
- **Neither:** Ranging or transitioning

This makes the MA Ribbon useful beyond just signal generation — it can serve as a regime filter for other strategies. See [[Regime Detection]].

### Ribbon Width = Momentum
The distance between fast and slow MA indicates trend strength:
```python
ribbon_width = (ma_fast - ma_slow) / ma_slow  # Normalized
```
- Wide ribbon: Strong trend, high confidence
- Narrow ribbon: Weakening trend, consider reducing position

### EMA vs SMA Trade-off
EMA weights recent data more → faster to detect new trends, but also faster to produce false signals. For a strategy that's explicitly about confirmation (triple alignment), EMA is actually the better choice — you're already filtering via triple confirmation, so the speed advantage of EMA helps without adding noise.

---

## Related Strategies
- [[EMA Crossover]] — Simpler version (2 MAs instead of 3)
- [[MACD Strategy]] — EMA-based with signal line (different confirmation method)
- [[Breakout]] — Can confirm breakouts with ribbon alignment

## Related Concepts
- [[Regime Detection]] — MA alignment as regime classifier
- [[Strategy Design]] — Principle 7: One edge per strategy
- [[Optimization]] — 3 parameters (fast/medium/slow) = safe for optimization

## Implementation References
- `src/strategies/momentum/ma_ribbon.py:10-102` — MovingAverageRibbonStrategy
- `src/strategies/momentum/ma_ribbon.py:105-197` — TripleMAStrategy
- `src/strategies/base.py:95-99` — Parameter validation pattern
