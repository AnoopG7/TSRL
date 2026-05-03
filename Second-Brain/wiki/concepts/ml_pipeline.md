# ML Pipeline for Trading

## Definition
A machine learning system that predicts price direction or returns using historical features (technical indicators, lag features, volume patterns) trained on labeled data.

**Core thesis:** Markets have subtle, non-linear patterns that ML can detect but rule-based strategies cannot capture.

## Why It Matters
- **Pattern recognition:** ML finds complex feature interactions humans miss
- **Adaptive:** Models can retrain as regimes change
- **Ensemble power:** Combine hundreds of weak signals into strong predictor
- **Alpha source:** Different from traditional technical analysis

## In My System

**Location:** 
- `src/ml/feature_engineering/features.py` — 116 features
- `src/ml/strategies/ml_strategies.py` — MLRandomForestStrategy, MLGradientBoostingStrategy

**Feature count:** 116 features across 6 categories

---

## Feature Categories

### 1. Lag Features (6 features)
```python
# Previous returns at different lags
df["lag_1"] = df["close"].shift(1).pct_change()
df["lag_2"] = df["close"].shift(2).pct_change()
df["lag_5"] = df["close"].shift(5).pct_change()
df["lag_10"] = df["close"].shift(10).pct_change()
df["lag_20"] = df["close"].shift(20).pct_change()
df["lag_60"] = df["close"].shift(60).pct_change()
```

**Rationale:** Auto-correlation in returns (momentum/reversal patterns)

---

### 2. Rolling Statistics (40 features)
```python
# Rolling mean (trend)
df["sma_5"] = df["close"].rolling(5).mean()
df["sma_10"] = df["close"].rolling(10).mean()
df["sma_20"] = df["close"].rolling(20).mean()

# Rolling std (volatility)
df["std_10"] = df["returns"].rolling(10).std()
df["std_20"] = df["returns"].rolling(20).std()

# Rolling min/max (range)
df["min_20"] = df["low"].rolling(20).min()
df["max_20"] = df["high"].rolling(20).max()

# Rolling skew/kurtosis (distribution shape)
df["skew_20"] = df["returns"].rolling(20).skew()
df["kurt_20"] = df["returns"].rolling(20).kurt()
```

**Windows:** 5, 10, 20, 60 days

**Rationale:** Capture local trend, volatility, and distribution changes

---

### 3. Technical Indicators (40 features)
```python
# RSI
df["rsi_14"] = 100 - (100 / (1 + rs_delta))

# MACD
df["macd"] = ema_fast - ema_slow
df["macd_signal"] = df["macd"].ewm(9).mean()
df["macd_hist"] = df["macd"] - df["macd_signal"]

# Bollinger Bands
df["bb_upper"] = sma + (2 * std)
df["bb_lower"] = sma - (2 * std)
df["bb_pct"] = (close - bb_lower) / (bb_upper - bb_lower)

# ATR (volatility)
df["atr_14"] = tr.rolling(14).mean()

# ADX (trend strength)
df["adx_14"] = ...
```

**Rationale:** Encoded trading knowledge as features

---

### 4. Volume Features (12 features)
```python
# Volume trend
df["volume_sma_10"] = df["volume"].rolling(10).mean()
df["volume_ratio"] = df["volume"] / df["volume_sma_10"]

# Volume-price interaction
df["volume_price_trend"] = (df["close"].pct_change() * df["volume"]).cumsum()
df["on_balance_volume"] = ...

# Volume volatility
df["volume_std"] = df["volume"].rolling(20).std()
```

**Rationale:** Volume confirms price moves (or signals reversals)

---

### 5. Price Pattern Features (12 features)
```python
# Candlestick patterns
df["doji"] = (abs(df["close"] - df["open"]) / (df["high"] - df["low"])) < 0.1
df["hammer"] = (df["close"] - df["low"]) > 2 * abs(df["open"] - df["close"])

# Price structure
df["higher_high"] = df["high"] > df["high"].shift(20)
df["lower_low"] = df["low"] < df["low"].shift(20)

# Gap detection
df["gap_up"] = df["open"] > df["high"].shift(1)
df["gap_down"] = df["open"] < df["low"].shift(1)
```

**Rationale:** Patterns that traders watch

---

### 6. Momentum/Acceleration Features (6 features)
```python
# Rate of change
df["roc_10"] = df["close"].pct_change(10)
df["roc_20"] = df["close"].pct_change(20)

# Acceleration
df["momentum"] = df["close"] - df["close"].shift(10)
df["acceleration"] = df["momentum"].diff()
```

**Rationale:** Speed and direction of price moves

---

## Label Engineering

