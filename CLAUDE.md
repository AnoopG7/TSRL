# CLAUDE.md — TSRL Project Context

## 1. Project Identity

**Project Name:** TSRL (Trading Strategy Research Lab)

**What it is:** A production-grade quantitative trading research platform combining event-driven backtesting, ML-powered strategies, and fundamental analysis. Built with Clean Architecture and Domain-Driven Design patterns.

**Primary Purpose:** Enable systematic trading strategy research, backtesting, and optimization for US/India equities and crypto markets.

**Target User:** Quantitative researchers, algorithmic traders, and developers building systematic trading strategies.

---

## 2. Tech Stack

### Backend (Python 3.11+)

| Library | Version | Role |
|---------|---------|------|
| fastapi | 0.109.0 | REST API framework |
| uvicorn | 0.27.0 | ASGI server |
| pydantic | 2.5.3 | Data validation |
| sqlalchemy | 2.0.25 | ORM |
| alembic | 1.13.1 | Database migrations |
| pandas | >=2.2.0 | Data processing |
| numpy | >=1.26.3 | Numerical computing |
| yfinance | 0.2.35 | Yahoo Finance data |
| nsetools | 1.0.11 | NSE India data |
| scikit-learn | 1.4.0 | ML pipelines |
| xgboost | 2.0.3 | Gradient boosting |
| plotly | 5.18.0 | Visualization |
| structlog | 24.1.0 | Structured logging |
| click | 8.1.7 | CLI framework |
| joblib | 1.3.2 | ML model persistence |

**Database:** SQLite with SQLAlchemy ORM + Alembic migrations

**Data Providers:**
- `yahoo_provider.py` — Yahoo Finance (free, US stocks)
- `nse_provider.py` — NSE India (free, Indian stocks)
- `alpha_vantage_provider.py` — Alpha Vantage (free tier)
- `fundamental_provider.py` — FMP + yfinance hybrid (fundamentals)
- `news_provider.py` — Finnhub (news/sentiment)
- `insider_provider.py` — Finnhub/FMP (insider trading)

### Frontend

| Technology | Role |
|------------|------|
| React 19 + TypeScript | UI framework |
| Vite 7.3 | Build tool |
| Tailwind CSS v4 | Styling |
| Zustand | State management |
| Recharts | Charting |
| Radix UI | UI primitives |

**Chart Components** (`frontend/src/components/charts/`):
- `EquityCurveChart.tsx` — Portfolio equity over time
- `DrawdownChart.tsx` — Drawdown visualization
- `FinancialTrendsChart.tsx` — Revenue, margins, FCF
- `EpsSurpriseChart.tsx` — EPS beat/miss history
- `RadarScoreChart.tsx` — Health score radar
- `MonthlyReturnsHeatmap.tsx` — Monthly returns heatmap
- `ParameterSensitivityChart.tsx` — Optimization sensitivity

**Pages** (`frontend/src/pages/`):
| Page | Purpose |
|------|---------|
| `BacktestPage.tsx` | Single-strategy backtest with charts |
| `ComparisonPage.tsx` | Multi-strategy comparison |
| `FundamentalsPage.tsx` — Fundamental analysis (Overview, Financials, Ratios, News, Insiders) |
| `OptimizationPage.tsx` | Parameter optimization (Grid/Random/Genetic) |
| `PortfolioPage.tsx` | Multi-symbol portfolio backtest |
| `WalkForwardPage.tsx` | Walk-forward validation |

---

## 3. Architecture (Clean Architecture + DDD)

```
Presentation (API/CLI/Frontend)
    ↓
Application Services (BacktestService, DataService, FundamentalService)
    ↓
Domain Layer (Entities, Value Objects) — NO external dependencies
    ↓
Infrastructure (SQLAlchemy, Data Providers, ML)
    ↓
Data Layer (SQLite, Yahoo Finance, NSE, FMP)
```

### Domain Entities (`src/domain/entities/`)

