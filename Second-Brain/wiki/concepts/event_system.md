# Event System

## Definition
The execution model that transforms strategy signals into real trades through a sequential event pipeline. TSRL uses a **bar-by-bar event loop**, not a message queue — signals are evaluated per bar and converted into position changes through a priority chain.

## Why It Matters
- **Execution realism**: Without event ordering, backtests assume perfect fills — live trading will punish this
- **Look-ahead prevention**: The event pipeline enforces temporal ordering (signal → next bar entry)
- **Exit priority**: Stop-loss, take-profit, trailing stop, and signal exits compete — only one wins per bar
- **Extensibility**: New exit types (time-based, volatility-based) plug into the priority chain

## In My System

### The Core Event Loop (`src/engine/backtest/engine.py:121-213`)

```
For each bar:
  1. Check pending_signal from previous bar → open position
  2. If no position: check for new signal → open position
  3. If in position: check exit conditions → close + set pending_signal
```

**This is NOT a traditional event bus.** There's no `EventEmitter` or pub/sub. It's a procedural loop with implicit event ordering baked into the `if/elif` chain.

### The Pending Signal Mechanism

The most critical design decision in the engine:

```python
# engine.py:198-201
# Set pending signal for next bar - DO NOT enter immediately
# This fixes look-ahead bias: signal is known at close,
# but entry happens at next bar's open
pending_signal = signal
```

**Why this exists:**
- Signal is calculated using the current bar's close price
- You can't act on the close price *at* the close — it's already happened
- Entry must happen at the next bar's open (simulated as next bar's close for simplicity)
- Without this, backtests show ~15-30% higher returns than reality

### Exit Priority Chain (Advanced Engine)

The `advanced_engine.py` introduces a strict priority order:

```
1. Stop Loss     → checked first (capital protection)
2. Take Profit   → checked if stop not hit
3. Trailing Stop  → checked if neither hit
4. Signal Exit   → checked last (strategy-driven)
```

**Key implementation** (`advanced_engine.py:171-229`):
```python
if risk.enable_stop_loss:
    # Check stop loss FIRST — always
    if position.side == PositionSide.LONG:
        stop_price = position.entry_price * (1 - risk.stop_loss_pct)
        if low_price <= stop_price:
            exit_trade = True
            exit_reason = "stop_loss"

if risk.enable_take_profit and not exit_trade:
    # Only check TP if stop wasn't hit
    ...

if risk.enable_trailing_stop and not exit_trade:
    # Only check trailing if neither hit
    ...

if not exit_trade:
    # Signal exit is the fallback
    if position.side == PositionSide.LONG and signal == -1:
        exit_trade = True
        exit_reason = "signal"
```

**Why this order matters:** In a single bar, price can hit both stop and target (gap through). The priority determines which exit is used — stop first protects capital.

---

## Engine Comparison

| Aspect | Event-Driven (`engine.py`) | Advanced (`advanced_engine.py`) | Vectorized (`engine.py::Vectorized`) |
|--------|---------------------------|-------------------------------|-------------------------------------|
| Execution | Bar-by-bar loop | Bar-by-bar with risk mgmt | Matrix operations |
| Stop Loss | ❌ Not supported | ✅ SL/TP/Trailing | ❌ Not supported |
| Look-ahead fix | `pending_signal` | ❌ Direct reversal | `shift(1)` |
| Speed | ~100-500ms | ~200-800ms | ~10-50ms |
| Use case | Final validation | Production simulation | Parameter scanning |

**Critical gap:** The advanced engine does NOT use `pending_signal`. On exit+reversal, it enters immediately at the same bar. This introduces slight look-ahead bias that the base engine fixes.

---

## Failure Cases & Edge Cases

### 1. Simultaneous Entry-Exit
**Symptom:** Strategy exits and re-enters on the same bar

**In base engine:** Prevented by `pending_signal` — entry delayed to next bar

**In advanced engine:** Allowed — enters immediately on reversal (`advanced_engine.py:555-580`)

**Impact:** ~0.1-0.5% per-trade difference in backtest results

### 2. Gap-Through Risk
**Symptom:** Price gaps through both stop and target in one bar

**Current behavior:** Stop loss wins (checked first in priority chain)

**Reality:** Fill at stop price, not at stop level (slippage on gaps not modeled)

### 3. Running Capital Drift
**Symptom:** Late trades use stale capital estimate

**Cause:** `running_capital` only updates on trade close, not on unrealized P&L

**Impact:** Position sizing is based on realized capital, not actual equity

---

## Key Insights

### Event-Driven ≠ Event Bus
TSRL's "event-driven" engine is really a **procedural state machine** with position as state. This is fine for single-symbol backtesting. Portfolio backtesting (multiple symbols) uses the `PortfolioEngine` which runs independent state machines per symbol.

### The Vectorized Shortcut
Vectorized mode skips the event loop entirely — it computes all signals, shifts by 1, and multiplies by returns. This is mathematically equivalent to the event loop *only if there are no complex exit conditions*. The moment you add stop-loss or trailing stops, vectorized breaks.

### Why Not A Real Event Bus?
Performance. A real event bus (e.g., `asyncio` queues) adds overhead for no benefit in backtesting. Every event is synchronous and sequential. For live trading, a real event bus would be necessary.

---

## Related Concepts
- [[Backtesting]] — The engines that implement this event model
- [[Trade Lifecycle]] — From signal to P&L through the event chain
- [[Position Sizing]] — How running capital affects position sizes
- [[Architecture Decisions]] — Why procedural over event bus

## Implementation References
- `src/engine/backtest/engine.py:121-213` — Base event loop
- `src/engine/backtest/advanced_engine.py:152-620` — Advanced with risk management
- `src/engine/backtest/engine.py:322-460` — Vectorized alternative
