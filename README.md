# Trading Strategy Research Lab (TSRL)

AI-Powered Quantitative Trading Platform for strategy research, backtesting, optimization, and machine learning-based signal generation.

## Features

### Trading & Analysis
- **12 Trading Strategies** — EMA Crossover, RSI Mean Reversion, MACD, Bollinger Bands, Volume Profile, MA Ribbon, Triple MA, Breakout, Volume Breakout, BBands, and ML-based strategies
- **Dual Backtesting Engines** — Event-driven (realistic order fills) & Vectorized (fast execution)
- **Risk Analytics** — 50+ metrics including Sharpe, Sortino, Max Drawdown, Calmar, Kelly Criterion, VaR, CVaR, Omega Ratio, Ulcer Index, Tail Ratio
- **Portfolio Backtesting** — Multi-asset portfolios with rebalancing, benchmarking against SPY/VTI

### Fundamental Analysis
- **5 Financial Pillars** — Valuation, Profitability, Liquidity, Solvency, Cash Flow
- **Health Score (0-100)** — Composite score with Piotroski F-Score & Altman Z-Score
- **News & Sentiment** — AI-powered sentiment analysis with Finnhub + Alpha Vantage
- **Insider Tracking** — Multi-source insider transactions (Finnhub → Alpha Vantage → SEC EDGAR)
- **EPS Surprise History** — Quarterly earnings beats/misses visualization
- **Company Comparison** — Side-by-side comparison of up to 5 stocks

### Optimization & Validation
- **Strategy Optimization** — Grid Search (exhaustive), Random Search, Genetic Algorithm
- **Walk-Forward Analysis** — Rolling & expanding window validation to detect overfitting
- **Parameter Sensitivity** — Visual heatmaps showing parameter impact on performance

### Machine Learning
- **Feature Engineering** — 116 features (lags, rolling stats, technical indicators, volume metrics)
- **ML Strategies** — Random Forest & Gradient Boosting classifiers
- **Signal Generation** — ML-based buy/sell recommendations

### Data & API
- **Multi-Source Data** — Yahoo Finance, NSE (India), Alpha Vantage, Finnhub, SEC EDGAR
- **REST API** — 20+ endpoints for backtesting, optimization, walk-forward, ML training, fundamentals
- **Caching** — Environment-aware caching (dev: 1hr TTL, prod: no cache)
- **Force Refresh** — Manual cache invalidation per stock
- **Database** — SQLite with SQLAlchemy ORM + Alembic migrations

### Frontend Dashboard
- **6 Analysis Pages** — Backtest, Compare, Portfolio, Optimization, Walk-Forward, Fundamentals
- **Interactive Charts** — Equity curves, drawdown charts, monthly returns heatmaps, parameter sensitivity, radar charts, EPS surprise bars
- **Data Source Selector** — Toggle between Yahoo Finance and Alpha Vantage
- **Theme Support** — Light/Dark mode
- **Form Validation** — React Hook Form + Zod schemas
- **Force Refresh Button** — Clear cache and fetch fresh data
- **Cache Banner** — Warning when showing cached data

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (optional, for caching)

### Backend Setup

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

The API will be available at `http://localhost:8000` (docs at `/docs`)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Usage

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -q

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run specific test phases
python -m pytest tests/unit/domain/ -v       # Domain entities
python -m pytest tests/unit/strategies/ -v   # Strategy logic
python -m pytest tests/integration/ -v        # Integration tests
python -m pytest tests/unit/test_properties.py -v  # Property-based tests
python -m pytest tests/performance/ -v        # Performance benchmarks
```

### CLI Commands

```bash
# Run a backtest
PYTHONPATH=. python -m src.cli backtest --strategy ema_crossover --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01

# List available strategies
PYTHONPATH=. python -m src.cli strategies

# Optimize parameters (grid/random/genetic)
PYTHONPATH=. python -m src.cli optimize --strategy ema_crossover --symbol AAPL --method grid

