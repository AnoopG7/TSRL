# Bollinger Bands Strategy

## Definition
A mean reversion strategy using Bollinger Bands (price ± N standard deviations) to identify overbought/oversold conditions.

**Core thesis:** Price tends to revert to the mean (middle band) after touching the outer bands, creating predictable bounce opportunities.

## Why It Matters
- **Mean reversion foundation**: Teaches counter-trend trading principles
- **Volatility adaptive**: Bands expand/contract with market conditions
- **Visual clarity:** Easy to see relative price position
- **Multi-timeframe**: Works on intraday to weekly charts

## In My System

**Location:** `src/strategies/mean_reversion/bollinger_bands.py::BollingerBandsStrategy`

**Registration:**
```python
@register_strategy("bollinger_bands")
class BollingerBandsStrategy(BaseStrategy):
```

**Strategy metadata:**
- **Name:** "bollinger_bands"
- **Type:** "mean_reversion"
- **Data requirements:** `["close"]` (can use high/low for band touches)

---

## Implementation Details

### Default Parameters
```python
def _set_default_parameters(self) -> None:
    self._params = {
        "period": 20,
        "std_dev": 2.0,
    }
```

**Why these values?**
- 20 period: One trading month (standard lookback)
- 2.0 std dev: Captures ~95% of price action (normal distribution)

---

### Band Calculation
```python
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    
    period = int(self._params["period"])
    std_dev = float(self._params["std_dev"])
    
    # Middle Band = Simple Moving Average
    sma = df["close"].rolling(window=period).mean()
    
    # Standard Deviation
    std = df["close"].rolling(window=period).std()
    
    # Upper/Lower Bands
    df["upper_band"] = sma + (std * std_dev)
    df["middle_band"] = sma
    df["lower_band"] = sma - (std * std_dev)
    
    # Signals
    df["signal"] = 0
    df.loc[df["close"] <= df["lower_band"], "signal"] = 1   # Buy (oversold)
    df.loc[df["close"] >= df["upper_band"], "signal"] = -1  # Sell (overbought)
    
    return df
```

**Key components:**

| Band | Formula | Interpretation |
|------|---------|----------------|
| **Upper** | SMA + (2σ × std) | Overbought territory |
| **Middle** | SMA(20) | Mean / fair value |
| **Lower** | SMA - (2σ × std) | Oversold territory |

---

### Band Width (Volatility Indicator)
```python
# Not explicitly calculated but derivable
band_width = (upper_band - lower_band) / middle_band
```

**What it tells you:**
- **Narrow bands:** Low volatility → potential breakout incoming
- **Wide bands:** High volatility → trend may be exhausting

**The Squeeze:**
```
Period: Low volatility (narrow bands)
  ↓
Breakout: Price escapes band with volume
  ↓
Trend: Price rides the band
```

---

### %B Indicator (Position Within Bands)
```python
# Not implemented but useful
percent_b = (close - lower_band) / (upper_band - lower_band)
```

**Interpretation:**
| %B | Meaning |
|----|---------|
| > 1.0 | Above upper band (overbought) |
| 0.8-1.0 | Near upper band |
| 0.4-0.6 | Middle (neutral) |
| 0-0.2 | Near lower band |
| < 0 | Below lower band (oversold) |

---

## Entry/Exit Logic

### Current Implementation
```python
# Entry: Price at or below lower band (oversold)
def entry_conditions(self, data, idx):
    return data["close"].iloc[idx] <= data["lower_band"].iloc[idx]

# Exit: Price at or above middle band (mean reached)
def exit_conditions(self, data, idx):
    return data["close"].iloc[idx] >= data["middle_band"].iloc[idx]
```

**Philosophy:**
- Buy at extreme (lower band)
- Exit at mean (middle band)
- Don't greed for the opposite band

---

## Enhanced Entry/Exit Patterns

### Pattern 1: Band Walk Exit
```python
# Instead of exiting at middle band, ride to upper band
# Exit when price closes below middle band (trend broken)

def exit_conditions(self, data, idx):
    # Exit if price closes below middle band after being above it
    return (data["close"].iloc[idx] < data["middle_band"].iloc[idx] and 
            data["close"].iloc[idx-1] >= data["middle_band"].iloc[idx-1])
```

**Trade-off:** More profit potential, but more giveback

---

### Pattern 2: Double Bottom Entry
```python
# Wait for two touches of lower band before entering
# Higher probability than single touch

def entry_conditions(self, data, idx):
    at_lower = data["close"] <= data["lower_band"]
    
    # Find previous touch within last 10 bars
    prev_touch = at_lower.shift().rolling(10).sum() > 0
    
    return at_lower.iloc[idx] and prev_touch.iloc[idx]
```

**Rationale:** Second test of support has higher success rate

---

### Pattern 3: RSI Confluence
```python
# BB touch + RSI oversold = higher probability
def entry_conditions(self, data, idx):
    bb_oversold = data["close"].iloc[idx] <= data["lower_band"].iloc[idx]
    rsi_oversold = data["rsi"].iloc[idx] < 30
    
    return bb_oversold and rsi_oversold
```

**Why it works:** Both indicators measure different aspects of "oversold"

---

## Parameter Sensitivity

### Period
| Value | Effect | Best For |
|-------|--------|----------|
| 10-14 | Tight bands, frequent signals | Scalping, crypto |
| 20 (default) | Balanced | Swing trading |
| 50-100 | Wide bands, rare signals | Position trading |

