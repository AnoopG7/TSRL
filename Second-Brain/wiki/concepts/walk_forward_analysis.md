# Walk-Forward Analysis

## Definition
A validation technique that tests strategies on out-of-sample data by repeatedly training on a historical window and testing on the subsequent period.

**Core thesis:** If a strategy only works on specific data, it's overfitted. If it works across multiple train/test splits, it has genuine edge.

## Why It Matters
- **Overfitting detection:** Distinguishes real edge from curve-fitting
- **Parameter stability:** Shows if parameters work across time periods
- **Regime testing:** Validates strategy in different market conditions
- **Production gate:** Should pass before deploying real capital

## In My System

**Location:** `src/engine/walkforward/walkforward.py::WalkForwardAnalysis`

**Usage:**
```python
from src.engine.walkforward.walkforward import WalkForwardAnalysis

wfa = WalkForwardAnalysis(
    train_window=252,    # 1 year of trading days
    test_window=63,      # 1 quarter
    step_size=63,        # Roll forward by 1 quarter
)

results = wfa.run(strategy, data)
```

---

## How It Works

### Standard Walk-Forward Process

```
Period 1: [Train: 2020] → [Test: Q1 2021]
Period 2: [Train: 2020 + Q1 2021] → [Test: Q2 2021]
Period 3: [Train: 2020 + Q1-Q2 2021] → [Test: Q3 2021]
...
```

**Two approaches:**

### 1. Rolling Window (Fixed Training Size)
```python
train_window = 252  # Always 1 year
test_window = 63    # Always 1 quarter

# Window rolls forward
Period 1: [Day 0:252] → [Day 253:315]
Period 2: [Day 63:315] → [Day 316:378]
Period 3: [Day 126:378] → [Day 379:441]
```

**Use case:** Recent data more relevant than old data

---

### 2. Expanding Window (Growing Training Size)
```python
train_window = 252  # Start with 1 year
test_window = 63

# Training set expands, test set rolls
Period 1: [Day 0:252] → [Day 253:315]
Period 2: [Day 0:315] → [Day 316:378]
Period 3: [Day 0:378] → [Day 379:441]
```

**Use case:** More data improves parameter estimates

**In my system:** Expanding window (default)

---

## Implementation Details

### Configuration
```python
@dataclass
class WalkForwardConfig:
    train_window: int = 252       # Training days (1 year)
    test_window: int = 63         # Testing days (1 quarter)
    step_size: int = 63           # Roll amount
    strategy_params: dict = None  # Optional fixed params
```

**Common settings:**

| Setting | Train | Test | Use Case |
|---------|-------|------|----------|
| Quarterly | 252 | 63 | Short-term strategies |
| Semi-annual | 252 | 126 | Medium-term strategies |
| Annual | 504 | 252 | Long-term strategies |

---

### Execution Flow

```python
def run(self, strategy: BaseStrategy, data: pd.DataFrame) -> WalkForwardResult:
    results = []
    
    # Split data into train/test windows
    for train_start, train_end, test_start, test_end in self._windows(data):
        # 1. Get training data
        train_data = data.iloc[train_start:train_end]
        test_data = data.iloc[test_start:test_end]
        
        # 2. Optimize parameters on training data
        best_params = self._optimize(strategy, train_data)
        
        # 3. Run backtest with best params on test data
        result = self._backtest(strategy, test_data, best_params)
        
        # 4. Store result
        results.append({
            "period": f"{test_start}:{test_end}",
            "params": best_params,
            "sharpe": result.metrics.sharpe_ratio,
            "return": result.total_return,
            "max_dd": result.metrics.max_drawdown,
        })
    
    return WalkForwardResult(windows=results)
```

**In my system:** `src/engine/walkforward/walkforward.py`

---

## Metrics To Analyze

### 1. In-Sample vs Out-Of-Sample Performance

```python
# For each window
is_sharpe = in_sample_result.metrics.sharpe_ratio
oos_sharpe = out_of_sample_result.metrics.sharpe_ratio
degradation = (oos_sharpe - is_sharpe) / is_sharpe
```

**Interpretation:**
| Degradation | Meaning |
|-------------|---------|
| 0% to -20% | Excellent (robust strategy) |
| -20% to -50% | Acceptable (some overfitting) |
| -50% to -80% | Poor (significant overfitting) |
| < -80% | Fail (strategy is curve-fit) |

---

### 2. Parameter Stability

```python
# Track best parameters across windows
window_params = []
for window in results:
    window_params.append(window["best_params"])

# If parameters vary wildly, strategy is unstable
param_variance = np.var([p["fast_period"] for p in window_params])
```

**Interpretation:**
- Low variance: Parameters stable across time (good)
- High variance: Parameters depend on specific period (bad)

---

### 3. Consistency Score