# Run walk-forward analysis
PYTHONPATH=. python -m src.cli walkforward --strategy ema_crossover --symbol AAPL

# Fetch OHLCV data
PYTHONPATH=. python -m src.cli fetch-data --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01
```

### API Examples

```bash
# Run a backtest
curl -X POST http://localhost:8000/api/v1/backtests/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ema_crossover",
    "symbol": "AAPL",
    "start_date": "2020-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000,
    "source": "yahoo"
  }'

# Compare strategies
curl -X POST http://localhost:8000/api/v1/backtests/compare \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_names": ["ema_crossover", "macd", "bollinger_bands"],
    "symbol": "AAPL",
    "start_date": "2020-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000
  }'

# Grid search optimization
curl -X POST http://localhost:8000/api/v1/optimization/grid \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ema_crossover",
    "symbol": "AAPL",
    "start_date": "2020-01-01",
    "end_date": "2024-01-01",
    "param_grid": {"fast_period": [10, 20], "slow_period": [50, 100]},
    "metric": "sharpe_ratio",
    "initial_capital": 100000
  }'

# Walk-forward analysis
curl -X POST http://localhost:8000/api/v1/walkforward/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ema_crossover",
    "symbol": "AAPL",
    "start_date": "2020-01-01",
    "end_date": "2024-01-01",
    "param_grid": {"fast_period": [10, 20], "slow_period": [50, 100]},
    "train_days": 252,
    "test_days": 63,
    "initial_capital": 100000
  }'

# Fundamental Analysis - Full Report
curl "http://localhost:8000/api/v1/fundamentals/AAPL?source=yfinance&use_cache=true"

# Fundamental Analysis - News & Sentiment Only
curl "http://localhost:8000/api/v1/fundamentals/AAPL/news"

# Fundamental Analysis - Insider Transactions
curl "http://localhost:8000/api/v1/fundamentals/AAPL/insiders"

# Compare Multiple Stocks
curl "http://localhost:8000/api/v1/fundamentals/compare?symbols=AAPL,MSFT,GOOGL&source=yfinance"
```

## Available Strategies

| Strategy | Type | Description |
|----------|------|-------------|
| `ema_crossover` | Momentum | EMA crossover signals (fast/slow) |
| `rsi_mean_reversion` | Mean Reversion | RSI oversold/overbought levels |
| `macd` | Momentum | MACD crossover signals |
| `ma_ribbon` | Momentum | Multiple moving average ribbon |
| `triple_ma` | Momentum | Triple moving average crossover |
| `breakout` | Breakout | Price breakout above/below recent high/low |
| `volume_breakout` | Volume | Volume surge breakout |
| `volume_profile` | Volume | Volume-based support/resistance levels |
| `bollinger_bands` | Mean Reversion | Bollinger Bands bounce strategy |
| `bbands` | Breakout | Bollinger Bands breakout |
| `ml_random_forest` | ML | Random Forest classifier signals |
| `ml_gradient_boosting` | ML | Gradient Boosting classifier signals |

## API Endpoints

### Core
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/strategies` | List all available strategies |
| GET | `/api/v1/strategies/{name}` | Get strategy details & parameters |

### Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/data/ingest` | Fetch and store OHLCV data |

### Backtesting
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/backtests/run` | Run a single backtest |
| POST | `/api/v1/backtests/compare` | Compare multiple strategies |
| POST | `/api/v1/backtests/portfolio` | Run portfolio backtest |

### Optimization
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/optimization/grid` | Grid search optimization |
| POST | `/api/v1/optimization/random` | Random search optimization |
| POST | `/api/v1/optimization/genetic` | Genetic algorithm optimization |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/walkforward/run` | Walk-forward analysis |
| POST | `/api/v1/ml/train` | Train ML model |

### Fundamental Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/fundamentals/{symbol}` | Full fundamental analysis (5 pillars + health score) |
| GET | `/api/v1/fundamentals/{symbol}/news` | News and sentiment only |
| GET | `/api/v1/fundamentals/{symbol}/insiders` | Insider transactions |
| GET | `/api/v1/fundamentals/compare` | Compare multiple stocks |

