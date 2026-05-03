# Strategy Design Principles

## Definition
Core principles for designing, implementing, and evaluating trading strategies that survive contact with real markets.

## Why It Matters
- **Avoid expensive lessons**: Learn from others' failures, not just your own
- **Faster iteration**: Clear design patterns reduce trial-and-error
- **Production readiness**: Strategies that work in backtest AND live trading

---

## The Strategy Interface (In My System)

All strategies inherit from `BaseStrategy` (`src/strategies/base.py`):

```python
class BaseStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass
    
    @property
    @abstractmethod
    def version(self) -> str: pass
    
    @property
    @abstractmethod
    def description(self) -> str: pass
    
    @property
    @abstractmethod
    def strategy_type(self) -> str: pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame: pass
    
    def entry_conditions(self, data: pd.DataFrame, idx: int) -> bool: ...
    def exit_conditions(self, data: pd.DataFrame, idx: int) -> bool: ...
    def risk_management(self, position, data, idx) -> RiskManagementResult: ...
```

**Design rationale:**
- **Name/Version**: Track strategy iterations (v1.0 → v2.0 after major changes)
- **Strategy Type**: Categorize (momentum, mean_reversion, breakout, ml)
- **generate_signals()**: Core logic — must be implemented
- **entry/exit_conditions**: Optional overrides (default to signal values)
- **risk_management**: Optional position-level risk controls

---

## Principle 1: Edge Must Be Quantifiable

**Bad:** "This strategy feels profitable"

**Good:** "This strategy has 55% win rate, 1.5 profit factor, 0.8 Sharpe"

**Implementation:**
```python
# Every strategy must produce measurable signals
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    df["signal"] = 0  # Quantifiable: 1 = buy, -1 = sell, 0 = flat
    df["signal_strength"] = 0.5  # Optional: confidence metric
    return df
```

**Why it matters:** If you can't measure it, you can't improve it

---

## Principle 2: Parameters Must Have Economic Rationale

**Bad:** "I tried 100 parameter combinations and picked the best"

**Good:** "12/26 EMA reflects weekly/bi-weekly trading cycles"

**Valid rationales:**
- **Market cycles**: Weekly, monthly, quarterly patterns
- **Behavioral**: Trader psychology (support/resistance levels)
- **Statistical**: Standard deviation, percentiles, mean reversion
- **Fundamental**: Earnings cycles, economic data releases

**Invalid rationales:**
- "It worked in backtest"
- "Someone on Twitter uses this"
- Random numbers

---

## Principle 3: Entry Is Only Half The Trade

A complete strategy specifies:
1. **Entry trigger**: When to enter
2. **Exit trigger**: When to exit (profit or loss)
3. **Position size**: How much to risk
4. **Invalidation**: When the thesis is broken

**Example (EMA Crossover):**
```python
# Entry
entry = fast_ema > slow_ema and prev_fast_ema <= prev_slow_ema

# Exit (full position reversal)
exit = fast_ema < slow_ema and prev_fast_ema >= prev_slow_ema

# Position size (from BaseStrategy)
position_size = (capital * risk_per_trade) / (entry_price - stop_price)

# Invalidation (not implemented — should be!)
invalidation = price < entry_price * 0.95  # 5% stop loss
```

---

## Principle 4: Strategy Type Determines Behavior

### Momentum Strategies
**Philosophy:** Trends persist

**Entry:** Breakout above resistance, MA crossover

**Exit:** Trend breaks (MA cross opposite direction)

**Win rate:** 40-50%

**Profit factor:** 1.5-2.5 (big wins, small losses)

**Examples:** [[EMA Crossover]], [[MACD Strategy]], [[Breakout Strategy]]

---

### Mean Reversion Strategies
**Philosophy:** Price returns to fair value

**Entry:** Price at extreme (RSI < 30, Bollinger Band touch)

**Exit:** Price at mean (middle band, RSI 50)

**Win rate:** 50-60%

**Profit factor:** 1.2-1.6 (many small wins, few large losses)

**Examples:** [[Bollinger Bands Strategy]], [[RSI Mean Reversion]]

---

### Breakout Strategies
**Philosophy:** Consolidation → expansion → trend

**Entry:** Price breaks range with volume

**Exit:** Range re-entry or trailing stop

**Win rate:** 35-45%

**Profit factor:** 2.0-3.0 (rare but big wins)

**Examples:** [[Breakout Strategy]], [[Bollinger Bands]] (band break)

---

### ML Strategies
**Philosophy:** Patterns too complex for rules can be learned

**Entry:** Model prediction (classification or regression)

**Exit:** Model prediction reversal or time-based

**Win rate:** 45-55% (slight edge)

**Profit factor:** 1.1-1.5

**Examples:** `src/ml/strategies/ml_strategies.py`

---

## Principle 5: Risk Management Is Part Of Strategy

**Not optional:** A strategy without risk management is gambling

**Three levels of risk control:**

### Level 1: Trade-Level
```python
# Stop loss
stop_loss = entry_price * 0.95  # 5% stop

# Take profit
take_profit = entry_price * 1.10  # 10% target

# Trailing stop
trailing_stop = max_price * 0.95  # 5% below highest price
```

### Level 2: Portfolio-Level
```python
# Max position size
max_position = capital * 0.20  # 20% max per position

# Max correlation
if correlation_with_existing > 0.7:
    skip_trade  # Don't add correlated risk
```

### Level 3: Strategy-Level
```python
# Max drawdown circuit breaker
if strategy_drawdown > 0.20:
    stop_trading  # 20% max drawdown

# Cooling off period
if consecutive_losses >= 5:
    reduce_position_size(0.5)  # Cut size in half
```

