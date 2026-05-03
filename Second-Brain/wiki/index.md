# TSRL Wiki — Trading Strategy Research Lab

> **Purpose:** Decision-making intelligence layer for systematic trading. Not a documentation dump — every note must be actionable.

---

## Core Concepts

### Philosophy & Design
- [[Strategy Design]] — 8 principles for building robust trading strategies
- [[Architecture Decisions]] — Why Clean Architecture, dual engines, registry pattern, SQLite

### Execution
- [[Backtesting]] — Event-driven vs vectorized vs advanced engines, look-ahead bias prevention
- [[Event System]] — Signal → position → trade event pipeline, exit priority chain
- [[Trade Lifecycle]] — From signal generation through execution costs to final P&L
- [[Walk-Forward Analysis]] — Out-of-sample validation, overfitting detection
- [[Optimization]] — Grid vs Random vs Genetic search, metric selection trade-offs

### Risk & Analytics
- [[Risk Metrics]] — Sharpe, Sortino, Max DD, Kelly, 50+ metrics with formulas
- [[Portfolio Metrics]] — Correlation, beta/alpha, risk contribution, diversification ratio
- [[Position Sizing]] — Fixed fractional vs ATR-based, Kelly criterion math, the 2% rule
- [[Fundamental Analysis]] — Health scores, Piotroski F-Score, Altman Z-Score, valuation

### Data & Infrastructure
- [[Data Pipeline]] — Provider abstraction, market formatting, Yahoo/AV/FMP
- [[Caching Strategy]] — No cache for OHLCV (intentional), TTL cache for fundamentals
- [[Domain Model]] — Entity catalog: Trade, Position, Signal, RiskMetrics, PortfolioMetrics

### Intelligence
- [[Regime Detection]] — Trending vs ranging vs volatile, strategy selection matrix
- [[ML Pipeline]] — 116 features, label engineering, RF/GBM strategies, leakage prevention

### Strategies (Detailed Notes)
- [[EMA Crossover]] — Momentum foundation, parameter sensitivity, whipsaw avoidance
- [[MACD Strategy]] — Signal line crossover, histogram leading, centerline strategies
- [[Bollinger Bands]] — Mean reversion, band walks, volatility squeeze
- [[Breakout]] — Channel breakout with ATR signal strength, false breakout analysis
- [[Volume Strategies]] — Volume Profile + Volume Breakout, volume-precedes-price
- [[MA Ribbon]] — Triple MA alignment, trend structure, regime proxy

---

## Strategy Registry

| Strategy | Type | Status | Key Insight |
|----------|------|--------|-------------|
| [[ema_crossover]] | Momentum | ✅ | Fast/slow EMA cross; 12/26 standard for reason |
| [[rsi_mean_reversion]] | Mean Reversion | ✅ | Oversold/overbought; add ADX filter for ranging |
| [[macd]] | Momentum | ✅ | Double-smoothed EMA; later signals but fewer whipsaws |
| [[ma_ribbon]] | Momentum | ✅ | Multiple MAs visualize trend structure |
| [[triple_ma]] | Momentum | ✅ | Adds confirmation MA; reduces false signals |
| [[volume_profile]] | Momentum | ✅ | Volume-based S/R levels |
| [[volume_breakout]] | Momentum | ✅ | Volume surge precedes price moves |
| [[breakout]] | Breakout | ✅ | Price expansion; use ATR for stops |
| [[bollinger_bands]] | Mean Reversion | ✅ | 2σ bands; watch for band walks |
| [[bbands]] | Breakout | ✅ | BB breakout variant |
| [[ml_random_forest]] | ML | ✅ | 116 features; 55-60% accuracy is excellent |
| [[ml_gradient_boosting]] | ML | ✅ | Higher accuracy, more overfitting risk |

---

## System Architecture

### Data Flow
```
Raw Data → Provider → Cache → Domain Entities → Services → Engine → Analytics → API → Frontend
```

### Key Components
| Component | File | Responsibility |
|-----------|------|----------------|
| Backtest Engine | `src/engine/backtest/engine.py` | Event-driven + vectorized execution |
| Portfolio Engine | `src/engine/backtest/portfolio_engine.py` | Multi-symbol, rebalancing |
| Backtest Service | `src/application/services/backtest_service.py` | Orchestration layer |
| Risk Metrics | `src/analytics/risk_metrics.py` | 50+ performance metrics |
| Portfolio Metrics | `src/analytics/portfolio_metrics.py` | Correlation, risk contribution |
| Base Strategy | `src/strategies/base.py` | Strategy interface contract |
| Strategy Registry | `src/strategies/registry.py` | Auto-discovery pattern |

