# Portfolio Metrics

## Definition
Metrics that measure the collective behavior of multiple assets held together. Unlike single-asset metrics, portfolio metrics capture **correlation effects**, **diversification benefits**, and **allocation efficiency**.

## Why It Matters
- **Correlation kills or saves**: Two 50% win rate strategies can combine into a 70% win rate portfolio (if uncorrelated) or a 30% disaster (if highly correlated)
- **Position sizing across assets**: A 20% position in AAPL isn't the same risk as 20% in a biotech stock
- **Rebalancing alpha**: Systematic rebalancing can add 1-3% annually without changing strategy

## In My System

Portfolio metrics calculated by `src/analytics/portfolio_metrics.py::PortfolioMetricsCalculator` and used by `src/engine/backtest/portfolio_engine.py`.

---

## Core Metrics

### Correlation Matrix
```python
corr_matrix = returns_df.corr()
```

**What it tells you:** Pairwise linear relationships between assets

**Interpretation:**
| Correlation | Meaning |
|-------------|---------|
| > 0.7 | High positive (move together) |
| 0.3-0.7 | Moderate positive |
| -0.3 to 0.3 | Low/uncorrelated (diversification benefit) |
| < -0.3 | Negative (hedge) |

**My implementation** (`portfolio_metrics.py:40-45`):
```python
corr_matrix = returns_df.corr()
metrics.correlation_matrix = {
    col: {row: round(corr_matrix.loc[row, col], 4) for row in corr_matrix.index}
    for col in corr_matrix.columns
}
```

**Output structure:**
```json
{
  "AAPL": {"AAPL": 1.0, "MSFT": 0.72, "GOOGL": 0.68},
  "MSFT": {"AAPL": 0.72, "MSFT": 1.0, "GOOGL": 0.65},
  ...
}
```

---

### Average Correlation
```python
# Mean of off-diagonal elements (excluding self-correlation = 1)
mask = ~np.eye(n, dtype=bool)  # Create False diagonal
off_diag = corr_matrix.values[mask]
avg_correlation = float(np.nanmean(off_diag))
```

**What it tells you:** Overall portfolio diversification

**Interpretation:**
| Avg Correlation | Diversification |
|-----------------|-----------------|
| > 0.7 | Poor (all assets move together) |
| 0.3-0.7 | Moderate |
| < 0.3 | Excellent (true diversification) |

**My implementation** (`portfolio_metrics.py:47-52`):
```python
n = len(corr_matrix)
if n > 1:
    mask = ~np.eye(n, dtype=bool)
    off_diag = corr_matrix.values[mask]
    metrics.avg_correlation = float(np.nanmean(off_diag))
```

---

### Portfolio Return (Weighted)
```python
portfolio_returns = sum(returns_df[s] * weights[s] for s in valid_symbols)
```

**What it tells you:** Combined return of all positions

**Example:**
- AAPL: +10% with 60% weight
- MSFT: -5% with 40% weight
- Portfolio: 0.6×10% + 0.4×(-5%) = +4%

---

### Portfolio Volatility
```python
# Full covariance formula
portfolio_var = w' × Σ × w
portfolio_vol = √portfolio_var
```

Where:
- `w` = weight vector
- `Σ` = covariance matrix

**My implementation** (`portfolio_metrics.py:135-147`):
```python
cov_matrix = returns_df.cov() * 252  # Annualize
w = np.array([weights.get(s, 0) for s in valid_symbols])

cov_filtered = cov_matrix.loc[valid_symbols, valid_symbols]
portfolio_var = float(np.dot(w, np.dot(cov_filtered.values, w)))
portfolio_vol = np.sqrt(portfolio_var) if portfolio_var > 0 else 0
```

**Key insight:** Portfolio volatility ≠ weighted average of individual volatilities (unless correlation = 1)

---

### Beta
```python
beta = cov(portfolio, benchmark) / var(benchmark)
```

**What it tells you:** Sensitivity to market movements

**Interpretation:**
| Beta | Meaning |
|------|---------|
| > 1 | More volatile than market |
| = 1 | Moves with market |
| 0-1 | Less volatile than market |
| < 0 | Inverse relationship (hedge) |

