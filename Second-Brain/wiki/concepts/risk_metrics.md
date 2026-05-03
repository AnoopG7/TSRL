# Risk Metrics

## Definition
Quantitative measurements of investment performance and risk exposure. They transform raw P&L data into comparable, actionable insights.

## Why It Matters
- ** apples-to-apples comparison**: Compare strategies with different risk profiles
- **Risk-adjusted decisions**: A 20% return with 5% drawdown beats 20% with 40% drawdown
- **Position sizing**: Kelly criterion tells you optimal bet size
- **Regulatory compliance**: Some metrics required for fund reporting

## In My System

All metrics calculated by `src/analytics/risk_metrics.py::RiskMetricsCalculator` and `src/domain/entities/metrics.py::RiskMetrics`.

### Return Metrics

#### Total Return
```python
total_return = (final_capital - initial_capital) / initial_capital
```
**Use case:** Simple performance measure, but ignores risk and time

#### CAGR (Compounded Annual Growth Rate)
```python
cagr = (final_capital / initial_capital) ** (1 / years) - 1
```
**Use case:** Compare strategies with different time horizons

**Edge case:** Returns 0.0 for negative or zero capital (code: `risk_metrics.py:14-23`)

---

### Risk-Adjusted Return Metrics

#### Sharpe Ratio
```python
sharpe = √252 × (returns.mean() - rf) / returns.std()
```

**What it tells you:** Excess return per unit of total risk

**Interpretation:**
| Sharpe | Quality |
|--------|---------|
| < 0.5 | Poor |
| 0.5-1.0 | Acceptable |
| 1.0-1.5 | Good |
| 1.5-2.0 | Very Good |
| > 2.0 | Excellent (or overfitted) |

**My implementation** (`risk_metrics.py:26-35`):
```python
@staticmethod
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    if len(returns) < 2 or returns.std() == 0:
        return 0.0  # Edge case: insufficient data or constant returns
    
    excess_returns = returns - risk_free_rate / periods_per_year
    return np.sqrt(periods_per_year) * excess_returns.mean() / returns.std()
```

**Failure case:** Returns 0.0 for < 2 data points — prevents division by zero

---

#### Sortino Ratio
```python
sortino = √252 × (returns.mean() - rf) / downside_std
```

**What it tells you:** Excess return per unit of BAD risk (downside deviation)

**Key difference from Sharpe:** Only penalizes downside volatility

**My implementation** (`risk_metrics.py:37-53`):
```python
downside_returns = returns[returns < 0]  # Only negative returns

if len(downside_returns) == 0 or downside_returns.std() == 0:
    return 0.0  # No downside = no penalty (but also no sortino)
```

**When Sortino > Sharpe:** Strategy has asymmetric returns (small losses, big wins)

**When Sortino ≈ Sharpe:** Symmetric return distribution (normal market behavior)

---

#### Calmar Ratio
```python
calmar = cagr / max_drawdown
```

**What it tells you:** Return per unit of worst-case loss

**Interpretation:**
- Calmar > 3: Exceptional (rare in practice)
- Calmar 1-3: Good
- Calmar < 1: Return doesn't compensate for drawdown risk

---

### Drawdown Metrics

#### Maximum Drawdown
```python
running_max = equity_curve.cummax()
drawdown = (equity_curve - running_max) / running_max
max_dd = abs(drawdown.min())
```

**What it tells you:** Worst peak-to-trough decline

**My implementation** (`risk_metrics.py:55-68`):
```python
@staticmethod
def calculate_max_drawdown(equity_curve: pd.Series) -> tuple[float, pd.Timestamp, pd.Timestamp]:
    if len(equity_curve) < 2:
        return 0.0, pd.NaT, pd.NaT  # Edge case: insufficient data
    
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max
    
    max_dd = drawdown.min()
    max_dd_idx = drawdown.idxmin()
    peak_idx = equity_curve[:max_dd_idx].idxmax()
    
    return abs(max_dd), peak_idx, max_dd_idx  # Returns (value, peak_date, trough_date)
```

**Why return peak/trough dates?** For recovery time analysis

---

#### Drawdown Duration Analysis
```python
# From DrawdownAnalyzer.get_drawdown_periods()
in_drawdown = drawdown < 0
# Track when drawdown starts/ends to measure recovery time
```

**What it tells you:** How long capital was underwater

**Psychological insight:** A 20% DD lasting 3 months feels very different from 20% DD lasting 2 years

---

### Trade Statistics

#### Win Rate
```python
win_rate = winning_trades / total_trades
```

**My implementation** (`risk_metrics.py:76-86`):
```python
@staticmethod
def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
    if not trades:
        return 0.0
    
    closed_trades = [t for t in trades if t.get("pnl") is not None]
    if not closed_trades:
        return 0.0
    
    winning = len([t for t in closed_trades if t["pnl"] > 0])
    return winning / len(closed_trades)
```

**Edge case handling:** Filters out open trades (pnl = None)

---

#### Profit Factor
```python
profit_factor = gross_profit / gross_loss
```

