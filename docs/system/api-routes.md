# API Routes

## Available Endpoints

### Health & Info
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root info - name, version, status |
| GET | `/api/v1/health` | Health check |

### Strategies
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/strategies` | List all available strategies |
| GET | `/api/v1/strategies/{strategy_name}` | Get strategy details (parameters, description) |

### Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/data/ingest` | Fetch and store OHLCV data |

### Backtests
| Method | Endpoint | Request | Description |
|--------|----------|---------|-------------|
| GET | `/api/v1/backtests` | `?limit=20` | List past backtests |
| POST | `/api/v1/backtests/run` | `BacktestRequest` | Run a single backtest |
| POST | `/api/v1/backtests/compare` | `CompareRequest` | Compare multiple strategies |
| POST | `/api/v1/backtests/portfolio` | `PortfolioBacktestRequest` | Portfolio-level backtest |

### Optimization
| Method | Endpoint | Request | Description |
|--------|----------|---------|-------------|
| POST | `/api/v1/optimization/grid` | `OptimizationRequest` | Grid search optimization |
| POST | `/api/v1/optimization/random` | `OptimizationRequest` | Random search optimization |
| POST | `/api/v1/optimization/genetic` | `OptimizationRequest` | Genetic algorithm optimization |

### Walk-Forward
| Method | Endpoint | Request | Description |
|--------|----------|---------|-------------|
| POST | `/api/v1/walkforward/run` | `WalkForwardRequest` | Walk-forward analysis |

### Machine Learning
| Method | Endpoint | Request | Description |
|--------|----------|---------|-------------|
| POST | `/api/v1/ml/train` | `MLTrainRequest` | Train ML model and backtest |

### Fundamentals
| Method | Endpoint | Query | Description |
|--------|----------|-------|-------------|
| GET | `/api/v1/fundamentals/{symbol}` | `?include_news=true&source=yahoo` | Full fundamental analysis |
| GET | `/api/v1/fundamentals/{symbol}/news` | | News & sentiment (lightweight) |
| GET | `/api/v1/fundamentals/{symbol}/insiders` | | SEC Form 4 insider trading |
| GET | `/api/v1/fundamentals/compare` | `?symbols=AAPL,MSFT` | Multi-stock comparison |

## Request Models

### BacktestRequest
```python
class BacktestRequest:
    strategy_name: str           # "ema_crossover", "macd", etc.
    symbol: str               # "AAPL", "RELIANCE", etc.
    start_date: str          # "2023-01-01"
    end_date: str          # "2024-01-01"
    timeframe: str = "1d"   # "1d", "1h", "1w"
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    parameters: Optional[dict] = None  # Strategy params override
    market: str = "us"      # "us", "india", "crypto"
```

### OptimizationRequest
```python
class OptimizationRequest:
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    param_grid: Dict[str, List]  # {"fast_period": [5, 10, 15], "slow_period": [20, 30, 40]}
    metric: str = "sharpe_ratio"  # Optimization metric
    n_iterations: int = 100
```

### WalkForwardRequest
```python
class WalkForwardRequest:
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    param_grid: Dict[str, List]
    train_days: int = 252       # Training window (1 year)
    test_days: int = 63        # Test window (quarter)
```

## Response Formats

### BacktestResponse
```python
class BacktestResponse:
    backtest_id: Optional[int]
    strategy: str
    symbol: str
    final_capital: float
    total_return: float
    total_trades: int
    metrics: dict  # Sharpe, Sortino, Drawdown, etc.
    execution_time_ms: float
    equity_curve: list
    drawdown_series: list
    monthly_returns: list
    trades: list
```

### FundamentalReport
```python
class FundamentalReport:
    symbol: str
    company_name: str
    sector: str
    industry: str
    market_cap: float
    current_price: float
    
    # Ratios
    pe_ratio: Optional[float]
    roe: Optional[float]
    # ... 50+ fields
    
    # Health Score
    health_score: Optional[float]
    health_grade: Optional[str]  # "A", "B", "C", "D", "F"
```

## CLI Commands (Alternative)

```bash
# Run backtest
PYTHONPATH=. python -m src.cli backtest --strategy ema_crossover --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01

# Optimize parameters
PYTHONPATH=. python -m src.cli optimize --strategy ema_crossover --symbol AAPL --method grid

# Walk-forward
PYTHONPATH=. python -m src.cli walkforward --strategy ema_crossover --symbol AAPL

# Fetch data
PYTHONPATH=. python -m src.cli fetch-data --symbol AAPL
```