### Database Schema
- `symbols` — Trading symbols
- `ohlcv` — Price data (timestamp, O/H/L/C/V)
- `backtests` — Backtest runs
- `trades` — Individual trades
- `signals` — Generated signals
- `optimization_runs` — Optimization results
- `ml_models` — Trained model metadata
- `walk_forward_results` — Walk-forward analysis

---

## Decision Frameworks

### Strategy Selection
```
Market Regime → Strategy Type
├── Strong Trend → Momentum (EMA, MACD, Breakout)
├── Sideways/Range → Mean Reversion (BB, RSI)
├── High Volatility → Breakout
└── Unknown/Changing → ML (adaptive)
```

### Position Sizing
```python
# Kelly Criterion (theoretical optimal)
kelly_fraction = W - (1-W) / R

# Practical: Half-Kelly or fixed fractional
position_size = capital * min(kelly_fraction / 2, 0.02)  # Max 2%
```

### Risk Limits
| Level | Limit | Action |
|-------|-------|--------|
| Per Trade | 2% capital | Position size |
| Per Strategy | 10% capital | Max allocation |
| Per Portfolio | 20% drawdown | Circuit breaker |

---

## Failure Mode Library

### Backtesting Pitfalls
- **Look-ahead bias:** Signal at close, entry at same close (fixed in engine.py:198)
- **Overfitting:** In-sample Sharpe > 2.0, OOS < 0.5
- **Commission bleed:** Strategy profitable before costs, losing after
- **Survivorship bias:** Testing only current constituents

### Live Trading Pitfalls
- **Slippage underestimation:** Fixed model doesn't capture gaps/liquidity
- **Regime change:** Strategy works in bull, fails in bear
- **Strategy decay:** Edge arbitraged away over time
- **Gap risk:** Earnings/news skip through stops

### ML Pitfalls
- **Label leakage:** Future data in features
- **Feature decay:** Signal disappears as others discover it
- **Regime blindness:** Model trained on bull market fails in bear
- **Overfitting:** 116 features, 50% accuracy

---

## Research Sessions

### Session Log
- [[log]] — Append-only research and development log

### Stocks Tracked
| Ticker | Sector | Status | Last Updated |
|--------|--------|--------|--------------|
| AAPL | Technology | Active | — |
| MSFT | Technology | Active | — |
| GOOGL | Technology | Active | — |
| AMZN | Consumer | Active | — |
| NVDA | Semiconductor | Active | — |
| RELIANCE | India (Energy) | Active | — |

---

## External Resources

### Data Providers
- Yahoo Finance — US stocks (free)
- NSE Tools — Indian stocks (free)
- Alpha Vantage — Alternative data (free tier)
- FMP — Fundamental data (paid)
- Finnhub — News/sentiment (freemium)

### Research Sources
*Add URLs as you research — one per line*
- 

---

## Quick Reference

### CLI Commands
```bash
# Run backtest
PYTHONPATH=. python -m src.cli backtest --strategy ema_crossover --symbol AAPL

# Run optimization
PYTHONPATH=. python -m src.cli optimize --strategy ema_crossover --symbol AAPL

# Run walk-forward
PYTHONPATH=. python -m src.cli walkforward --strategy ema_crossover --symbol AAPL

# List strategies
PYTHONPATH=. python -m src.cli strategies
```

### API Endpoints
```
GET  /api/v1/strategies              # List all strategies
POST /api/v1/backtests/run           # Run single backtest
POST /api/v1/backtests/compare       # Compare strategies
POST /api/v1/backtests/portfolio     # Multi-symbol portfolio
POST /api/v1/optimization/grid       # Grid search
POST /api/v1/optimization/random     # Random search
POST /api/v1/optimization/genetic    # Genetic algorithm
POST /api/v1/walkforward/run         # Walk-forward analysis
GET  /api/v1/fundamentals/{symbol}   # Fundamental analysis
```

### Key Thresholds
| Metric | Threshold | Meaning |
|--------|-----------|---------|
| Sharpe > 1.5 | Excellent | Or overfitted |
| Win Rate > 55% | Good | For mean reversion |
| Profit Factor > 1.5 | Good | Edge exists |
| Max DD < 15% | Excellent | Psychological comfort |
| OOS/IS Ratio > 0.5 | Acceptable | Not overfitted |

---

## Navigation
- [CLAUDE.md](../CLAUDE.md) — Project context and architecture
- [docs/system/](../docs/system/) — System documentation
- [graphify-out/GRAPH_REPORT.md](../graphify-out/GRAPH_REPORT.md) — Code graph analysis
