# Architecture Decisions

## Definition
The "why" behind TSRL's structural choices. Not what the code does, but why it's shaped this way. These are the decisions that are expensive to reverse.

## Why It Matters
- **Prevent rework**: Understanding past reasoning prevents re-debating settled questions
- **Onboarding**: New contributors need the "why", not just the "what"
- **Evolution**: When the context changes, you can re-evaluate the original reasoning

---

## ADR-1: Clean Architecture (Layered)

**Decision:** Separate the system into 4 layers: Domain, Application, Infrastructure, Engine

```
src/
├── domain/          → Entities, value objects (no dependencies)
├── application/     → Services (orchestration, depends on domain)
├── infrastructure/  → Database, APIs, file I/O (depends on domain)
├── engine/          → Backtest, optimizer, walkforward (depends on domain)
└── strategies/      → Strategy implementations (depends on domain)
```

**Why:** Trading logic (strategies, signals) must not depend on infrastructure (database, API). You should be able to:
- Swap SQLite for Postgres without touching strategy code
- Replace Yahoo with a custom data provider without changing the engine
- Test strategies in isolation (no DB, no network)

**Trade-off:** More boilerplate (repository pattern, service layer). But trading systems live for years — the abstraction pays off when you migrate databases or change providers.

---

## ADR-2: Dual Backtest Engine (Event-Driven + Vectorized)

**Decision:** Two engines for different use cases instead of one configurable engine.

**Why:**
- Event-driven: Realistic execution, position tracking, complex exits — needed for final validation
- Vectorized: 10× faster, needed for optimization (600+ backtests per run)
- Sharing an engine with a "mode" flag would mean compromising both: too slow for optimization, too simple for production

**Trade-off:** Code duplication (~30% overlap). The vectorized engine has its own `_extract_trades_from_signals()` that duplicates the event-driven logic. Bugs must be fixed in both.

**Current gap:** The advanced engine (`advanced_engine.py`) is a third variant with risk management. Three engines means three places to fix bugs.

---

## ADR-3: Strategy Registry Pattern

**Decision:** Use `@register_strategy("name")` decorator + `auto_discover()` for strategy lookup.

```python
@register_strategy("ema_crossover")
class EMACrossoverStrategy(BaseStrategy):
    ...

# At startup:
StrategyRegistry.auto_discover()  # Scans momentum/, breakout/, etc.

# At runtime:
strategy = StrategyRegistry.create("ema_crossover", fast_period=12)
```

**Why:**
- Zero-config strategy addition: Drop a file in the right folder, done
- API-friendly: Frontend sends `strategy_name` string, backend resolves it
- Type-safe: Decorator enforces `BaseStrategy` subclass

**Trade-off:** Magic — strategies aren't explicitly imported anywhere. If `auto_discover()` fails silently, strategies disappear without error.

**Discovery path:** `src/strategies/registry.py:56-77` — scans `momentum/`, `breakout/`, `volatility/`, `mean_reversion/` subdirectories.

---

## ADR-4: SQLite for Persistence

**Decision:** Use SQLite (via SQLAlchemy + Alembic) as the primary database.

**Why:**
- Zero setup: No server process, no Docker, no credentials
- Portable: Database is a single file (`.db`)
- Good enough: Trading systems don't need concurrent writes (single user, sequential backtests)

**When to migrate:** If you need:
- Multi-user access (web deployment)
- Concurrent writes (parallel optimizations writing results)
- More than ~1M rows (SQLite handles this fine, but Postgres is faster)

**Migration path:** SQLAlchemy makes this easy — change the connection string, run Alembic.

---

## ADR-5: Zustand over Redux (Frontend)

**Decision:** Use Zustand for React state management instead of Redux.

**Why:**
- Less boilerplate: No actions, reducers, or action types
- TypeScript-first: Zustand's types are simpler
- Small app: TSRL's frontend has 3 stores (backtest, theme, data source) — Redux would be overkill

**Trade-off:** Less ecosystem tooling. No Redux DevTools time-travel debugging.

---

## ADR-6: `before_backtest()` Hook

**Decision:** Strategies can transform data before backtesting via `before_backtest()`.

```python
class BaseStrategy:
    def before_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        return data  # Default: no-op
```

**Why:**
- Some strategies need indicator pre-computation (e.g., RSI, Bollinger Bands)
- The engine shouldn't know about strategy-specific preprocessing
- Allows data augmentation (add columns) without modifying the DataFrame in `generate_signals()`

**Trade-off:** Strategies can mutate the data in unexpected ways. If `before_backtest()` drops rows or reindexes, the engine may break.

---

## ADR-7: Two Cache Systems

**Decision:** OHLCV data has NO cache. Fundamental data has file-based JSON cache with TTL.

**Why OHLCV isn't cached:**
- Each backtest should use fresh data (reproducibility)
- The optimizer passes pre-fetched data to all iterations (no redundant fetches)
- Caching introduces stale data risk

**Why fundamentals ARE cached:**
- FMP API has rate limits (250 calls/day on free tier)
- Financial statements update quarterly — caching for 7 days is safe
- The comparison feature hits 2× providers per request

**See:** [[Caching Strategy]] for detailed TTL logic

---

## ADR-8: Python Backend + React Frontend

**Decision:** FastAPI (Python) for backend, React + Vite + TypeScript for frontend.

**Why Python backend:**
- pandas/numpy are the standard for financial data analysis
- Strategy authors expect Python (not TypeScript)
- ML pipeline needs scikit-learn/xgboost (Python only)

**Why React frontend:**
- Recharts for equity curves, drawdown charts, heatmaps
- Component model fits the dashboard layout
- Zustand for minimal state management

**Why not Jupyter?** Jupyter is for exploration. TSRL needs:
- Persistent backtest history
- Compare mode (side-by-side strategies)
- Shareable results (URL-based)

---

## Key Insight

### Architecture Is About Trade-offs
Every decision above has a downside. The goal isn't perfection — it's making the trade-offs explicit so future you (or future contributors) can re-evaluate them when the context changes.

---

## Related Concepts
- [[Domain Model]] — The entity layer these decisions shape
- [[Event System]] — ADR-2 in action
- [[Data Pipeline]] — ADR-7 in action
- [[Strategy Design]] — ADR-3 and ADR-6 in action

## Implementation References
- `src/` — Layered architecture (ADR-1)
- `src/strategies/registry.py` — Strategy registry (ADR-3)
- `src/infrastructure/database/connection.py` — SQLite config (ADR-4)
- `frontend/src/stores/` — Zustand stores (ADR-5)
