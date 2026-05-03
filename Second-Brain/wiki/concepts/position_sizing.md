# Position Sizing

## Definition
Determines how much capital to allocate per trade. The difference between a strategy that survives and one that blows up is almost never the signal — it's the position size.

## Why It Matters
- **Survival**: Wrong position size can bankrupt you even with a positive-expectancy strategy
- **Compounding**: Size affects geometric growth rate — Kelly criterion proves optimal sizing exists
- **Risk per trade**: 2% risk per trade survives 10 consecutive losses. 10% risk doesn't.

## In My System

### Current Implementation: Fixed Fractional

TSRL uses a simple fixed-fractional approach:

```python
# engine.py:231-233
available_capital = capital if capital is not None else config.initial_capital
max_shares = int((available_capital * config.max_position_size) / adjusted_price)
quantity = max(1, max_shares)
```

**Translation:** Buy as many shares as 20% of available capital allows.

**Parameters:**
| Parameter | Default | Effect |
|-----------|---------|--------|
| `max_position_size` | 0.2 (20%) | Caps single position at 20% of capital |
| `risk_per_trade` | 0.02 (2%) | Available but NOT used in position calc |

**Critical gap:** `risk_per_trade` exists in `BacktestConfig` but is **never used** in the actual position sizing calculation. The engine uses `max_position_size` instead. This means the ATR-based sizing in `BaseStrategy.calculate_position_size()` is dead code in backtesting.

---

### BaseStrategy Position Sizer (Unused)

```python
# base.py:136-152
def calculate_position_size(self, capital, risk_per_trade, entry_price, stop_loss_price):
    if entry_price == stop_loss_price:
        return 0
    risk_amount = capital * risk_per_trade          # $100K × 2% = $2,000
    price_risk = abs(entry_price - stop_loss_price) # $100 - $95 = $5
    position_size = risk_amount / price_risk         # $2,000 / $5 = 400 shares
    return max(0, position_size)
```

**This is the correct approach** — size based on risk, not capital percentage. But it requires a stop-loss price, which the base engine doesn't compute.

**Integration path:** The advanced engine with `RiskManagementConfig.stop_loss_pct` has the stop price. Wire it into position sizing to unlock proper risk-based sizing.

---

## Position Sizing Methods (Theory → Practice)

### 1. Fixed Fractional (Current)
```
Position = Capital × Fixed% / Price
```
- **Pros:** Simple, predictable allocation
- **Cons:** Ignores volatility — same size for calm AAPL and volatile TSLA
- **Used in:** TSRL's engine

### 2. Risk-Based (ATR)
```
Stop = Entry - ATR × Multiplier
Position = (Capital × Risk%) / (Entry - Stop)
```
- **Pros:** Adjusts for volatility — smaller position in volatile markets
- **Cons:** Requires ATR calculation and stop-loss level
- **Used in:** `BaseStrategy.calculate_position_size()` (but not wired)

### 3. Kelly Criterion
```
Kelly% = W - (1-W) / R
Where: W = win rate, R = avg_win / avg_loss
```
- **Pros:** Mathematically optimal for geometric growth
- **Cons:** Assumes known W and R (we don't), leads to huge positions
- **Used in:** `risk_metrics.py` for calculation, not for sizing

### 4. Half/Quarter Kelly
```
Position = Capital × Kelly% × 0.5
```
- **Pros:** 75% of optimal growth with much lower drawdown risk
- **Cons:** Still requires reliable W and R estimates
- **Rule of thumb:** Use half-Kelly in practice

---

## The Math That Matters

### Why 2% Risk Per Trade?

Starting capital: $100,000. Risk per trade: 2% = $2,000.

| Consecutive Losses | Capital Remaining | Drawdown |
|--------------------|------------------|----------|
| 5 | $90,392 | 9.6% |
| 10 | $81,707 | 18.3% |
| 15 | $73,857 | 26.1% |
| 20 | $66,761 | 33.2% |

At **10% risk per trade:**

| Consecutive Losses | Capital Remaining | Drawdown |
|--------------------|------------------|----------|
| 5 | $59,049 | 41.0% |
| 10 | $34,868 | 65.1% |

**A 65% drawdown requires 186% gain to recover.** That's why 2% is the standard.

### Kelly Example

Strategy: 55% win rate, 1.5:1 payoff ratio

```
Kelly% = 0.55 - (0.45 / 1.5) = 0.55 - 0.30 = 0.25 (25%)
Half Kelly = 12.5%
Quarter Kelly = 6.25%
```

**Full Kelly risk:** 50% chance of 50% drawdown at some point. Not survivable psychologically.

---

## Failure Cases & Edge Cases

### 1. Over-Allocation at Low Capital
**Symptom:** Position is larger than available capital

**Cause:** `max(1, max_shares)` guarantees at least 1 share even if capital is insufficient

**Impact:** At $50 capital with $100 stock, you're 200% leveraged

**Fix:** Add check: `if adjusted_price > available_capital * max_position_size: return None`

### 2. Volatility Blindness
**Symptom:** Same dollar position in AAPL (15% annual vol) and TSLA (60% annual vol)

**Cause:** Fixed fractional ignores volatility

**Impact:** TSLA position is 4× riskier in real terms

**Fix:** ATR-based sizing (already coded in `BaseStrategy`, needs wiring)

### 3. Portfolio Over-Concentration
**Symptom:** 5 correlated positions × 20% each = 100% effective exposure

**Cause:** `max_position_size` is per-position, not portfolio-level

**Impact:** Correlated drawdown hits all positions simultaneously

**Current mitigation:** `PortfolioConfig.weights` caps total allocation

---

## Key Insights

### Position Sizing > Signal Quality
A perfect signal with bad sizing loses money. A mediocre signal with proper sizing survives.

### The Unrealized Gap
TSRL tracks `running_capital` (realized), not mark-to-market equity. During a trade, your position sizing uses stale capital estimates. This means the first trade after a big win is appropriately sized, but the second trade after an unrealized gain is undersized.

### Implementation Priority
If you could change one thing in the current engine, wire `calculate_position_size()` to the backtest loop using ATR-based stops. This single change would make position sizing volatility-aware and eliminate the biggest gap in the current system.

---

## Related Concepts
- [[Risk Metrics]] — Kelly criterion calculation
- [[Trade Lifecycle]] — Where position sizing happens (Stage 2)
- [[Event System]] — The loop that calls position sizing
- [[Strategy Design]] — Principle 5: Risk management is part of strategy

## Implementation References
- `src/engine/backtest/engine.py:231-233` — Current fixed fractional
- `src/strategies/base.py:136-152` — Unused ATR-based sizer
- `src/engine/backtest/advanced_engine.py:39-49` — RiskManagementConfig