**My implementation** (`portfolio_metrics.py:64-75`):
```python
aligned = pd.DataFrame({
    "portfolio": portfolio_returns,
    "benchmark": benchmark_returns,
}).dropna()

if len(aligned) > 20:  # Minimum data requirement
    cov = aligned["portfolio"].cov(aligned["benchmark"])
    var_bench = aligned["benchmark"].var()
    
    if var_bench > 0:
        metrics.beta = float(cov / var_bench)
```

**Edge case:** Requires 20+ data points for statistical significance

---

### Alpha (Jensen's Alpha)
```python
alpha = portfolio_return - rf - beta × (benchmark_return - rf)
```

**What it tells you:** Excess return unexplained by market exposure

**Interpretation:**
- Alpha > 0: Skill (or luck)
- Alpha = 0: Market return (beta replication)
- Alpha < 0: Underperformance (fees, poor timing)

**My implementation** (`portfolio_metrics.py:77-82`):
```python
portfolio_annual = aligned["portfolio"].mean() * 252
benchmark_annual = aligned["benchmark"].mean() * 252
metrics.alpha = float(
    portfolio_annual - risk_free_rate - metrics.beta * (benchmark_annual - risk_free_rate)
)
```

---

### Tracking Error
```python
tracking_error = std(portfolio_returns - benchmark_returns) × √252
```

**What it tells you:** How actively the portfolio differs from benchmark

**Use case:** Information ratio denominator

---

### Information Ratio
```python
information_ratio = active_return / tracking_error
```

Where `active_return = portfolio_return - benchmark_return`

**Interpretation:**
| IR | Quality |
|----|---------|
| < 0.5 | Poor active management |
| 0.5-1.0 | Acceptable |
| > 1.0 | Good stock picking |

---

### Diversification Ratio
```python
diversification_ratio = weighted_avg_volatility / portfolio_volatility
```

**What it tells you:** How much risk reduction comes from diversification

**Interpretation:**
- DR = 1: No diversification benefit (correlation = 1)
- DR > 1: Diversification reduces risk
- DR = 2: Portfolio volatility is half of weighted average (excellent diversification)

**My implementation** (`portfolio_metrics.py:111-147`):
```python
# Individual volatilities (annualized)
vols = returns_df.std() * np.sqrt(252)

# Weighted average volatility
weighted_vol = sum(weights.get(s, 0) * vols.get(s, 0) for s in returns_df.columns)

# Portfolio volatility (from covariance)
portfolio_vol = np.sqrt(portfolio_var)

if portfolio_vol > 0:
    return float(weighted_vol / portfolio_vol)
```

---

### Concentration (HHI - Herfindahl-Hirschman Index)
```python
concentration_hhi = sum(weight ** 2 for weight in weights.values())
```

**What it tells you:** Portfolio concentration

**Interpretation:**
| HHI | Concentration |
|-----|---------------|
| 1.0 | Single asset (max concentration) |
| 0.5-1.0 | High concentration |
| 0.2-0.5 | Moderate |
| < 0.2 | Well diversified |

**Example:**
- Equal weight 5-asset portfolio: HHI = 5 × (0.2)² = 0.2
- Equal weight 10-asset portfolio: HHI = 10 × (0.1)² = 0.1

---

### Risk Contribution
```python
# Marginal Contribution to Risk (MCTR)
mctr = (Σ × w) / portfolio_vol

# Risk contribution = weight × MCTR / portfolio_vol
risk_contribution[symbol] = w[i] * mctr[i] / portfolio_vol
```

**What it tells you:** How much each asset contributes to total portfolio risk

**Key insight:** A 5% weight in a volatile asset can contribute more risk than a 20% weight in a stable asset

**My implementation** (`portfolio_metrics.py:162-198`):
```python
# Marginal contribution to risk
mctr = np.dot(cov_filtered.values, w) / portfolio_vol

# Component contribution
for i, symbol in enumerate(valid_symbols):
    contributions[symbol] = float(w[i] * mctr[i] / portfolio_vol)
```

**Use case:** Risk parity allocation (equal risk contribution)

---

## Portfolio Engine Implementation

### Enhanced Portfolio Backtest Engine
`src/engine/backtest/portfolio_engine.py::EnhancedPortfolioBacktestEngine`