## Frontend Pages

### 1. Backtest Page
- Strategy selection with parameter editor
- Equity curve, drawdown, and monthly returns charts
- Detailed metrics (Sharpe, Sortino, Max Drawdown, Win Rate, etc.)
- Trade history table

### 2. Compare Page
- Compare multiple strategies side-by-side
- Multi-line equity curve overlay
- Strategy ranking table

### 3. Portfolio Page
- Multi-asset portfolio backtesting
- Custom weights or equal weighting
- Rebalancing options (threshold-based, periodic)
- Benchmark comparison (SPY, VTI)

### 4. Optimization Page
- Parameter grid configuration
- Grid/Random/Genetic optimization methods
- Parameter sensitivity scatter plots
- Best parameters highlighted

### 5. Walk-Forward Page
- Train/test window configuration
- Rolling & expanding window analysis
- Stability score calculation
- Per-window results table

### 6. Fundamentals Page
- **5 Tabs**: Overview, Financials, Ratios, News & Sentiment, Insiders
- Health Score Gauge (0-100) with Piotroski F-Score & Altman Z-Score
- Financial Trends Chart (Revenue, Net Income, FCF over 5 years)
- EPS Surprise History (quarterly beats/misses)
- Radar Score Chart (5-pillar breakdown)
- Insider Tracker (monthly buy/sell visualization)
- News Feed with sentiment badges
- Force Refresh button + Cache banner
- Multi-stock comparison mode (up to 5 stocks)

## Project Structure

```
TSRL/
├── config/                     # Configuration (YAML + Pydantic)
│   ├── settings.yaml
│   └── .env                   # API keys (Alpha Vantage, Finnhub)
│
├── src/                       # Backend
│   ├── domain/               # Core business entities
│   │   ├── entities/        # OHLCV, Signal, Trade, Position, Metrics, Fundamental
│   │   └── value_objects/   # Symbol, Timeframe
│   │
│   ├── application/          # Service layer
│   │   └── services/        # BacktestService, DataService, FundamentalService
│   │
│   ├── infrastructure/       # External integrations
│   │   ├── database/       # SQLAlchemy ORM, Alembic migrations
│   │   │   ├── models/     # ORM models
│   │   │   └── repositories/
│   │   └── data_providers/  # Yahoo, NSE, Alpha Vantage, Finnhub, Insider, Fundamental Cache
│   │
│   ├── strategies/           # Plugin-based strategy system
│   │   ├── registry.py      # Strategy auto-discovery
│   │   ├── base.py          # BaseStrategy abstract class
│   │   ├── momentum/        # EMA, MACD, MA Ribbon, Triple MA
│   │   ├── mean_reversion/ # RSI, Bollinger Bands
│   │   ├── breakout/        # Price breakout strategies
│   │   ├── volume/          # Volume-based strategies
│   │   └── ml/             # ML Random Forest, Gradient Boosting
│   │
│   ├── engine/              # Execution engines
│   │   ├── backtest/       # Event-driven & vectorized engines
│   │   ├── optimizer/      # Grid, Random, Genetic optimizers
│   │   └── walkforward/   # Walk-forward validation
│   │
│   ├── ml/                 # Machine Learning
│   │   ├── feature_engineering/  # 116-feature pipeline
│   │   └── strategies/     # ML strategy implementations
│   │
│   ├── analytics/          # Risk metrics calculator (50+ metrics)
│   │
│   ├── main.py             # FastAPI application
│   └── cli.py             # CLI tool
│
├── frontend/               # React + Vite + TypeScript
│   ├── src/
│   │   ├── pages/         # 6 main pages
│   │   │   ├── BacktestPage.tsx
│   │   │   ├── ComparisonPage.tsx
│   │   │   ├── PortfolioPage.tsx
│   │   │   ├── OptimizationPage.tsx
│   │   │   ├── WalkForwardPage.tsx
│   │   │   └── FundamentalsPage.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── charts/    # EquityCurve, Drawdown, Heatmap, Sensitivity, Radar, EPS, Financial
│   │   │   ├── fundamentals/  # HealthScoreGauge, InsiderTracker, QualityScores, NewsCard
│   │   │   ├── forms/     # ParameterEditor, DataSourceSelector
│   │   │   ├── layout/   # AppLayout, Header
│   │   │   └── ui/       # MetricCard, ThemeToggle, Skeleton, etc.
│   │   │
│   │   ├── hooks/         # React Query hooks (apiHooks.ts)
│   │   ├── lib/          # API client, constants, schemas, utils
│   │   ├── store/        # Zustand stores
│   │   └── styles/       # CSS (theme, colors)
│   │
│   └── package.json
│
├── tests/                 # Test suite (547 tests, 89% coverage)
│   ├── unit/            # Domain, strategies, engine, ML
│   ├── integration/     # Workflow, database, portfolio
│   └── performance/     # Scalability benchmarks
│
├── notebooks/            # Jupyter research notebooks
├── alembic/             # Database migrations
└── data/               # SQLite DB, cache, models
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

data:
  providers:
    yahoo:
      enabled: true
    alpha_vantage:
      enabled: true
      api_key: "${ALPHA_VANTAGE_API_KEY}"
```