### Binary Classification (Default)
```python
# 1 if price goes up in next N days, 0 otherwise
def create_labels(data: pd.DataFrame, horizon: int = 5) -> pd.Series:
    future_return = data["close"].shift(-horizon) / data["close"] - 1
    return (future_return > 0).astype(int)
```

**Horizon options:**
- 1-day: Scalping (high noise)
- 5-day: Swing trading (balanced)
- 20-day: Position trading (low noise)

---

### Triple Barrier Method (Advanced)
```python
# Label based on which barrier hits first:
# 1 = upper (profit), -1 = lower (loss), 0 = time expiry

def triple_barrier(data, profit_target, stop_loss, horizon):
    labels = []
    for i in range(len(data)):
        entry_price = data["close"].iloc[i]
        subset = data.iloc[i:i+horizon]
        
        max_price = subset["high"].max()
        min_price = subset["low"].min()
        
        if max_price >= entry_price * (1 + profit_target):
            labels.append(1)  # Profit target hit
        elif min_price <= entry_price * (1 - stop_loss):
            labels.append(-1)  # Stop loss hit
        else:
            labels.append(0)  # Time expiry
    
    return labels
```

**Why better:** Accounts for path, not just endpoint

---

## Models Used

### Random Forest Classifier
```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    min_samples_split=50,
    min_samples_leaf=20,
    class_weight="balanced",
)
```

**Pros:**
- Handles non-linear relationships
- Feature importance (interpretability)
- Robust to outliers
- No feature scaling needed

**Cons:**
- Can overfit without regularization
- Slower than linear models

**In my system:** `src/ml/strategies/ml_strategies.py::MLRandomForestStrategy`

---

### Gradient Boosting Classifier
```python
from sklearn.ensemble import GradientBoostingClassifier

model = GradientBoostingClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=3,
    min_samples_split=50,
)
```

**Pros:**
- Often better accuracy than RF
- Handles complex interactions

**Cons:**
- More hyperparameters to tune
- Slower training
- More prone to overfitting

**In my system:** `src/ml/strategies/ml_strategies.py::MLGradientBoostingStrategy`

---

## Training Process

### 1. Feature-Label Alignment
```python
# Features at time t predict label at time t (which is return from t to t+horizon)
X = features.iloc[:-horizon]  # Remove last 'horizon' rows (no labels)
y = labels.iloc[:-horizon]    # Remove rows without labels
```

**Critical:** Ensure no look-ahead bias in feature calculation

---

### 2. Train/Test Split (Purged)
```python
# Standard split (WRONG for time series)
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]

# Purged split (CORRECT)
train_size = int(len(X) * 0.8)
gap = horizon  # Prevent leakage
X_train, X_test = X[:train_size], X[train_size + gap:]
y_train, y_test = y[:train_size], y[train_size + gap:]
```

**Why gap?** Labels overlap with features near split point

---

### 3. Cross-Validation (Time Series)
```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)

for train_idx, test_idx in tscv.split(X):
    model.fit(X.iloc[train_idx], y.iloc[train_idx])
    score = model.score(X.iloc[test_idx], y.iloc[test_idx])
```

**Key:** Training data always before test data (no shuffling)

---

### 4. Feature Importance
```python
importances = model.feature_importances_
feature_names = features.columns

# Top 10 features
top_10 = pd.DataFrame({
    "feature": feature_names,
    "importance": importances
}).sort_values("importance", ascending=False).head(10)
```

**Use case:** Identify which features drive predictions

---

## Signal Generation

### Prediction to Position
```python
# Get prediction probabilities
prob_up = model.predict_proba(X_latest)[0, 1]  # P(up)

# Convert to position
if prob_up > 0.6:
    position = 1  # Long
elif prob_up < 0.4:
    position = -1  # Short
else:
    position = 0  # Flat
```

**Threshold tuning:**
- Higher threshold (0.7): Fewer trades, higher confidence
- Lower threshold (0.55): More trades, lower edge per trade

---

### Probability-Weighted Sizing
```python
# Position size proportional to confidence
base_size = capital * 0.02  # 2% base risk
confidence = abs(prob_up - 0.5) * 2  # 0 to 1 scale
position_size = base_size * (0.5 + confidence)  # 50% to 150% of base
```

**Rationale:** Bet more when model is confident

---

## Failure Cases & Edge Cases

### 1. Look-Ahead Bias in Features
**Symptom:** 90%+ accuracy in backtest, 50% live

**Cause:** Features use future data

**Example (bug):**
```python
# WRONG: Using close price that includes future information
df["return_today"] = df["close"].pct_change()
df["label"] = (df["close"].shift(-1) > df["close"]).astype(int)

# Model learns: "If return_today > 0, label = 1" (leakage!)
```

**Fix:**
```python
# CORRECT: Features at time t use only data up to time t
df["return_yesterday"] = df["close"].shift(1).pct_change()
df["label"] = (df["close"].shift(-1) > df["close"]).astype(int)
```

