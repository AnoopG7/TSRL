# Trading Strategy Research Lab

AI-Powered Trading Strategy Research Platform for quantitative trading analysis, backtesting, and machine learning-based signal generation.

## Features

- **12 Trading Strategies** — EMA Crossover, RSI, MACD, Bollinger Bands, Volume Profile, MA Ribbon, and ML-based strategies
- **Backtesting Engine** — Event-driven & vectorized engines with commission, slippage, stop-loss, and take-profit support
- **Risk Analytics** — Sharpe, Sortino, Max Drawdown, Calmar, Kelly Criterion, VaR, CVaR, Omega Ratio, and more
- **Strategy Optimization** — Grid Search, Random Search, and Genetic Algorithm optimizers
- **Walk-Forward Analysis** — Rolling and expanding window validation to detect overfitting
- **Machine Learning** — 116-feature engineering pipeline with Random Forest and Gradient Boosting classifiers
- **REST API** — FastAPI backend with 12 endpoints (backtesting, optimization, walk-forward, ML)
- **Modern Dashboard** — React + TypeScript frontend with equity curves, drawdown charts, and monthly returns heatmaps
- **486 Tests, 89% Coverage** — Unit, integration, property-based, and performance tests

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)

### Backend

```bash
# Clone and enter the project
git clone https://github.com/AnoopG7/TSRL.git
cd TSRL

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run the API server
PYTHONPATH=. python src/main.py
```

The API will be available at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`

### Running Tests

```bash
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -q

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run specific test phase
python -m pytest tests/unit/domain/ -v          # Domain entities
python -m pytest tests/unit/strategies/ -v       # Strategy logic
python -m pytest tests/integration/ -v           # Integration tests
python -m pytest tests/unit/test_properties.py   # Property-based tests
python -m pytest tests/performance/ -v           # Performance benchmarks
```

## Usage

### CLI

```bash
source .venv/bin/activate

# Run a backtest
PYTHONPATH=. python -m src.cli backtest --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01

# Run with a specific strategy
PYTHONPATH=. python -m src.cli backtest --strategy macd --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01

# List available strategies
PYTHONPATH=. python -m src.cli strategies

# Optimize strategy parameters
PYTHONPATH=. python -m src.cli optimize --strategy ema_crossover --symbol AAPL --start-date 2022-01-01 --end-date 2024-01-01 --method grid

# Run walk-forward analysis
PYTHONPATH=. python -m src.cli walkforward --strategy ema_crossover --symbol AAPL --start-date 2020-01-01 --end-date 2024-12-31

# Fetch OHLCV data
PYTHONPATH=. python -m src.cli fetch-data --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01
```

### API

```bash
# Run a backtest
curl -X POST http://localhost:8000/api/v1/backtests/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ema_crossover",
    "symbol": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000
  }'

# Compare strategies
curl -X POST http://localhost:8000/api/v1/backtests/compare \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_names": ["ema_crossover", "macd", "bollinger_bands"],
    "symbol": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01"
  }'
```

## Available Strategies

| Strategy | Type | Description |
|----------|------|-------------|
| `ema_crossover` | Momentum | EMA crossover signals |
| `rsi_mean_reversion` | Mean Reversion | RSI oversold/overbought |
| `macd` | Momentum | MACD crossover signals |
| `ma_ribbon` | Momentum | Multiple moving average ribbon |
| `triple_ma` | Momentum | Triple moving average crossover |
| `volume_profile` | Volume | Volume-based support/resistance |
| `volume_breakout` | Volume | Volume surge breakout |
| `bollinger_bands` | Mean Reversion | Bollinger Bands bounce |
| `bollinger_breakout` | Breakout | Bollinger Bands breakout |
| `ml_random_forest` | ML | Random Forest classifier |
| `ml_gradient_boosting` | ML | Gradient Boosting classifier |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/strategies` | List all strategies |
| GET | `/api/v1/strategies/{name}` | Get strategy details |
| GET | `/api/v1/backtests` | List past backtests |
| POST | `/api/v1/data/ingest` | Fetch and store OHLCV data |
| POST | `/api/v1/backtests/run` | Run a backtest |
| POST | `/api/v1/backtests/compare` | Compare multiple strategies |
| POST | `/api/v1/optimization/grid` | Grid search optimization |
| POST | `/api/v1/optimization/random` | Random search optimization |
| POST | `/api/v1/optimization/genetic` | Genetic algorithm optimization |
| POST | `/api/v1/walkforward/run` | Walk-forward analysis |
| POST | `/api/v1/ml/train` | Train ML model and backtest |

## Project Structure

```
TSRL/
├── config/                     # Configuration (YAML + Pydantic)
├── src/
│   ├── domain/                 # Core business entities
│   │   ├── entities/           # OHLCV, Signal, Trade, Position, Metrics
│   │   └── value_objects/      # Symbol, Timeframe
│   ├── application/            # Service layer
│   │   └── services/           # BacktestService, DataService
│   ├── infrastructure/         # External integrations
│   │   ├── database/           # SQLAlchemy ORM, repositories
│   │   └── data_providers/     # Yahoo Finance, NSE, caching
│   ├── strategies/             # Plugin-based strategy system
│   │   ├── momentum/           # EMA, RSI, MACD, MA Ribbon
│   │   └── mean_reversion/     # Bollinger Bands
│   ├── engine/                 # Execution engines
│   │   ├── backtest/           # Event-driven + vectorized engines
│   │   ├── optimizer/          # Grid, Random, Genetic optimizers
│   │   └── walkforward/        # Walk-forward validation
│   ├── ml/                     # Machine Learning
│   │   ├── feature_engineering/# 116-feature pipeline
│   │   └── strategies/         # RF, GBM strategies
│   ├── analytics/              # Risk metrics calculator
│   ├── main.py                 # FastAPI application
│   └── cli.py                  # CLI tool
├── frontend/                   # React + Vite + TypeScript
│   └── src/
│       ├── pages/              # BacktestPage, ComparisonPage
│       ├── components/         # Charts, UI components
│       └── store/              # Zustand state management
├── notebooks/                  # Jupyter research notebooks
│   ├── 01_data_exploration     # Data fetching, distributions, volatility
│   ├── 02_strategy_backtest    # Strategy comparison, equity curves
│   └── 03_optimization         # Grid search, heatmaps, walk-forward
├── tests/                      # Test suites (486 tests, 89% coverage)
│   ├── unit/                   # Domain, strategy, engine, ML tests
│   ├── integration/            # Workflow, database, portfolio tests
│   └── performance/            # Scalability benchmarks
├── alembic/                    # Database migrations
└── data/                       # SQLite DB, cache, models
```

## Configuration

Edit `config/settings.yaml`:

```yaml
database:
  path: "data/trading_lab.db"

backtest:
  default_capital: 100000.0
  default_commission: 0.001
  default_slippage: 0.0005

api:
  host: "0.0.0.0"
  port: 8000
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI |
| Database | SQLite, SQLAlchemy, Alembic |
| Data | Pandas, NumPy, yfinance |
| ML | scikit-learn, XGBoost |
| Testing | pytest, Hypothesis, pytest-cov |
| Frontend | React, Vite, TypeScript, Tailwind CSS |

## License

MIT