Edit `config/.env` for API keys:

```bash
# API Keys
ALPHA_VANTAGE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# Environment (development/production)
ENVIRONMENT=development

# SEC EDGAR (for insider fallback)
SEC_EDGAR_USER_AGENT=YourName email@example.com
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, Pydantic |
| Database | SQLite, SQLAlchemy, Alembic |
| Data | Pandas, NumPy, yfinance |
| ML | scikit-learn, XGBoost |
| Testing | pytest, Hypothesis, pytest-cov |
| Frontend | React 19, Vite, TypeScript |
| State | Zustand |
| Charts | Recharts |
| Forms | React Hook Form, Zod |
| API Client | TanStack Query, Axios |

## Testing

- **547 tests** across 6 phases:
  - Domain Layer (172 tests)
  - Strategies (107 tests)
  - Engine & ML (104 tests)
  - Integration (50 tests)
  - Property-based (21 tests)
  - Performance (10 tests)
- **89% code coverage**

## What's Next? (Roadmap)

Potential enhancements to consider:

### High Priority
- [x] **Fundamental Analysis** — Complete fundamental analysis with 5 pillars + health score ✅
- [ ] **Backtest Persistence** — Save/load backtest results from database
- [ ] **Real-time Data** — WebSocket for live price feeds
- [ ] **Paper Trading** — Simulated trading with real-time data
- [ ] **Export Results** — PDF/CSV export for reports

### Medium Priority
- [ ] **Live Trading** — Connect to broker APIs (Alpaca, Interactive Brokers)
- [ ] **Options Strategies** — Options pricing and Greeks
- [ ] **Crypto Support** — Binance, Coinbase APIs
- [ ] **Portfolio Optimization** — Mean-variance, risk-parity
- [ ] **Email Alerts** — Notifications on signals/trades

### Lower Priority
- [ ] **User Authentication** — Multi-user support
- [ ] **Cloud Deployment** — Docker, Kubernetes configs
- [ ] **Strategy Marketplace** — Share strategies
- [ ] **Backtest Benchmarking** — Compare against SPY/BTC benchmarks

---

## ⚠️ Personal Project

**This is a personal project** built for learning and experimentation. While it's a private repository, please **do not copy or replicate** this work for your own projects.
