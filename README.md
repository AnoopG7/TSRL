# Trading Strategy Research Lab

AI-Powered Trading Strategy Research Platform for quantitative trading research.

## Features

- **Data Ingestion** - Fetch OHLCV data from Yahoo Finance & NSE India
- **Strategy Engine** - Plugin-based strategy system with built-in strategies
- **Backtesting** - Event-driven & vectorized backtesting with commission/slippage modeling
- **Risk Analytics** - Comprehensive risk metrics (Sharpe, Sortino, Drawdown, etc.)
- **REST API** - FastAPI-based API for all operations
- **Modern UI** - React + Tailwind + Shadcn dashboard

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+

### Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
PYTHONPATH=. python src/main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Usage

### Running a Backtest

```bash
# Using the CLI
source venv/bin/activate
PYTHONPATH=. python -m src.cli backtest --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01

# Or via API
curl -X POST http://localhost:8000/api/v1/backtests/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ema_crossover",
    "symbol": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000
  }'
```

### Available Strategies

| Strategy | Type | Description |
|----------|------|-------------|
| `ema_crossover` | Momentum | EMA crossover signals |
| `rsi_mean_reversion` | Mean Reversion | RSI oversold/overbought |
| `breakout` | Breakout | Price breakout from highs/lows |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root info |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/strategies` | List strategies |
| GET | `/api/v1/strategies/{name}` | Strategy details |
| POST | `/api/v1/data/ingest` | Fetch OHLCV data |
| POST | `/api/v1/backtests/run` | Run backtest |

## Project Structure

```
trading_research_lab/
├── config/                    # Configuration (YAML + Pydantic)
├── src/
│   ├── domain/               # Business entities
│   │   ├── entities/        # OHLCV, Signal, Trade, Position, Metrics
│   │   └── value_objects/   # Symbol, Timeframe
│   ├── infrastructure/      # External implementations
│   │   ├── database/         # SQLAlchemy ORM
│   │   └── data_providers/  # Yahoo, NSE
│   ├── strategies/          # Trading strategies
│   │   └── momentum/        # EMA, RSI strategies
│   ├── engine/              # Execution engines
│   │   └── backtest/        # Backtesting engine
│   └── analytics/          # Risk metrics
├── frontend/                 # React + Vite + Tailwind
├── scripts/                 # Utility scripts
├── data/                    # Data storage
└── logs/                    # Log files
```

## Configuration

Edit `config/settings.yaml` to customize:

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

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Lint code
ruff check src/
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI |
| Database | SQLite, SQLAlchemy |
| Data | Pandas, NumPy, yfinance |
| ML | scikit-learn, XGBoost |
| Frontend | React, Vite, TypeScript |
| UI | Tailwind CSS, Shadcn UI |

## License

MIT