**Key features:**
1. **Weighted allocation**: `allocated_capital = initial_capital * weight`
2. **Rebalancing**: Periodic or threshold-based
3. **Benchmark comparison**: Beta/alpha calculation

### Rebalancing Logic

**Two triggers** (`portfolio_engine.py:486-496`):

```python
# 1. Periodic rebalancing
if date in rebalance_dates:
    should_rebalance = True
    reason = "periodic"

# 2. Threshold rebalancing (drift detection)
if cfg.rebalance_threshold:
    max_drift = max(abs(current_weights[s] - target_weights[s]))
    if max_drift > cfg.rebalance_threshold:
        should_rebalance = True
        reason = f"threshold ({max_drift:.2%} drift)"
```

**Rebalance cost calculation:**
```python
value_traded = sum(abs(new_values[s] - current_values[s]) for s in holdings)
rebalance_cost = value_traded * cfg.commission
```

**Typical drift threshold:** 5% (0.05)

---

## Failure Cases & Edge Cases

### 1. No Common Dates
**Symptom:** "No overlapping date range found across symbols"

**Cause:** Symbols have non-overlapping trading calendars (e.g., US + India stocks)

**Handled in code** (`portfolio_engine.py:378-408`):
```python
# Fallback: use date range intersection
min_dates = [data.index.min() for data in symbols_data.values()]
max_dates = [data.index.max() for data in symbols_data.values()]
start_date = max(min_dates)
end_date = min(max_dates)

if start_date >= end_date:
    raise ValueError("No overlapping date range found")
```

**Mitigation:** Ensure all symbols have overlapping trading periods

---

### 2. Weights Don't Sum to 1
**Symptom:** ValueError on PortfolioConfig initialization

**Handled in code** (`portfolio_engine.py:67-72`):
```python
def __post_init__(self):
    if self.weights is not None:
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):  # 1% float tolerance
            raise ValueError(f"Weights must sum to 1.0, got {total}")
```

---

### 3. Insufficient Data for Beta/Alpha
**Symptom:** Beta/alpha return None or 0

**Handled in code** (`portfolio_metrics.py:70`):
```python
if len(aligned) > 20:  # Minimum for statistical significance
    # Calculate beta/alpha
```

**Rule:** Minimum 20 data points, preferably 60+

---

### 4. Singular Covariance Matrix
**Symptom:** Matrix inversion fails in optimization

**Cause:** Perfect correlation between assets (rare but possible)

**Mitigation:** Remove one of the perfectly correlated assets

---

## Key Insights

### Correlation During Crises
> "Diversification works until it doesn't. In March 2020, all correlations went to 1."

**Implication:** Backtests may overstate diversification benefits if they don't include crisis periods

---

### Rebalancing Bonus
Systematic rebalancing adds value through:
1. **Mean reversion capture**: Buy low, sell high automatically
2. **Volatility pumping**: Forced trading in volatile markets

**Typical bonus:** 1-3% annually for 60/40 portfolios

**Cost consideration:** Rebalancing too frequently burns commission

---

### Risk Parity vs Equal Weight
| Approach | Allocation | Risk Profile |
|----------|------------|--------------|
| Equal Weight | 20% each | Volatile assets dominate risk |
| Risk Parity | Equal risk contribution | Stable assets get higher weight |

**Example:**
- Equal weight: 20% stocks, 20% bonds → 90% of risk from stocks
- Risk parity: 50% bonds, 50% stocks → Equal risk from each

---

### The Beta Trap
A low-beta portfolio isn't necessarily low-risk:
- Could be high idiosyncratic risk
- Could have fat tails (low beta, high crash risk)

**Always check:** Max drawdown alongside beta

---

## Related Concepts
- [[Backtesting]] — Portfolio engine overview
- [[Risk Metrics]] — Single-asset risk measurements
- [[Walk-Forward Analysis]] — Out-of-sample portfolio validation
- [[Fundamental Analysis]] — Fundamental-based portfolio construction

## Implementation References
- `src/analytics/portfolio_metrics.py` — Calculator class
- `src/domain/entities/portfolio_metrics.py` — PortfolioMetrics entity
- `src/engine/backtest/portfolio_engine.py` — Enhanced portfolio engine
- `src/application/services/backtest_service.py:327-405` — Portfolio backtest orchestration
