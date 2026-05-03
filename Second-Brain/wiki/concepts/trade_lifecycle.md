# Trade Lifecycle

## Definition
The complete journey of a trade from signal generation to realized P&L. Understanding this lifecycle reveals where costs accumulate, where bugs hide, and why backtest results diverge from reality.

## Why It Matters
- **Cost awareness**: Commission and slippage are applied at specific points — miss one and your backtest lies
- **Debugging**: When a trade's P&L looks wrong, trace it through each lifecycle stage
- **System extension**: Adding features (partial fills, position scaling) requires understanding the current flow

## In My System

### The Full Pipeline

```
Strategy.generate_signals(data)
    → signal = 1 (buy) or -1 (sell)
        → Engine._open_position()
            → Apply slippage to entry price
            → Calculate position size (capital × max_position_size / price)
            → Create Position object
                → Monitor each bar for exit conditions
                    → Engine._close_position()
                        → Apply slippage to exit price
                        → Calculate commission (entry_value + exit_value) × rate
                        → Create Trade object with final P&L
                            → running_capital += trade.pnl
```

---

### Stage 1: Signal Generation

**Where:** `strategy.generate_signals(data)` → returns DataFrame with `signal` column

**Output:** `1` (long), `-1` (short), `0` (flat)

**Key detail:** Signal is computed using the *entire* data slice up to current bar. The `shift(1)` or `pending_signal` pattern then prevents acting on current bar's close.

---

### Stage 2: Position Opening (`engine.py:216-244`)

```python
def _open_position(self, symbol, timestamp, price, side, data, idx, config, capital):
    # Step 1: Apply slippage
    adjusted_price = price * (1 + slippage)  # Buy: pay more
    
    # Step 2: Calculate quantity
    max_shares = int((available_capital * max_position_size) / adjusted_price)
    quantity = max(1, max_shares)  # Always buy at least 1 share
    
    # Step 3: Create Position
    return Position(entry_price=adjusted_price, quantity=quantity, side=side)
```

**Cost applied here:** Slippage (entry)

**Design decision:** Position size is capped at `max_position_size` (default 20%) of available capital. This is a fixed fractional approach, not ATR-based.

**Edge case:** `max(1, max_shares)` — if capital is too low for even 1 share at 20%, you still buy 1. This can over-allocate in low-capital scenarios.

---

### Stage 3: Position Monitoring

**Where:** The main `for idx in range(len(signals))` loop

**What happens each bar:**
1. Update trailing stop price (if enabled, advanced engine only)
2. Check exit conditions (stop/TP/trailing/signal)
3. Track `entry_high` and `entry_low` for trailing stop calculation

**Not tracked:** Unrealized P&L. The system only knows realized P&L after trade close.

---

### Stage 4: Position Closing (`engine.py:246-276`)

```python
def _close_position(self, position, exit_price, exit_timestamp, config):
    # Step 1: Apply slippage (opposite direction)
    adjusted_exit = exit_price * (1 - slippage)  # Sell: receive less
    
    # Step 2: Calculate commission
    # Commission on BOTH sides (entry + exit)
    commission = (entry_price * quantity + adjusted_exit * quantity) * commission_rate
    
    # Step 3: Calculate slippage cost
    slippage_cost = abs(exit_price - adjusted_exit) * quantity
    
    # Step 4: Create Trade with P&L
    trade = Trade(
        entry_price=position.entry_price,
        exit_price=adjusted_exit,
        commission=commission,
        slippage=slippage_cost,
    )
    # trade.pnl = (exit - entry) * qty - commission  (computed in Trade entity)
```

**Costs applied here:** Slippage (exit) + Commission (both sides)

---

### Stage 5: Capital Update

```python
# engine.py:194-195
if trade.pnl is not None:
    running_capital += trade.pnl
```

**This affects future position sizes.** Winning trades → bigger positions. Losing trades → smaller positions. This is compounding — it amplifies both gains and losses.

---

## Cost Model

| Cost Type | When Applied | Formula | Default |
|-----------|-------------|---------|---------|
| Entry Slippage | Position open | `price × (1 + slippage)` | 0.05% |
| Exit Slippage | Position close | `price × (1 - slippage)` | 0.05% |
| Commission | Position close | `(entry_value + exit_value) × rate` | 0.1% |
| Total per round-trip | — | ~0.3% of trade value | — |

**For a $100,000 position:**
- Entry slippage: $50
- Exit slippage: $50
- Commission: $200 (0.1% of $200,000 notional)
- **Total: $300 per round-trip**

At 20 trades/year: **$6,000/year in execution costs**

---

## Entity Flow

```
Position (open state)       Trade (closed state)
├── symbol                  ├── symbol
├── entry_time              ├── entry_time
├── entry_price (slippage-adjusted) ├── entry_price
├── quantity                ├── quantity
├── side (LONG/SHORT)       ├── side
├── current_price           ├── exit_time
└── (no P&L yet)            ├── exit_price (slippage-adjusted)
                            ├── commission
                            ├── slippage
                            ├── status (CLOSED)
                            └── pnl (computed)
```

**Key:** `Position` → `Trade` is a one-way conversion at close. You cannot reopen a closed trade.

---

## Failure Cases & Edge Cases

### 1. Commission Double-Count
**Risk:** Commission applied on both entry and exit in `_close_position`, but entry slippage was already applied in `_open_position`

**Reality in code:** Commission is calculated on raw values, slippage on adjusted values — no double-count. But the naming can confuse during debugging.

### 2. Negative Capital
**Symptom:** `running_capital` goes negative after a series of losses

**Cause:** No circuit breaker — engine will keep trading with negative capital

**Impact:** Position sizes become negative (nonsensical)

**Fix needed:** Add `if running_capital <= 0: break` to the event loop

### 3. End-of-Data Force Close
**Symptom:** Last trade always has worse performance

**Cause:** Open positions are force-closed at the last bar's close (`engine.py:203-212`)

**Impact:** This isn't a "real" trade — it's an accounting entry. Inflates trade count.

---

## Key Insights

### The 0.3% Tax
Every round-trip costs ~0.3% by default. A strategy needs **at least 0.3% edge per trade** to break even. This eliminates most high-frequency strategies on daily bars.

### Compounding Works Both Ways
Because `running_capital` updates after each trade, a drawdown reduces future position sizes. This is mathematically equivalent to fractional Kelly betting — good for survival, bad for recovery speed.

### Position ≠ Trade
A Position is an open state machine. A Trade is a closed historical record. The engine converts one to the other at exit. This distinction matters for portfolio tracking — you can't "query open positions" from the Trade table.

---

## Related Concepts
- [[Event System]] — The loop that drives this lifecycle
- [[Risk Metrics]] — Computed from the Trade objects this lifecycle produces
- [[Position Sizing]] — How quantity is determined at Stage 2
- [[Backtesting]] — The orchestration layer that triggers this lifecycle

## Implementation References
- `src/engine/backtest/engine.py:216-276` — Open/close position
- `src/domain/entities/trade.py` — Trade entity (P&L calculation)
- `src/domain/entities/position.py` — Position entity (open state)
- `src/application/services/backtest_service.py:64-135` — Orchestration