| Entity | Purpose |
|--------|---------|
| `ohlcv.py` | OHLCV price data |
| `signal.py` | Trading signals (SignalType, SignalStrength) |
| `trade.py` | Trade records (TradeSide, TradeStatus) |
| `position.py` | Position tracking (PositionSide) |
| `metrics.py` | RiskMetrics (50+ metrics) |
| `portfolio_metrics.py` | PortfolioMetrics (correlation, risk contribution) |
| `fundamental.py` | FundamentalReport (ratios, health scores) |
| `rebalance_event.py` | RebalanceEvent for portfolio rebalancing |

**Value Objects:** `Symbol`, `Timeframe` (`src/domain/value_objects/`)

### Application Services (`src/application/services/`)

| Service | Responsibility |
|---------|----------------|
| `backtest_service.py` | Orchestrates: data → strategy → engine → persistence |
| `data_service.py` | Data fetching, caching, provider selection |
| `fundamental_service.py` | Fundamental analysis, health scores, ratios |

### Infrastructure (`src/infrastructure/`)

- `data_providers/` — Yahoo, NSE, Alpha Vantage, FMP, Fundamental, News, Insider
- `database/` — SQLAlchemy ORM, repositories (BacktestRepository, OHLCVRepository)
- `logging/` — structlog setup

### Engine (`src/engine/`)

| Module | Purpose |
|--------|---------|
| `backtest/engine.py` | BacktestEngine, VectorizedBacktestEngine |
| `backtest/portfolio_engine.py` | PortfolioBacktestEngine, MultiStrategyPortfolioEngine |
| `optimizer/optimizer.py` | GridSearch, RandomSearch, GeneticAlgorithm |
| `walkforward/walkforward.py` | WalkForwardAnalysis (rolling/expanding windows) |

### Strategies (`src/strategies/`)

**Families:**
- `momentum/` — EMA, MACD, RSI, MA Ribbon, Volume
- `mean_reversion/` — Bollinger Bands
- `breakout/` — Price/volume breakouts
- `volatility/` — (placeholder)
- `ml/` — Random Forest, Gradient Boosting

### Analytics (`src/analytics/`)

- `portfolio_metrics.py` — Correlation matrix, risk contribution
- `risk_metrics.py` — 50+ metrics (Sharpe, Sortino, VaR, CVaR, Calmar, Kelly, Omega)

### ML (`src/ml/`)

- `feature_engineering/features.py` — 116 features (lag, rolling, technicals, volume)
- `strategies/ml_strategies.py` — MLRandomForestStrategy, MLGradientBoostingStrategy

### Frontend (`frontend/src/`)

- `pages/` — 6 pages (Backtest, Comparison, Fundamentals, Optimization, Portfolio, WalkForward)
- `components/` — UI components, chart components
- `hooks/` — API hooks (apiHooks.ts)
- `store/` — Zustand stores (useBacktestStore, useDataSourceStore, useThemeStore)

### Notebooks (`notebooks/`)

| Notebook | Purpose |
|----------|---------|
| `01_data_exploration.ipynb` | OHLCV data exploration |
| `02_strategy_backtest.ipynb` | Strategy backtesting |
| `03_optimization.ipynb` | Parameter optimization |

---

## 4. Strategy Registry

**Location:** `src/strategies/registry.py`

**Pattern:** Decorator-based auto-discovery

```python
from src.strategies.registry import register_strategy

@register_strategy("ema_crossover")
class EMACrossoverStrategy(BaseStrategy):
    ...
```

**All Strategies:**

| Family | Strategies |
|--------|------------|
| **Momentum** | `ema_crossover`, `rsi_mean_reversion`, `macd`, `ma_ribbon`, `triple_ma`, `volume_profile`, `volume_breakout` |
| **Mean Reversion** | `bollinger_bands`, `bbands` |
| **Breakout** | `breakout` |
| **ML** | `ml_random_forest`, `ml_gradient_boosting` |

**Registry Methods:**
- `StrategyRegistry.auto_discover()` — Load all @register_strategy decorated classes
- `StrategyRegistry.get(name)` — Get strategy class by name
- `StrategyRegistry.list_strategies()` — List all strategy names
- `StrategyRegistry.get_all_strategy_info()` — Get full strategy metadata

---

## 5. Data Flow

```
Raw Data → Data Provider → Cache Layer → Domain Entities → Services → Engine → Analytics → API → Frontend
```