**In my system:** `RiskManagementResult` (`src/strategies/base.py:39-47`)

---

## Principle 6: Avoid Look-Ahead Bias

**Definition:** Using information that wasn't available at decision time

**Common mistakes:**

### Mistake 1: Using Close Price For Entry
```python
# WRONG: Signal calculated using close, entry at same close
if signal == 1:
    entry_price = current_bar["close"]  # Look-ahead!

# CORRECT: Signal known at close, entry at next bar
if signal == 1:
    pending_entry = True  # Execute next bar's open
```

**Fixed in my system** (`engine.py:198-201`):
```python
# Set pending signal for next bar - DO NOT enter immediately
pending_signal = signal
```

---

### Mistake 2: Repainting Indicators
```python
# WRONG: Using current bar's high/low in indicator calculation
highest = df["high"].rolling(20).max()  # Includes current bar

# For backtesting, this is fine (you know the bar's range)
# For live trading, you don't know the high until bar closes

# CORRECT: Use previous bar's value for live simulation
highest = df["high"].shift(1).rolling(20).max()
```

---

### Mistake 3: Future Data In Features
```python
# WRONG: Using adjusted close (includes future dividends/splits)
df["returns"] = df["adjusted_close"].pct_change()

# CORRECT: Use raw close for backtesting
df["returns"] = df["close"].pct_change()
```

---

## Principle 7: One Edge Per Strategy

**Bad:** "This strategy uses RSI + MACD + Bollinger Bands + volume + ..."

**Good:** "This strategy exploits mean reversion (RSI). Other indicators are filters."

**Why:**
- Multiple edges = overfitting
- Hard to diagnose failures
- Can't tell which component adds value

**Valid multi-indicator use:**
- Primary indicator: Generates signal
- Secondary indicator: Filters signals (reduces false positives)
- Tertiary indicator: Position sizing (confidence weighting)

**Example:**
```python
# Primary: RSI mean reversion
rsi_oversold = rsi < 30

# Filter: ADX confirms ranging market (not trending)
adx_ranging = adx < 25

# Entry: Both conditions must be true
entry = rsi_oversold and adx_ranging
```

---

## Principle 8: Strategies Decay

**Reality:** A strategy that works today may not work in 6 months

**Causes:**
1. **Regime change:** Bull → bear → sideways
2. **Crowding:** Too many traders using same signals
3. **Arbitrage:** Edge gets traded away

**Mitigation:**
- **Walk-forward analysis:** Regularly test out-of-sample
- **Strategy rotation:** Switch strategies based on regime
- **Parameter adaptation:** Adjust parameters quarterly

**In my system:** `src/engine/walkforward/walkforward.py`

---

## Failure Cases & Edge Cases

### 1. Overfitting
**Symptom:** Perfect backtest, terrible live performance

**Detection:**
- In-sample Sharpe > 2.0, out-of-sample Sharpe < 0.5
- Parameter sensitivity: Small changes cause large performance swings
- Too many parameters relative to trades

**Prevention:**
- ≤ 1 parameter per 100 trades
- Walk-forward validation
- Out-of-sample testing

---

### 2. Curve-Fitting
**Symptom:** Strategy works on specific assets but not others

**Cause:** Parameters tuned to specific asset behavior

**Example:**
```python
# Works on AAPL (tech stocks)
fast_period = 12, slow_period = 26

# Fails on XOM (energy stocks)
# Different sector = different cycle
```

**Prevention:**
- Test on diverse asset classes
- Use universal parameters (or sector-specific tuning)

---

### 3. Data Snooping
**Symptom:** "Discovered" pattern that doesn't repeat

**Cause:** Testing too many hypotheses on same dataset

**Example:**
```python
# Test 100 parameter combinations
# Best one: fast=13, slow=29
# This isn't discovery — it's statistics
```

**Prevention:**
- Holdout dataset (never used in development)
- Bonferroni correction: Adjust significance for multiple tests

---

### 4. Regime Blindness
**Symptom:** Strategy works in bull market, fails in bear

**Cause:** Strategy designed for one regime only

**Example:**
- Long-only momentum: Works 2010-2020 (bull), fails Q1 2020 (crash)

**Prevention:**
- Test across multiple regimes
- Add regime detection (ADX, volatility, trend filters)
- Have multiple strategies for different regimes

---

## Key Insights

### The Edge Equation
```
Edge = (Win Rate × Avg Win) - (Loss Rate × Avg Loss) - Costs

Costs = Commission + Slippage + Market Impact
```

**Implication:** A 60% win rate means nothing if avg_loss >> avg_win

---

### The Parameter Stability Test
```python
# Test robustness
for param in range(best_param * 0.8, best_param * 1.2, step=5%):
    result = backtest(strategy, param)
    
# If performance varies > 50%, parameter is unstable
# Unstable parameters = overfitting
```

---

### The Strategy Lifecycle
```
Discovery → Backtest → Optimization → Paper Trade → Live → Decay → Retirement
```

**Typical lifespan:** 6 months to 3 years for retail strategies

**Institutional edge:** Lasts longer (better tech, faster execution)

---

## Related Concepts
- [[Backtesting]] — How strategies are tested
- [[Risk Metrics]] — How strategy performance is measured
- [[Walk-Forward Analysis]] — Out-of-sample validation
- [[Base Strategy]] — Implementation interface

## Implementation References
- `src/strategies/base.py` — Base class
- `src/strategies/registry.py` — Auto-discovery pattern
- `src/strategies/momentum/` — Momentum strategy examples
- `src/strategies/mean_reversion/` — Mean reversion examples