### Standard Deviations
| Value | Effect | Win Rate |
|-------|--------|----------|
| 1.5 | More signals, lower quality | ~45% |
| 2.0 (default) | Balanced | ~50-55% |
| 2.5-3.0 | Fewer signals, higher quality | ~55-60% |

**Key insight:** Higher std dev = rarer signals but better win rate

---

## Failure Cases & Edge Cases

### 1. Band Walk (Trend Continuation)
**Symptom:** Price touches lower band, you buy, price continues down along the band

**Cause:** Strong downtrends "walk the band" — price hugs lower band for extended periods

**Visual pattern:**
```
Price: ↓↓↓↓↓ (stays at lower band)
Lower Band: ↓↓↓ (moving down with price)
Result: You catch falling knife
```

**Detection:**
```python
# Count consecutive bars at/touching lower band
consecutive_bars = (df["close"] <= df["lower_band"]).rolling(5).sum()
if consecutive_bars >= 3:
    # Strong downtrend - don't buy the dip
```

**Mitigation:**
- Wait for price to CLOSE below band, not just touch
- Add RSI filter: Require RSI < 30 (not just BB touch)
- Use stop-loss: Exit if price drops X% below entry

---

### 2. Breakout Fakeout
**Symptom:** Price breaks upper band (short signal), then rockets higher

**Cause:** Breakouts from Bollinger Band squeezes can trend 2-3 standard deviations

**Example:**
```
Earnings beat → Price gaps above upper band → You short
Price continues up 20% → Massive loss
```

**Mitigation:**
- Never short breakouts without confirmation
- Wait for failed breakout (price returns inside bands)
- Use hard stop-loss above recent high

---

### 3. Low Volatility Trap
**Symptom:** Bands narrow, no signals for weeks

**Cause:** Very low volatility → price never touches bands

**Detection:**
```python
band_width = (df["upper_band"] - df["lower_band"]) / df["middle_band"]
if band_width < band_width.rolling(60).min() * 1.1:
    # Bands at multi-month narrow - expect breakout soon
```

**Action:** Stand aside, wait for breakout direction

---

### 4. Earnings Gap Risk
**Symptom:** Stop-loss skipped, massive overnight loss

**Cause:** Gaps through all bands simultaneously

**Example:**
```
Day close: $100 (at lower band, you buy)
Stop-loss: $95
Next open: $80 (earnings disaster)
Result: -20% instead of -5%
```

**Mitigation:**
- Reduce position size before earnings
- Use options for defined risk
- Close positions before major news events

---

## Performance Characteristics

### Typical Metrics (S&P 500 stocks, 2010-2023)
| Metric | Value |
|--------|-------|
| Win Rate | 50-60% |
| Profit Factor | 1.2-1.6 |
| Sharpe Ratio | 0.6-1.0 |
| Max Drawdown | 20-30% |
| Avg Trade Duration | 5-15 days |
| Trades per Year | 20-40 |

**Comparison to momentum strategies:**
- Higher win rate, lower profit factor
- Shorter holding period
- More trades (higher commission impact)

---

## Regime Dependence
| Market Regime | Performance |
|---------------|-------------|
| Sideways/ranging | Excellent (mean reversion thrives) |
| Slow uptrend | Good (buys dips) |
| Slow downtrend | Good (shorts rallies) |
| Strong trend | Poor (gets run over) |
| High volatility | Mixed (more signals, more risk) |

---

## Key Insights

### The 95% Rule
> "With 2 standard deviations, ~95% of price action should stay within bands. When it breaks out, pay attention."

**Implication:** A close outside the bands is a 2-sigma event — statistically significant

---

### Mean Reversion ≠ Contrarian
Mean reversion works because:
1. **Overreaction:** Price overshoots fair value
2. **Profit-taking:** Traders lock in gains at extremes
3. **Arbitrage:** Institutional money flows to fair value

**It's not about being contrarian — it's about statistical gravity.**

---

### Volatility Clustering
> "Volatility begets volatility. Narrow bands → explosive move → wide bands → consolidation"

**Cycle:**
1. Compression (narrow bands)
2. Expansion (breakout)
3. Trend (band walk)
4. Stabilization (bands contract)
5. Repeat

**Trading implication:** After a big move, expect continued volatility

---

## Usage Examples

### CLI
```bash
# Basic backtest
PYTHONPATH=. python -m src.cli backtest \
  --strategy bollinger_bands \
  --symbol AAPL \
  --start-date 2020-01-01

# Tighter bands (more signals)
PYTHONPATH=. python -m src.cli backtest \
  --strategy bollinger_bands \
  --strategy-params '{"period": 14, "std_dev": 1.5}' \
  --symbol SPY
```

### API
```python
POST /api/v1/backtests/run
{
  "strategy_name": "bollinger_bands",
  "symbol": "AAPL",
  "parameters": {"period": 20, "std_dev": 2.0}
}
```

---

## Related Strategies
- [[RSI Mean Reversion]] — Similar philosophy, different indicator
- [[EMA Crossover]] — Opposite approach (momentum vs mean reversion)
- [[Breakout Strategy]] — Trades the band break, not the bounce

## Implementation References
- `src/strategies/mean_reversion/bollinger_bands.py` — Full implementation
- `src/strategies/base.py` — Base class interface
- `src/engine/backtest/engine.py` — Execution engine