---

### 2. Label Leakage
**Symptom:** Model predicts perfectly on test set

**Cause:** Label information leaked into features

**Example:**
```python
# WRONG: Future return in features
df["future_return"] = df["close"].shift(-5) / df["close"] - 1
df["label"] = (df["future_return"] > 0).astype(int)

# Model learns: "If future_return > 0, label = 1" (perfect!)
```

**Detection:**
- Check feature importances for suspicious features
- Remove any feature with "shift(-" in calculation

---

### 3. Regime Change
**Symptom:** Model works for 6 months, then fails

**Cause:** Market regime changed (bull → bear, low vol → high vol)

**Example:**
```
2020-2021: Bull market, low vol → Model learns "buy dips"
2022: Bear market, high vol → "Buy dips" = catch falling knives
```

**Mitigation:**
- Retrain quarterly (or monthly)
- Add regime features (VIX, ADX, volatility)
- Use ensemble of models trained on different regimes

---

### 4. Feature Decay
**Symptom:** Feature importance drops over time

**Cause:** Other traders arbitrage away the signal

**Example:**
```
Year 1: RSI divergence predicts reversals (Sharpe 1.5)
Year 2: Everyone knows RSI divergence → edge disappears
```

**Mitigation:**
- Monitor feature importance drift
- Continuously research new features
- Use feature selection to drop decayed features

---

### 5. Overfitting to Noise
**Symptom:** 116 features, 50% test accuracy

**Cause:** Too many features relative to samples

**Rule of thumb:**
- Minimum 100 samples per feature
- With 116 features, need 11,600+ samples (~46 years of daily data)

**Mitigation:**
- Feature selection (keep top 20-30 features)
- Regularization (max_depth, min_samples_leaf)
- Simpler models (logistic regression before RF)

---

## Performance Characteristics

### Typical Metrics (US stocks, 2015-2023)
| Metric | Random Forest | Gradient Boosting |
|--------|---------------|-------------------|
| Accuracy | 52-58% | 54-60% |
| Precision (long) | 55-60% | 57-62% |
| Recall | 50-60% | 48-58% |
| Sharpe Ratio | 0.5-1.0 | 0.6-1.2 |
| Max Drawdown | 15-25% | 12-20% |
| Turnover | High (daily signals) | High |

**Comparison to rule-based strategies:**
- Lower win rate than mean reversion
- Higher turnover than trend following
- More adaptive to regime changes

---

## Key Insights

### The Feature Importance Reality
> "Top features are often lag returns and volatility — not exotic indicators."

**Typical top 5:**
1. Lag_1 return (1-day momentum)
2. Volatility (std_20)
3. RSI_14
4. MACD histogram
5. Volume ratio

**Implication:** Simple features work; complexity doesn't add much

---

### The Accuracy Ceiling
> "55-60% accuracy is excellent for daily prediction. Higher usually means overfitting."

**Why:** Markets are near-efficient; 60% predictability is genuine edge

**Red flag:** 70%+ accuracy → check for leakage

---

### The Retraining Cadence
```
Daily: Update features, get predictions
Weekly: Update model weights (optional)
Monthly: Full retrain with new data
Quarterly: Feature selection review
```

**Minimum:** Retrain monthly

**Optimal:** Walk-forward retraining (continuous)

---

### The Sample Efficiency Problem
```
Daily data: ~252 samples/year
With 116 features: Need 46 years for 100:1 ratio

Solution:
- Use more data (intraday, multiple symbols)
- Reduce features (feature selection)
- Use regularization
```

---

## Usage Examples

### CLI
```bash
# Train and backtest ML strategy
PYTHONPATH=. python -m src.cli backtest \
  --strategy ml_random_forest \
  --symbol AAPL \
  --start-date 2020-01-01 \
  --strategy-params '{"n_estimators": 100, "max_depth": 5}'
```

### Python
```python
from src.ml.strategies.ml_strategies import MLRandomForestStrategy
from src.engine.backtest.engine import BacktestEngine

# Create and train strategy
strategy = MLRandomForestStrategy(n_estimators=100, max_depth=5)
strategy.fit(ohlcv_data)  # Train model

# Run backtest
engine = BacktestEngine()
result = engine.run(strategy, ohlcv_data)
```

---

## Related Concepts
- [[Backtesting]] — How ML strategies are tested
- [[Strategy Design]] — ML as strategy type
- [[Feature Engineering]] — Creating predictive features
- [[Walk-Forward Analysis]] — Out-of-sample validation for ML

## Implementation References
- `src/ml/feature_engineering/features.py` — 116 features
- `src/ml/strategies/ml_strategies.py` — ML strategies
- `src/strategies/base.py` — Base class interface
