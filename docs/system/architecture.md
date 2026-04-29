# System Architecture

## Core Pipeline
```
Data → Strategy → Risk → Execution → Portfolio → Metrics
```

## Module Mapping

### Domain Layer (src/domain/)
- **Entities**: `OHLCV`, `Signal`, `Trade`, `Position`, `RiskMetrics`, `PortfolioMetrics`, `FundamentalReport`, `RebalanceEvent`
- **Value Objects**: `Symbol`, `Timeframe`
- **Location**: `src/domain/entities/`, `src/domain/value_objects/`

### Application Services (src/application/services/)
- **BacktestService**: Orchestrates backtesting workflow (data → strategy → engine → persistence)
- **DataService**: Handles data fetching, caching, provider selection
- **FundamentalService**: Computes ratios, CAGR, health scores from fundamentals
- **Location**: `src/application/services/`

### Infrastructure Layer (src/infrastructure/)
- **Data Providers**: `YahooProvider`, `NSEProvider`, `AlphaVantageProvider`, `FundamentalProvider`, `NewsProvider`, `InsiderProvider`
- **Database**: SQLAlchemy ORM, repositories (OHLCVRepository, BacktestRepository)
- **Logging**: `src/infrastructure/logging/setup.py`
- **Location**: `src/infrastructure/data_providers/`, `src/infrastructure/database/`

### Execution Layer (src/engine/)
- **BacktestEngine**: Event-driven single-symbol backtesting (`src/engine/backtest/engine.py`)
- **PortfolioEngine**: Multi-symbol portfolio backtesting (`src/engine/backtest/portfolio_engine.py`)
- **AdvancedEngine**: Vectorized backtesting with optimizations
- **Optimizer**: Grid Search, Random Search, Genetic Algorithm (`src/engine/optimizer/`)
- **WalkForward**: Rolling/expanding window validation (`src/engine/walkforward/`)
- **Location**: `src/engine/backtest/`, `src/engine/optimizer/`, `src/engine/walkforward/`

### Strategy Layer (src/strategies/)
- **Registry**: Auto-discovery via decorator pattern (`src/strategies/registry.py`)
- **Momentum**: EMA Crossover, MACD, MA Ribbon, Volume Strategies
- **Mean Reversion**: Bollinger Bands
- **Breakout**: Breakout, Volume Breakout
- **ML**: Random Forest, Gradient Boosting classifiers
- **Location**: `src/strategies/momentum/`, `src/strategies/mean_reversion/`, `src/strategies/breakout/`, `src/strategies/ml/`

### Analytics Layer (src/analytics/)
- **RiskMetrics**: Sharpe, Sortino, VaR, CVaR, Max Drawdown, Calmar, Kelly, etc.
- **PortfolioMetrics**: Correlation matrix, risk contribution, benchmark comparison
- **Location**: `src/analytics/`

### ML Layer (src/ml/)
- **Feature Engineering**: 116 features (lag, rolling, technical indicators, volume)
- **ML Strategies**: RandomForest, GradientBoosting classifiers
- **Location**: `src/ml/feature_engineering/`, `src/ml/strategies/`

### Presentation Layer
- **API**: FastAPI (`src/main.py`) - 16+ endpoints
- **CLI**: Click CLI (`src/cli.py`)
- **Frontend**: React 19 + TypeScript + Vite + Zustand + Recharts

## Data Flow
```
1. DataProvider.fetch() → OHLCV[]
2. OHLCV → Strategy.generate_signals() → Signal[]
3. Signal[] → BacktestEngine.run() → Trade[]
4. Trade[] → PortfolioEngine → Position[]
5. Trades/Positions → RiskMetrics.calculate() → Metrics
6. Metrics → API Response → Frontend
```

## Caching Layers
1. `src/infrastructure/data_providers/cache.py` (OHLCV data)
2. `src/infrastructure/data_providers/fundamental_cache.py` (fundamentals)