**Two Cache Layers:**
1. `src/infrastructure/data_providers/cache.py` — OHLCV data caching
2. `src/infrastructure/data_providers/fundamental_cache.py` — Fundamental data caching (JSON, TTL-based)

**Flow:**
1. `DataService.ingest_and_persist()` fetches OHLCV via provider
2. Data validated and stored in SQLite via `OHLCVRepository`
3. `BacktestService.run_backtest()` loads data, creates strategy instance
4. `BacktestEngine.run()` processes bars, generates signals, executes trades
5. `RiskMetrics.calculate()` computes performance metrics
6. `BacktestRepository` persists results
7. API returns `BacktestResponse` to frontend

---

## 6. Database Schema

**Tables** (`src/infrastructure/database/models/orm_models.py`):
- `symbols` — Trading symbols (ticker, exchange, currency)
- `ohlcv` — Price data (symbol_id, timestamp, O/H/L/C/V)
- `backtests` — Backtest runs (name, strategy_id, initial_capital, results)
- `trades` — Individual trades (backtest_id, entry/exit, P&L)
- `signals` — Generated signals (backtest_id, timestamp, type, strength)
- `optimization_runs` — Optimization results (params, metrics)
- `ml_models` — Trained model metadata
- `walk_forward_results` — Walk-forward analysis results

**Repositories:**
- `BacktestRepository` — CRUD for backtest runs
- `OHLCVRepository` — Price data persistence
- `TradeRepository` — Trade record persistence

**Migrations:** `alembic/versions/` — Auto-generated schema migrations

---

## 7. API Endpoints

### Strategies
- `GET /api/v1/strategies` — List all strategies
- `GET /api/v1/strategies/{name}` — Get strategy details

### Data
- `POST /api/v1/data/ingest` — Fetch and store OHLCV data

### Backtests
- `GET /api/v1/backtests` — List backtests
- `POST /api/v1/backtests/run` — Run single backtest
- `POST /api/v1/backtests/compare` — Compare multiple strategies
- `POST /api/v1/backtests/portfolio` — Multi-symbol portfolio backtest

### Optimization
- `POST /api/v1/optimization/grid` — Grid search
- `POST /api/v1/optimization/random` — Random search
- `POST /api/v1/optimization/genetic` — Genetic algorithm

### Walk-Forward
- `POST /api/v1/walkforward/run` — Walk-forward analysis

### Fundamentals
- `GET /api/v1/fundamentals/{symbol}` — Get fundamental analysis
- `GET /api/v1/fundamentals/compare` — Compare multiple symbols
- `GET /api/v1/fundamentals/{symbol}/insiders` — Insider trading data

### ML
- `POST /api/v1/ml/train` — Train ML model

### Health
- `GET /api/v1/health` — Health check

---

## 8. Current State (from PROGRESS.md)

**Working:**
- ✅ Full backtest engine (event-driven + vectorized)
- ✅ Portfolio backtesting (multi-symbol, rebalancing)
- ✅ 10+ strategies across 4 families
- ✅ 3 optimizers (Grid, Random, Genetic)
- ✅ Walk-forward analysis
- ✅ ML strategies (Random Forest, Gradient Boosting)
- ✅ 116-feature ML pipeline
- ✅ Fundamental analysis (health scores, ratios, insider tracking)
- ✅ 50+ risk metrics
- ✅ FastAPI with 16+ endpoints
- ✅ React frontend with 6 pages
- ✅ Database persistence with Alembic migrations
- ✅ 486 tests (89% coverage)

**In Progress:**
- 🔧 Enhanced chart visualizations (crosshair sync, trade markers)
- 🔧 Fundamental analysis UI enhancements

**Blocked:**
- ⏸️ Paper trading (awaiting real-time data feed decision)

---

## 9. Active Development Priorities (from NEXT_STEPS.md)

1. **Data validation pipeline** — Forward-fill gaps, corporate actions handling
2. **Enhanced visualizations** — Monthly returns heatmap, rolling metrics plots
3. **Paper trading simulator** — Real-time feed, order execution
4. **Full test coverage** — Target 80%+ across all modules
5. **API expansion** — More endpoints for trades, equity curves, ML models