**Interpretation:**
| Profit Factor | Quality |
|---------------|---------|
| < 1.0 | Losing strategy |
| 1.0-1.5 | Marginal |
| 1.5-2.0 | Good |
| > 2.0 | Excellent |

**My implementation** (`risk_metrics.py:100-121`):
```python
gross_profit = sum(t["pnl"] for t in closed_trades if t["pnl"] > 0)
gross_loss = abs(sum(t["pnl"] for t in closed_trades if t["pnl"] < 0))

if gross_loss == 0:
    if gross_profit > 0:
        return 100.0  # Cap at 100 to avoid infinity propagation
    else:
        return 1.0  # No profit, no loss = neutral
```

**Why cap at 100?** Prevents infinity from breaking downstream calculations

---

#### Expectancy
```python
expectancy = total_pnl / n_trades
```

**What it tells you:** Average profit per trade

**Use case:** Compare strategies with different trade frequencies

---

### Advanced Metrics

#### Rolling Sharpe
```python
rolling_sharpe = √252 × (returns.rolling(60).mean() - rf) / returns.rolling(60).std()
```

**What it tells you:** How risk-adjusted returns change over time

**Use case:** Detect strategy decay or regime changes

**My implementation** (`risk_metrics.py:123-136`):
```python
@staticmethod
def calculate_rolling_sharpe(
    returns: pd.Series,
    window: int = 60,
    risk_free_rate: float = 0.0,
) -> pd.Series:
    if len(returns) < window:
        return pd.Series([0.0], index=returns.index)  # Edge case: insufficient data
    
    rolling_mean = returns.rolling(window=window).mean()
    rolling_std = returns.rolling(window=window).std()
    
    sharpe = np.sqrt(252) * (rolling_mean - risk_free_rate / 252) / rolling_std
    return sharpe.fillna(0)
```

---

#### Monthly Returns Heatmap
```python
monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
monthly_pivot = monthly.pivot_table(values=0, index="year", columns="month")
```

**What it tells you:** Seasonality patterns, consistency

**Use case:** Frontend visualization (`MonthlyReturnsHeatmap.tsx`)

---

#### Kelly Criterion
```python
kelly_fraction = W - (1-W) / R
```
Where:
- W = win probability
- R = win/loss ratio (average win / average loss)

**What it tells you:** Optimal position size for geometric growth

**Warning:** Full Kelly is too aggressive; use Half-Kelly or Quarter-Kelly

**Edge case:** Returns negative if expectancy is negative (don't bet!)

---

## Failure Cases & Edge Cases

### 1. Insufficient Data
**Symptom:** Metrics return 0.0 or NaN

**Handled in code:**
```python
if len(returns) < 2:
    return 0.0  # Can't compute std with < 2 points
```

**Rule:** Minimum 30 data points for meaningful statistics

### 2. Division by Zero
**Symptom:** Infinity in profit factor, Sharpe, etc.

**Handled in code:**
```python
if gross_loss == 0:
    return 100.0  # Cap instead of infinity
if returns.std() == 0:
    return 0.0  # No volatility = no Sharpe
```

### 3. NaN Propagation
**Symptom:** One NaN corrupts entire metrics dict

**Cause:** Missing data in equity curve

**Fix:** `fillna(0)` before calculations

### 4. Annualization Errors
**Symptom:** Wrong Sharpe for non-daily data

**Cause:** Using 252 for hourly/weekly data

**Fix:** Adjust `periods_per_year`:
- Daily: 252
- Hourly: 252 × 6.5 (trading hours)
- Weekly: 52

---

## Key Insights

### The Sharpe Ratio Lie
> "A Sharpe ratio of 2+ usually means one of three things: (1) You found alpha, (2) You're overfitted, (3) You're measuring risk wrong."

**Reality check:** Most professional hedge funds target 1.0-1.5 Sharpe

### Drawdown Is Psychological
A 20% drawdown requires a 25% gain to recover. A 50% drawdown requires a 100% gain.

**Formula:** `recovery_gain = 1 / (1 - drawdown) - 1`

### Win Rate ≠ Profitability
A 40% win rate strategy can be highly profitable with:
- Win/loss ratio > 2:1
- Example: Lose $1 four times, win $3 once = net +$1

**Focus on:** Profit factor, not win rate

### The Kelly Criterion Trap
Full Kelly maximizes geometric growth but:
- Has 50% chance of 50% drawdown
- Assumes known probabilities (we don't have them)

**Practical approach:** Half-Kelly or fixed fractional (1-2% per trade)

---

## Related Concepts
- [[Backtesting]] — How metrics are generated
- [[Portfolio Metrics]] — Portfolio-level aggregation
- [[Walk-Forward Analysis]] — Out-of-sample metric validation
- [[Fundamental Analysis]] — Fundamental-based risk metrics (Piotroski, Altman Z)

## Implementation References
- `src/analytics/risk_metrics.py` — Calculator class
- `src/domain/entities/metrics.py` — RiskMetrics entity
- `src/engine/backtest/engine.py:89-93` — Metrics calculation in engine
- `src/application/services/backtest_service.py:129` — Metrics serialization
