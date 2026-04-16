# Trading Strategy Research Lab

AI-Powered Trading Strategy Research Platform for quantitative trading analysis, backtesting, and machine learning-based signal generation.

## Features

- **12 Trading Strategies** — EMA Crossover, RSI, MACD, Bollinger Bands, Volume Profile, MA Ribbon, and ML-based strategies
- **Backtesting Engine** — Event-driven & vectorized engines with commission, slippage, stop-loss, and take-profit support
- **Fundamental Analysis** — 5-pillar health scoring, Piotroski F-Score, Altman Z-Score, EPS surprise, insider tracking, news sentiment
- **Risk Analytics** — Sharpe, Sortino, Max Drawdown, Calmar, Kelly Criterion, VaR, CVaR, Omega Ratio, and more
- **Strategy Optimization** — Grid Search, Random Search, and Genetic Algorithm optimizers
- **Walk-Forward Analysis** — Rolling and expanding window validation to detect overfitting
- **Machine Learning** — 116-feature engineering pipeline with Random Forest and Gradient Boosting classifiers
- **REST API** — FastAPI backend with 16 endpoints (backtesting, optimization, walk-forward, ML, fundamentals)
- **Modern Dashboard** — React + TypeScript frontend with equity curves, drawdown charts, monthly returns heatmaps, and a full fundamental analysis dashboard
- **643 Tests** — Unit, integration, property-based, and performance tests across trading engine, ML, and fundamentals

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

### Environment Variables

Create `config/.env` with the following keys (all optional for basic backtesting):

```bash
# Required for Fundamental Analysis
FINNHUB_API_KEY=your_key          # News, EPS surprise, insider data (free: 60 calls/min)
ALPHA_VANTAGE_API_KEY=your_key    # Sentiment scoring (free: 500 calls/day)
SEC_EDGAR_USER_AGENT="YourApp/1.0 your@email.com"  # SEC EDGAR insider data

# Optional — paid data providers
FMP_API_KEY=your_key              # Financial Modeling Prep (production-grade fundamentals)
```

### Running Tests

```bash
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -q

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run specific test suites
python -m pytest tests/unit/domain/ -v             # Domain entities
python -m pytest tests/unit/strategies/ -v          # Strategy logic
python -m pytest tests/unit/fundamentals/ -v        # Fundamental analysis
python -m pytest tests/integration/ -v              # Integration tests
python -m pytest tests/unit/test_properties.py      # Property-based tests
python -m pytest tests/performance/ -v              # Performance benchmarks
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
| `breakout` | Breakout | Price breakout above/below recent high/low |
| `macd` | Momentum | MACD crossover signals |
| `ma_ribbon` | Momentum | Multiple moving average ribbon |
| `triple_ma` | Momentum | Triple moving average crossover |
| `volume_profile` | Volume | Volume-based support/resistance |
| `volume_breakout` | Volume | Volume surge breakout |
| `bollinger_bands` | Mean Reversion | Bollinger Bands bounce |
| `bbands` | Breakout | Bollinger Bands breakout |
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
| POST | `/api/v1/backtests/portfolio` | Portfolio-level backtest |
| POST | `/api/v1/optimization/grid` | Grid search optimization |
| POST | `/api/v1/optimization/random` | Random search optimization |
| POST | `/api/v1/optimization/genetic` | Genetic algorithm optimization |
| POST | `/api/v1/walkforward/run` | Walk-forward analysis |
| POST | `/api/v1/ml/train` | Train ML model and backtest |
| GET | `/api/v1/fundamentals/{symbol}` | Full fundamental analysis |
| GET | `/api/v1/fundamentals/{symbol}/news` | News & sentiment (lightweight) |
| GET | `/api/v1/fundamentals/{symbol}/insiders` | SEC Form 4 insider trading |
| GET | `/api/v1/fundamentals/compare` | Multi-stock comparison |

## Project Structure

```
TSRL/
├── config/                     # Configuration (YAML + Pydantic + .env)
├── src/
│   ├── domain/                 # Core business entities
│   │   ├── entities/           # OHLCV, Signal, Trade, Position, Metrics, FundamentalReport
│   │   └── value_objects/      # Symbol, Timeframe
│   ├── application/            # Service layer
│   │   └── services/           # BacktestService, DataService, FundamentalService
│   ├── infrastructure/         # External integrations
│   │   ├── database/           # SQLAlchemy ORM, repositories
│   │   └── data_providers/     # Yahoo Finance, FMP, Finnhub, Alpha Vantage, SEC EDGAR
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
│       ├── pages/              # BacktestPage, ComparisonPage, FundamentalsPage
│       ├── components/
│       │   ├── charts/         # FinancialTrends, EpsSurprise, RadarScore
│       │   ├── fundamentals/   # HealthScoreGauge, RatioTable, InsiderTracker, etc.
│       │   └── ui/             # MetricCard, shared components
│       └── store/              # Zustand state management
├── notebooks/                  # Jupyter research notebooks
│   ├── 01_data_exploration     # Data fetching, distributions, volatility
│   ├── 02_strategy_backtest    # Strategy comparison, equity curves
│   └── 03_optimization         # Grid search, heatmaps, walk-forward
├── tests/                      
│   ├── unit/
│   │   ├── domain/             # Entity validation (6 files)
│   │   ├── strategies/         # Strategy logic (4 files)
│   │   ├── engine/             # Backtest, optimizer, walk-forward (3 files)
│   │   ├── fundamentals/       # Health score, Piotroski, Altman Z, cache, providers (8 files)
│   │   ├── analytics/          # Risk and portfolio metrics (2 files)
│   │   ├── ml/                 # Feature engineering, ML strategies (2 files)
│   │   ├── api/                # API endpoint tests (1 file)
│   │   ├── cli/                # CLI command tests (1 file)
│   │   └── test_properties.py  # Hypothesis property-based tests
│   ├── integration/            # Workflow, database, portfolio, fundamentals API (5 files)
│   └── performance/            # Scalability benchmarks (1 file)
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
| Frontend | React, Vite, TypeScript, Recharts |

## License

MIT