```python
# Percentage of windows with positive returns
winning_windows = sum(1 for r in results if r["return"] > 0)
consistency = winning_windows / len(results)
```

**Interpretation:**
| Consistency | Quality |
|-------------|---------|
| > 80% | Excellent |
| 60-80% | Good |
| 50-60% | Marginal |
| < 50% | Poor (random walk) |

---

## Failure Cases & Edge Cases

### 1. Insufficient Data
**Symptom:** Only 2-3 windows available

**Cause:** Not enough historical data for meaningful WFA

**Rule of thumb:**
- Minimum: 4 windows
- Preferred: 8+ windows
- Ideal: 12+ windows (3+ years with quarterly rolls)

**Mitigation:**
- Reduce test_window (shorter test periods)
- Reduce step_size (more overlapping windows)
- Use longer historical data

---

### 2. Look-Ahead In Optimization
**Symptom:** OOS performance matches IS performance (suspiciously good)

**Cause:** Optimization accidentally uses test data

**Example (bug):**
```python
# WRONG: Optimizing on full data, then splitting
best_params = optimize(strategy, data)  # Uses test data!
train_data, test_data = split(data)
```

**Correct:**
```python
# Optimize only on training data
best_params = optimize(strategy, train_data)
result = backtest(strategy, test_data, best_params)
```

---

### 3. Parameter Drift
**Symptom:** Best parameters change dramatically between windows

**Example:**
```
Window 1: fast=8, slow=20
Window 2: fast=15, slow=35
Window 3: fast=5, slow=12
```

**Interpretation:**
- Strategy has no stable edge
- Parameters are fitting noise

**Action:**
- Use fixed parameters (not optimized)
- Simplify strategy (fewer parameters)
- Consider strategy invalid

---

### 4. Single Window Drives Returns
**Symptom:** 80% of total return comes from 1 out of 8 windows

**Cause:** Strategy works in one regime only

**Example:**
```
Window 1-3: -5% return (sideways market)
Window 4: +50% return (strong trend)
Window 5-8: -3% return (sideways market)
```

**Interpretation:** Strategy is regime-dependent

**Action:**
- Add regime filter (only trade in favorable conditions)
- Combine with other strategies (regime rotation)
- Reject strategy (not robust)

---

## Key Insights

### The Overfitting Test
> "If your strategy needs different parameters for every period, it has no edge — it has memory."

**Real edge:** Works with similar parameters across different time periods

**Fake edge:** Works only with perfectly tuned parameters on specific data

---

### The WFA Reality Check
Typical degradation pattern:
```
In-sample Sharpe: 1.8
Out-of-sample Sharpe: 0.9
Degradation: 50%
```

**This is NORMAL.** Expect 30-50% degradation.

**Red flags:**
- OOS Sharpe < 0.5 (edge disappeared)
- OOS Sharpe > IS Sharpe (data leakage)

---

### The Minimum Viable Edge
For a strategy to be production-worthy:
- OOS Sharpe > 0.5
- OOS win rate > 45%
- Consistency > 60%
- Parameter variance < 20%

**If any metric fails:** Strategy needs more work

---

### Walk-Forward ≠ Cross-Validation

| Aspect | Walk-Forward | Cross-Validation |
|--------|--------------|------------------|
| Data order | Preserved (time series) | Shuffled |
| Train/test split | Sequential | Random |
| Use case | Trading strategies | ML classification |
| Leakage risk | Low (temporal integrity) | High (if shuffled) |

**Never shuffle time series data!** Tomorrow's data can't predict today.

---

## Usage Examples

### CLI (if implemented)
```bash
# Run walk-forward analysis
PYTHONPATH=. python -m src.cli walkforward \
  --strategy ema_crossover \
  --symbol AAPL \
  --train-window 252 \
  --test-window 63
```

### Python
```python
from src.engine.walkforward.walkforward import WalkForwardAnalysis
from src.strategies.registry import StrategyRegistry

strategy = StrategyRegistry.create("ema_crossover")
wfa = WalkForwardAnalysis(train_window=252, test_window=63)

results = wfa.run(strategy, ohlcv_data)

# Analyze results
print(f"Windows: {len(results.windows)}")
print(f"Avg OOS Sharpe: {np.mean([r['sharpe'] for r in results.windows]):.2f}")
print(f"Consistency: {sum(r['return'] > 0 for r in results.windows) / len(results.windows):.1%}")
```

---

## Related Concepts
- [[Backtesting]] — In-sample testing
- [[Risk Metrics]] — Performance measurement
- [[Strategy Design]] — Building robust strategies
- [[Parameter Optimization]] — Finding optimal settings

## Implementation References
- `src/engine/walkforward/walkforward.py` — Walk-forward engine
- `src/engine/optimizer/optimizer.py` — Parameter optimization
- `src/application/services/backtest_service.py` — Backtest orchestration
