# Volume Strategies

## Definition
Strategies that use trading volume as the primary or confirming signal. Based on the principle that **volume precedes price** — unusual volume activity signals institutional interest before price moves visibly.

## Why It Matters
- **Confirmation filter**: Price breakouts without volume are often fakeouts
- **Institutional footprint**: Large players can't hide volume — it leaks into the tape
- **Regime clue**: Volume expansion → new trend starting. Volume contraction → consolidation

## In My System

Two volume strategies registered in `src/strategies/momentum/volume_strategies.py`:

---

### 1. Volume Profile Strategy (`volume_profile`)

**Core logic:** Buy on volume spike + price up. Sell on volume dry-up + price down.

```python
@register_strategy("volume_profile")
class VolumeProfileStrategy(BaseStrategy):
```

**Signal generation:**
```python
def generate_signals(self, data):
    avg_volume = volume.rolling(window=self._lookback).mean()
    
    # Buy: volume spike + price rising
    volume_spike = volume > (avg_volume * self._volume_threshold)
    price_up = close > close.shift(1)
    signals.loc[volume_spike & price_up, "signal"] = 1
    
    # Sell: volume dry-up + price falling
    volume_drop = volume < (avg_volume * 0.5)
    price_down = close < close.shift(1)
    signals.loc[volume_drop & price_down, "signal"] = -1
```

**Parameters:**
| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `lookback` | 20 | 5-100 | Baseline volume window |
| `volume_threshold` | 1.5 | 1.0-5.0 | Multiplier for "unusual" volume |

**Key insight:** The buy and sell conditions are **asymmetric**:
- Buy requires volume > 1.5× average (spike)
- Sell requires volume < 0.5× average (dry-up)

This means the strategy is biased long — it enters on volume surges and exits on volume exhaustion. The sell signal is a weakness indicator, not a reversal signal.

---

### 2. Volume Breakout Strategy (`volume_breakout`)

**Core logic:** Price breaks above N-day high WITH above-average volume = confirmed breakout.

```python
@register_strategy("volume_breakout")
class VolumeBreakoutStrategy(BaseStrategy):
```

**Signal generation:**
```python
def generate_signals(self, data):
    high = close.rolling(window=self._period).max()
    volume_ma = volume.rolling(window=self._volume_ma_period).mean()
    
    # Buy: price breaks above channel + volume confirms
    breakout = (close > high.shift(1)) & (volume > volume_ma)
    signals.loc[breakout, "signal"] = 1
    
    # Sell: price drops + volume confirms
    breakdown = (close < close.shift(1)) & (volume > volume_ma)
    signals.loc[breakdown, "signal"] = -1
```

**Parameters:**
| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `period` | 20 | 5-100 | Breakout channel width |
| `volume_ma_period` | 20 | 5-50 | Volume baseline |

**How it differs from [[Breakout]] strategy:**
- Breakout strategy: Price breaks channel → signal (no volume check)
- Volume Breakout: Price breaks channel AND volume above MA → signal

The volume filter eliminates ~40% of signals (mostly the false ones).

---

## Volume Indicators (In Feature Engineering)

The ML feature pipeline computes several volume indicators (`features.py:102-117`):

### OBV (On-Balance Volume)
```python
obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
```
**What it shows:** Cumulative volume flow. Rising OBV with rising price = trend confirmed. Rising OBV with flat price = accumulation (smart money buying).

### VWAP (Volume-Weighted Average Price)
```python
tp = (high + low + close) / 3
vwap = (tp * volume).cumsum() / volume.cumsum()
```
**What it shows:** Fair value price weighted by volume. Price above VWAP = bullish intraday bias.

### Volume Ratio
```python
volume_ratio_{window} = volume / volume.rolling(window).mean()
```
**What it shows:** Current volume relative to average. Ratio > 2 = very unusual activity.

### MFI (Money Flow Index)
```python
mfi = 100 - (100 / (1 + positive_money_flow / negative_money_flow))
```
**What it shows:** RSI weighted by volume. MFI < 20 = oversold with volume confirmation.

---

## Failure Cases & Edge Cases

### 1. Volume Spike on Bad News
**Symptom:** High volume + price drop triggers no signal (Volume Profile), but triggers sell signal (Volume Breakout)

**Cause:** Volume Profile needs `volume < 0.5×` for sell. Bad news creates high volume, not low volume.

**Impact:** Volume Profile misses crash-related exits. Volume Breakout correctly sells.

### 2. After-Hours Volume
**Symptom:** Backtest shows clean signals, live trading misses the move

**Cause:** Daily volume bars include pre-market and after-hours. If the spike happened at 4:01 PM, you couldn't trade at 4:01 PM with daily data.

**Mitigation:** Use intraday timeframes for volume strategies, or filter to regular-hours-only volume (not implemented).

### 3. Volume Seasonality
**Symptom:** Strategy works great January-November, fails in December

**Cause:** December volume is typically 30-40% lower (holidays). The rolling average drops, making normal January volume look like a "spike."

**Mitigation:** Use 252-day (1 year) volume average instead of 20-day. Or deseasonalize.

### 4. Crypto Volume Manipulation
**Symptom:** Massive volume spikes with no price movement

**Cause:** Wash trading (common on unregulated exchanges). Volume is artificial.

**Impact:** Volume strategies generate false signals. Consider using only regulated exchange volume.

---

## Key Insights

### Volume Precedes Price (But Not Always)
The classic axiom is true ~60% of the time. The other 40% is noise, wash trading, or index rebalancing. Volume is a filter, not a primary signal.

### The Asymmetry Problem
Both volume strategies have asymmetric buy/sell logic:
- Volume Profile: Strong buy (spike), weak sell (dry-up)
- Volume Breakout: Buy on breakout + volume, sell on any drop + volume

This means exit timing is the weakest link. Consider combining with [[EMA Crossover]] for exits (momentum-based exit instead of volume-based exit).

### Volume + Price > Volume Alone
Neither strategy uses volume in isolation. Volume confirms price action. A volume spike without a price move is inconclusive. A price move without volume is suspicious. Both together = conviction.

---

## Related Strategies
- [[Breakout]] — Same thesis without volume confirmation
- [[EMA Crossover]] — Can provide exit signals for volume strategies
- [[MA Ribbon]] — MA alignment as trend context for volume signals

## Related Concepts
- [[Regime Detection]] — Volume expansion indicates regime transition
- [[Data Pipeline]] — Volume data quality varies by provider and market
- [[Risk Metrics]] — Trade frequency affects Sharpe calculation

## Implementation References
- `src/strategies/momentum/volume_strategies.py` — Both strategies
- `src/ml/feature_engineering/features.py:102-117` — Volume features (OBV, VWAP)
- `src/ml/feature_engineering/features.py:210-221` — MFI calculation
