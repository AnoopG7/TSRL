# Regime Detection

## Definition
Identifying whether the market is trending, ranging, volatile, or transitioning — and adapting strategy selection accordingly. A strategy that dominates in trending markets may bleed in sideways markets.

## Why It Matters
- **Strategy selection**: EMA Crossover profits in trends, dies in chop. RSI Mean Reversion does the opposite. Knowing the regime tells you which to deploy.
- **Risk adjustment**: Volatile regimes need smaller position sizes
- **False signal filtering**: A "buy" signal in a bear market has very different meaning than in a bull market

## In My System

### ML-Based Regime Labels (`src/ml/feature_engineering/features.py:282-297`)

```python
class LabelGenerator:
    @staticmethod
    def generate_regime_labels(returns: pd.Series, window: int = 20) -> pd.Series:
        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()
        z_score = (returns - rolling_mean) / rolling_std
        
        labels = pd.Series(index=returns.index, dtype=float)
        labels[z_score > 1] = 1      # Abnormally high returns (bullish)
        labels[z_score < -1] = -1    # Abnormally low returns (bearish)
        labels[(z_score >= -1) & (z_score <= 1)] = 0  # Normal (ranging)
```

**What this does:** Classifies each bar as bull/bear/neutral based on whether returns are >1σ from the rolling mean.

**Limitation:** This is a label generator for ML training, not a live regime detector. It uses current-bar data (no look-ahead), but the 20-bar window means regime detection lags by ~1 month.

---

### Feature-Based Regime Indicators

The `FeatureEngineer` computes several regime-indicative features:

| Feature | What It Measures | Regime Signal |
|---------|-----------------|---------------|
| `volatility_{window}` | Rolling return std | High = volatile regime |
| `z_score_{window}` | Price deviation from mean | |z| > 2 = extreme regime |
| `rsi_14` | Momentum oscillator | < 30 = oversold, > 70 = overbought |
| `bb_width_{window}` | Bollinger Band width | Narrow = squeeze, wide = expansion |
| `atr_{period}` | Average True Range | Absolute volatility level |

**No composite regime classifier exists.** The features are available but there's no function that says "the market is currently in a trending regime." This is the primary gap.

---

## Regime Framework (Theory)

### Four Regimes

| Regime | Characteristics | Best Strategy Type | Worst Strategy Type |
|--------|----------------|-------------------|-------------------|
| **Trending Up** | ADX > 25, price > MA200, RSI 50-70 | Momentum (EMA, MACD) | Mean Reversion |
| **Trending Down** | ADX > 25, price < MA200, RSI 30-50 | Short Momentum | Long-only Mean Reversion |
| **Ranging** | ADX < 20, price between support/resistance | Mean Reversion (RSI, BB) | Momentum (whipsaws) |
| **Volatile Transition** | VIX spike, ATR expansion, BB squeeze → expansion | Breakout | Everything else (until direction established) |

### Detection Methods

#### 1. ADX (Average Directional Index)
```
ADX > 25 → trending
ADX < 20 → ranging
```
**Not implemented in TSRL.** Would need to add to `FeatureEngineer`.

#### 2. Volatility Percentile
```python
current_vol = returns.rolling(20).std().iloc[-1]
vol_percentile = (historical_vol < current_vol).mean()
# > 80th percentile = volatile regime
```
**Available:** `volatility_{window}` features exist but no percentile ranking.

#### 3. Moving Average Alignment
```python
# From MA Ribbon strategy
bullish = (ma_fast > ma_medium) & (ma_medium > ma_slow)
bearish = (ma_fast < ma_medium) & (ma_medium < ma_slow)
# Neither = ranging
```
**Available:** `MovingAverageRibbonStrategy` already computes this for signals. Could extract for regime detection.

---

## The Strategy Selection Matrix

| Detected Regime | Deploy | Stand Down | Position Size |
|-----------------|--------|------------|---------------|
| Strong Trend Up | EMA Crossover, MA Ribbon, MACD | RSI Mean Reversion | Full (100%) |
| Strong Trend Down | Short EMA, Short MACD | Long-only strategies | Full (100%) |
| Ranging/Choppy | RSI Mean Reversion, Bollinger Bands | All momentum | Reduced (50%) |
| Volatile Transition | Breakout, Volume Breakout | All strategies (wait for clarity) | Reduced (25%) |

**Current gap:** No automatic strategy rotation. The user must manually select strategies. Building an auto-selector that uses regime detection → strategy routing is a high-impact feature.

---

## Failure Cases & Edge Cases

### 1. Regime Lag
**Symptom:** Regime detected after it's over

**Cause:** 20-bar rolling window means ~1 month lag for daily data

**Impact:** By the time you detect a trend, 60-80% of the move is over

**Mitigation:** Use shorter windows (5-10 bars) for faster detection, at the cost of more noise

### 2. Regime Flip-Flop
**Symptom:** Regime changes every few days

**Cause:** Market at boundary between trending and ranging

**Impact:** Strategy switching costs (each switch = new warmup period)

**Mitigation:** Add hysteresis: require 5+ consecutive days in new regime before switching

### 3. Black Swan Blindness
**Symptom:** Regime detector says "normal" right before a crash

**Cause:** Z-score uses historical volatility. COVID crash was 6σ — way outside the training distribution

**Impact:** No regime model can predict true black swans. Use portfolio-level circuit breakers instead.

---

## Key Insights

### Regime Detection Is The Meta-Strategy
Individual strategies have edges in specific regimes. A regime detector that routes to the right strategy IS the alpha — it's the strategy that selects strategies.

### The 80/20 of Regime Detection
Simple ADX + volatility percentile captures 80% of regime information. Complex ML models (Hidden Markov Models, regime-switching GARCH) add accuracy but also overfitting risk and implementation complexity.

### Current State: Manual → Automated Path
1. **Now:** User selects strategy manually (fully implemented)
2. **Next:** Add regime features + dashboard indicator (shows current regime)
3. **Later:** Auto-routing: detect regime → select best strategy → execute

---

## Related Concepts
- [[Strategy Design]] — Principle 4: Strategy type determines behavior
- [[EMA Crossover]] — Works in trending, fails in ranging
- [[Optimization]] — Can optimize per-regime
- [[ML Pipeline]] — Uses `generate_regime_labels()` for training

## Implementation References
- `src/ml/feature_engineering/features.py:282-297` — Regime label generator
- `src/ml/feature_engineering/features.py:78-100` — Volatility features
- `src/strategies/momentum/ma_ribbon.py:84-98` — MA alignment (regime proxy)
