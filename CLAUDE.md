# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Commands

### Backend Setup & Development
```bash
# Create and activate virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run API server
PYTHONPATH=. python src/main.py

# Run CLI
PYTHONPATH=. python -m src.cli --help
```

### Frontend Setup & Development
```bash
cd frontend && npm install
npm run dev        # Start dev server (port 5173)
npm run build      # Production build
npm run lint       # ESLint check
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -q

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run specific test categories
python -m pytest tests/unit/domain/ -v       # Domain entities
python -m pytest tests/unit/strategies/ -v   # Strategy logic
python -m pytest tests/integration/ -v       # Integration tests
python -m pytest tests/unit/test_properties.py  # Property-based tests
python -m pytest tests/performance/ -v       # Performance benchmarks

# Run single test file
python -m pytest tests/path/to/test_file.py::test_function_name -v
```

### Linting & Type Checking
```bash
# Lint with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/

# Fix auto-fixable lint issues
ruff check --fix src/
```

### CLI Commands
```bash
# List strategies
PYTHONPATH=. python -m src.cli strategies

# Run backtest
PYTHONPATH=. python -m src.cli backtest --strategy ema_crossover --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01

# Optimize parameters
PYTHONPATH=. python -m src.cli optimize --strategy ema_crossover --symbol AAPL --method grid

# Walk-forward analysis
PYTHONPATH=. python -m src.cli walkforward --strategy ema_crossover --symbol AAPL

# Fetch OHLCV data
PYTHONPATH=. python -m src.cli fetch-data --symbol AAPL
```

## Architecture Overview

### Clean Architecture Layers

```
Presentation (API/CLI/Frontend)
    ↓
Application Services (BacktestService, DataService)
    ↓
Domain Layer (Entities, Value Objects, Events)
    ↓
Infrastructure (Database, Data Providers, ML)
    ↓
Data Layer (SQLite, Yahoo Finance, NSE)
```

**Key Principle**: Dependencies point inward. Domain layer has no external dependencies.

### Directory Structure

```
TSRL/
├── src/
│   ├── domain/           # Core entities (Trade, Position, Signal, OHLCV, Metrics)
│   ├── application/      # Services (BacktestService, DataService)
│   ├── infrastructure/   # SQLAlchemy, data providers (Yahoo, NSE, Alpha Vantage)
│   ├── strategies/       # 12+ strategies with registry pattern
│   ├── engine/           # Backtest, optimizer, walkforward engines
│   ├── ml/               # Feature engineering (116 features), RF/GBM classifiers
│   ├── analytics/        # 50+ risk metrics (Sharpe, Sortino, VaR, CVaR)
│   ├── main.py           # FastAPI entry point
│   └── cli.py            # Click CLI
├── frontend/src/         # React 19 + TypeScript + Zustand + Recharts
├── tests/                # 486 tests (89% coverage)
├── config/settings.yaml  # Configuration
└── data/                 # SQLite DB, cache, models
```

### Key Patterns

**Strategy Registry** (`src/strategies/registry.py`):
```python
from src.strategies.registry import register_strategy, StrategyRegistry

# Decorator pattern for registering strategies
@register_strategy("my_strategy")
class MyStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame: ...
    def entry_conditions(self, data: pd.DataFrame, idx: int) -> bool: ...
    def exit_conditions(self, data: pd.DataFrame, idx: int) -> bool: ...

# Auto-discovery loads strategies from momentum/, breakout/, volatility/, mean_reversion/
StrategyRegistry.auto_discover()
```

**Event-Driven Backtesting**: The engine processes bars sequentially, emitting events (SignalEvent, OrderEvent, FillEvent) through a pub/sub model.

**ML Pipeline**: 116-feature engineering (lag, rolling, technical indicators, volume) → StandardScaler → RandomForest/GradientBoosting classifier.

### Configuration

Edit `config/settings.yaml` for:
- Database path
- Data provider settings (Yahoo, NSE, Alpha Vantage)
- Backtest defaults (capital, commission, slippage)
- Risk parameters
- ML settings

Pydantic settings class loads from this file automatically.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/strategies` | GET | List strategies |
| `/api/v1/backtests/run` | POST | Run backtest |
| `/api/v1/backtests/compare` | POST | Compare strategies |
| `/api/v1/optimization/grid` | POST | Grid search |
| `/api/v1/optimization/random` | POST | Random search |
| `/api/v1/optimization/genetic` | POST | Genetic algorithm |
| `/api/v1/walkforward/run` | POST | Walk-forward analysis |
| `/api/v1/ml/train` | POST | Train ML model |
| `/api/v1/data/ingest` | POST | Fetch and store OHLCV |

Full API docs at `http://localhost:8000/docs` when running.

### Frontend State Management

Uses Zustand for global state:
- `useBacktestStore` - Backtest results, trades, metrics
- `useStrategyStore` - Available strategies, selected strategy
- State persisted in `frontend/src/store/`

### Testing Architecture

- **Unit tests** (`tests/unit/`) - Domain entities, strategies, engine components
- **Integration tests** (`tests/integration/`) - Full backtest workflow, database, API
- **Property-based tests** (`tests/unit/test_properties.py`) - Hypothesis tests for invariants
- **Performance tests** (`tests/performance/`) - Benchmarks for large datasets

Key test fixtures in `tests/conftest.py` provide sample OHLCV data, strategy instances.

### Available Strategies

Built-in strategies in `src/strategies/`:
- `ema_crossover`, `rsi_mean_reversion`, `macd`, `ma_ribbon`, `triple_ma`
- `breakout`, `volume_breakout`, `volume_profile`
- `bollinger_bands`, `bbands`
- `ml_random_forest`, `ml_gradient_boosting`

### Database

SQLite with SQLAlchemy ORM. Models in `src/infrastructure/database/models/`:
- `OHLCVModel` - Price data
- `BacktestModel` - Backtest runs
- `TradeModel` - Individual trades
- `SignalModel` - Generated signals
- `OptimizationRun` - Optimization results

### Important Implementation Details

1. **PYTHONPATH** must include `.` when running CLI or tests from project root
2. **Strategy parameters** validated via Pydantic-like Parameter class with min/max bounds
3. **Commission/slippage** modeled in backtest engine - configurable per backtest
4. **Walk-forward** uses 252-day train / 63-day test windows by default
5. **ML models** saved to `data/models/` with joblib