---

## 10. Architectural Decisions

| Decision | Why |
|----------|-----|
| **Clean Architecture** | Separation of concerns, testability, maintainability |
| **Domain-Driven Design** | Complex trading logic requires clear entity boundaries |
| **Zustand over Redux** | Simpler API, less boilerplate, built-in persistence |
| **SQLite + Alembic** | Simple deployment, upgradeable to PostgreSQL |
| **yfinance + NSE dual** | Free data sources for US and Indian markets |
| **Event-driven backtesting** | Realistic simulation of bar-by-bar execution |
| **Strategy registry pattern** | Plugin architecture for easy strategy addition |
| **116 ML features** | Comprehensive feature set for ML strategies |

---

## 11. Coding Standards

**Python:**
- Sync (not async) for business logic, async for API endpoints
- Type hints throughout (mypy enforced)
- Pydantic for data validation, dataclasses for config/result objects
- structlog for all logging (no print statements)
- ruff for linting, mypy for type checking

**Frontend:**
- Functional components only (no class components)
- Named exports (not default exports)
- TypeScript strict mode
- Zustand for state (no Redux)
- Recharts for all charts

**Testing:**
- Unit tests: `tests/unit/` — Domain, strategies, engine, analytics
- Integration tests: `tests/integration/` — Full workflows, API
- Property-based: `tests/unit/test_properties.py` — Hypothesis tests
- Performance: `tests/performance/` — Benchmarks

**File Naming:**
- Python: `snake_case.py` (modules), `PascalCase` (classes)
- TypeScript: `PascalCase.tsx` (components), `camelCase.ts` (utils)
- Tests: `test_*.py`

---

## 12. Graphify Integration

**Purpose:** Reduce token usage by extracting code structure into a queryable graph.

**Commands:**
```bash
# Build/rebuild the graph
graphify update .

# Query the graph
graphify query "Where is portfolio execution handled?"
graphify query "Which files implement momentum strategies?"
graphify query "How does data flow through the system?"

# Get shortest path between concepts
graphify path "BacktestConfig" "PortfolioMetrics"

# Explain a node and its neighbors
graphify explain "BaseStrategy"
```

**Output:** `graphify-out/`
- `graph.json` — Full graph structure (2080 nodes, 6385 edges)
- `GRAPH_REPORT.md` — Analysis report with god nodes, communities
- `graph.html` — Interactive visual exploration

**God Nodes** (most connected):
1. `BacktestConfig` (187 edges)
2. `BaseStrategy` (179 edges)
3. `BacktestEngine` (116 edges)
4. `FundamentalReport` (108 edges)
5. `FundamentalService` (101 edges)

**Workflow:**
1. **Start of session:** `graphify query "what did we work on last?"`
2. **During coding:** Query for context instead of reading files
3. **After changes:** `graphify update .` to refresh

---

## 13. Do NOT Do (Hard Rules)

- ❌ Do not use `print()` for logging — use `src/infrastructure/logging/setup.py`
- ❌ Do not add new data providers without implementing `base.py` interface
- ❌ Do not create strategies without registering in `registry.py`
- ❌ Do not modify domain entities without updating tests in `tests/unit/domain/`
- ❌ Do not touch `alembic/versions/` manually — use `alembic revision` commands
- ❌ Do not install frontend packages without checking existing components
- ❌ Do not hardcode symbols — use `domain/value_objects/symbol.py`
- ❌ Do not modify business logic without understanding the layer boundaries
- ❌ Do not skip Graphify updates after significant code changes

---

## Quick Commands

### Backend
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python src/main.py          # API server
PYTHONPATH=. python -m src.cli --help    # CLI
```

### Frontend
```bash
cd frontend && npm install
npm run dev       # Dev server (port 5173)
npm run build     # Production build
```

### Testing
```bash
python -m pytest tests/ -q                    # All tests
python -m pytest tests/ --cov=src             # With coverage
python -m pytest tests/unit/strategies/ -v    # Strategy tests
```

### Linting
```bash
ruff check src/ tests/       # Lint
mypy src/                    # Type check
ruff check --fix src/        # Auto-fix
```

---

*Last Updated: 2026-04-29*
