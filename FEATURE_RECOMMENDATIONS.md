# Trading Research Lab — Feature Recommendations

Prioritized improvements to take TSRL from a solid foundation to a portfolio-standout project.

---

## 🔴 Priority 1: Immediate Impact

### 1.1 Frontend Charts & Visualizations
**Why:** Transforms the dashboard from "backend project with a form" to a visual trading research platform. The #1 thing that will impress anyone viewing the project.

**What to Add:**
- **Equity Curve Chart** — Plot portfolio value over time (Recharts or Lightweight Charts by TradingView)
- **Drawdown Chart** — Underwater plot showing risk periods
- **Monthly Returns Heatmap** — Classic quant visualization, color-coded grid of returns by month/year

**Tech:** Use [Recharts](https://recharts.org/) (already React-based) or [Lightweight Charts](https://tradingview.github.io/lightweight-charts/) for the candlestick-style charts.

**API Changes:**
```
GET /api/v1/backtests/{id}/equity    → returns equity curve data points
GET /api/v1/backtests/{id}/drawdown  → returns drawdown series
```

---

### 1.2 Strategy Comparison View
**Why:** Users can compare multiple strategies side-by-side — a natural feature for a "research" platform.

**What to Add:**
- Run the same backtest config against 2-3 strategies
- Display metrics side-by-side in a comparison table
- Overlay equity curves on the same chart

**API:**
```
POST /api/v1/backtests/compare
Body: {
  "strategies": ["ema_crossover", "macd", "bollinger_bands"],
  "symbol": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01"
}
```

---

### 1.3 Unit Tests for Core Modules
**Why:** Zero test coverage is the biggest risk. Any refactor could silently break things.

**What to Test First:**
1. Domain entities (OHLCV, Signal, Trade, Position, Metrics) — pure data, easiest to test
2. Risk metrics calculator — mathematical correctness is critical
3. Strategy signal generation — verify signals produce expected outputs on known data
4. Backtest engine — determinism (same input → same output)

**Target:** 80%+ coverage on domain and analytics layers.

---

## 🟡 Priority 2: Short-Term (2-4 Weeks)

### 2.1 Application Service Layer
**Why:** Business logic currently lives in API handlers (`main.py`), violating Clean Architecture.

**What to Do:**
- Create `src/application/services/backtest_service.py` — orchestrates data fetching, strategy creation, backtest execution, result persistence
- Create `src/application/services/data_service.py` — handles provider selection, caching, storage
- API handlers become thin wrappers that call services

### 2.2 Parameter Optimization (Grid Search)
**Why:** You already have `StrategyParameter` with `min_value`, `max_value`, `step` — the infrastructure is there.

**What to Add:**
```python
class GridSearchOptimizer:
    def optimize(self, strategy_class, data, param_grid) -> OptimizationResult:
        # Test all parameter combinations
        # Return sorted results with Sharpe, return, drawdown for each combo
```

**API:**
```
POST /api/v1/optimization/grid
Body: {
  "strategy": "ema_crossover",
  "params": {
    "fast_period": {"min": 5, "max": 20, "step": 5},
    "slow_period": {"min": 20, "max": 60, "step": 10}
  },
  "symbol": "AAPL", ...
}
```

**Frontend:** Show a parameter heatmap — X axis = fast_period, Y axis = slow_period, color = Sharpe ratio.

### 2.3 Walk-Forward Validation
**Why:** Separates "toy backtester" from "serious research tool." Proves strategies aren't overfit.

**What to Add:**
```python
class WalkForwardValidator:
    def validate(self, strategy_class, data, n_splits, train_pct) -> WalkForwardResult:
        # Split data into rolling train/test windows
        # Optimize on train, evaluate on test
        # Compare in-sample vs out-of-sample performance
```

### 2.4 Candlestick Chart on Dashboard
**Why:** A trading platform without a price chart feels incomplete.

**Tech:** Use **Lightweight Charts** (TradingView's open-source library) — it's built for exactly this.
- Show OHLCV candlesticks
- Overlay buy/sell signal markers
- Overlay indicator lines (EMA, Bollinger Bands, etc.)

---

## 🟠 Priority 3: Medium-Term (1-2 Months)

### 3.1 ML Signal Strategy
**What to Add:**
- Feature engineering pipeline (lag features, rolling stats, technical indicators)
- XGBoost classifier for direction prediction
- Model persistence (joblib)
- Walk-forward ML training (no data leakage)

### 3.2 Jupyter Notebook Examples
**Why:** Makes the project usable as a *research lab*, not just a web app. Interviewers love documented analysis.

**Add 3 Notebooks:**
1. `notebooks/01_data_exploration.ipynb` — Fetch data, plot, analyze distributions
2. `notebooks/02_strategy_backtest.ipynb` — Run backtests programmatically, compare strategies
3. `notebooks/03_optimization.ipynb` — Parameter optimization with heatmaps

### 3.3 Docker One-Command Setup
```yaml
# docker-compose.yml
services:
  backend:
    build: .
    ports: ["8000:8000"]
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
```
Makes it trivially easy for anyone to run the project.

### 3.4 Volatility Strategies
Fill the `strategies/volatility/` directory:
- **ATR Expansion** — Trade when volatility expands beyond threshold
- **Volatility Breakout** — Keltner Channel or ATR-based entries
- **Mean Reversion on IV** — If you add options data later

---

## 🔵 Priority 4: Long-Term / Nice-to-Have

### 4.1 Paper Trading Simulator
- Simulated real-time feed using historical data replayed at intervals
- Order execution simulation with realistic delays
- Live equity tracking dashboard

### 4.2 Advanced Risk Metrics
- Kelly Criterion, Value at Risk (VaR), Conditional VaR
- Omega Ratio, Ulcer Index, Tail Ratio
- Return distribution analysis (skewness, kurtosis)

### 4.3 Multi-Asset Portfolio Optimization
- Mean-variance optimization (Markowitz)
- Risk parity allocation
- Correlation matrix visualization

### 4.4 Real-Time Data (WebSocket)
- Stream live prices via WebSocket
- Real-time signal generation
- Alert system (email/push when signals fire)

---

## Quick Reference: Effort vs. Impact

```
HIGH IMPACT
│
│  ★ Charts/Viz     ★ Strategy Compare    ★ Walk-Forward
│  ★ Unit Tests     ★ Grid Optimizer      ★ Candlestick Chart
│
│          ★ Service Layer    ★ ML Module
│          ★ Notebooks        ★ Docker
│
│                    ★ Paper Trading
│                    ★ Volatility Strats
│                    ★ Advanced Metrics
│
└──────────────────────────────────────── HIGH EFFORT
```

---

*Created: February 2026*
