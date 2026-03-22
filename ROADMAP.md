# TSRL — Roadmap

> Last Updated: March 2026

## ✅ Completed

| Phase | What | Tests |
|-------|------|-------|
| Domain Layer | Entities: OHLCV, Signal, Trade, Position, Metrics, Symbol | 172 |
| Data Ingestion | Yahoo Finance, NSE, caching, validation, sample data gen | 72 |
| Strategy Engine | 12 strategies, registry, parameter validation | 107 |
| Backtest Engine | Event-driven + vectorized, commission/slippage/stop-loss | 104 |
| Risk Analytics | Sharpe, Sortino, Drawdown, Calmar, Kelly, VaR, CVaR, Omega | 40 |
| Optimizer | Grid Search, Random Search, Genetic Algorithm | 20 |
| Walk-Forward | Rolling + expanding window validation | 13 |
| ML Module | 116 features, Random Forest, Gradient Boosting | 50 |
| Database | SQLAlchemy ORM, Alembic migrations, repositories | 12 |
| API | FastAPI with 7 endpoints | — |
| Frontend | React + charts (equity, drawdown, heatmap) | — |
| Testing | Unit, integration, property-based, performance | **486 tests, 89%** |

---

## 🔜 Next Steps

### Phase 1: API Expansion _(~2-3 hours)_

Add 5 endpoints to expose existing engines via REST:

| Endpoint | Engine |
|----------|--------|
| `POST /api/v1/optimization/grid` | `GridSearchOptimizer` |
| `POST /api/v1/optimization/random` | `RandomSearchOptimizer` |
| `POST /api/v1/optimization/genetic` | `GeneticAlgorithmOptimizer` |
| `POST /api/v1/walkforward/run` | `WalkForwardAnalysis` |
| `POST /api/v1/ml/train` | ML strategies |

### Phase 2: CLI Enhancement _(~1-2 hours)_

- Add `--strategy` flag (currently hardcoded to EMA)
- Add `optimize` and `walkforward` commands
- Colorized terminal output

### Phase 3: Frontend ↔ Backend Integration _(~1-2 hours)_

- Verify real backtest flow end-to-end (not just demo mode)
- Fix any data format mismatches
- Test equity curve, drawdown, and heatmap charts with real data

### Phase 4: Docker Setup _(~1-2 hours)_

- `Dockerfile` for backend
- `Dockerfile` for frontend
- `docker-compose.yml` — one-command startup

### Phase 5: Jupyter Notebooks _(~2-3 hours)_

- `01_data_exploration.ipynb` — Fetch, plot, analyze
- `02_strategy_backtest.ipynb` — Compare strategies
- `03_optimization.ipynb` — Grid search + walk-forward with heatmaps

---

## Technical Debt

- [ ] `connection.py` — 34% coverage (bypassed by in-memory test DB)
- [ ] `cli.py` / `main.py` — 0% coverage (no API/CLI tests)
- [ ] Remaining ruff warnings (ambiguous variables, exception chaining)
