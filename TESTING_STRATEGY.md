# TSRL Testing Strategy - Implementation Plan

> Last Updated: March 2026

---

## Overview

- **Test Framework**: pytest + pytest-cov + pytest-mock + hypothesis (property-based)
- **Test Structure**: tests/unit/, tests/integration/, tests/fixtures/
- **Target Coverage**: 80%+ (phased approach)
- **Test Files Location**: `/Users/anoop/Developer/Projects/TSRL/tests/`

---

## Phase 1: Unit Tests - Domain Layer (Week 1)

### Goal: Establish foundational testing for core business logic

### 1.1 Domain Entities

| File | Location | Test Coverage | Tests |
|------|----------|---------------|-------|
| `domain/entities/trade.py` | `tests/unit/domain/` | Trade, TradeSide, TradeStatus | pnl, pnl_pct, is_winning, is_closed calculations |
| `domain/entities/position.py` | `tests/unit/domain/` | Position, PositionSide | market_value, cost_basis, unrealized_pnl |
| `domain/entities/signal.py` | `tests/unit/domain/` | SignalType, SignalStrength | is_buy, is_sell, is_entry, is_exit |
| `domain/entities/ohlcv.py` | `tests/unit/domain/` | OHLCV entity | typical_price, range, is_bullish |
| `domain/entities/metrics.py` | `tests/unit/domain/` | RiskMetrics | is_profitable, risk_of_ruin, recovery_factor |
| `domain/value_objects/symbol.py` | `tests/unit/domain/` | Symbol, Timeframe | ticker conversion, minutes mapping |

### 1.2 Risk Metrics Calculator

Location: `tests/unit/analytics/test_risk_metrics.py`

| Function | Tests |
|----------|-------|
| `calculate_total_return` | Basic, edge cases (zero initial) |
| `calculate_cagr` | Edge cases (zero days, negative returns) |
| `calculate_sharpe_ratio` | Zero std, insufficient data |
| `calculate_sortino_ratio` | No downside returns |
| `calculate_max_drawdown` | Single point, full recovery |
| `calculate_win_rate` | No trades, all wins, all losses |
| `calculate_profit_factor` | No losses, no wins |
| `calculate_kelly_criterion` | Win rate edge cases |
| `calculate_var` | Different confidence levels |
| `calculate_cvar` | Tail risk |

### Phase 1 Deliverable
- **50+ unit tests**
- **Files to create**:
  - `tests/unit/domain/__init__.py`
  - `tests/unit/domain/test_trade.py`
  - `tests/unit/domain/test_position.py`
  - `tests/unit/domain/test_signal.py`
  - `tests/unit/domain/test_ohlcv.py`
  - `tests/unit/domain/test_metrics.py`
  - `tests/unit/domain/test_symbol.py`
  - `tests/unit/analytics/__init__.py`
  - `tests/unit/analytics/test_risk_metrics.py`
  - `tests/conftest.py` (shared fixtures)

---

## Phase 2: Unit Tests - Strategies (Week 2)

### Goal: Test all trading strategies

### 2.1 Strategy Base

Location: `tests/unit/strategies/`

| Class | Tests |
|-------|-------|
| `BaseStrategy` | Parameter get/set, validation, to_dict |
| `StrategyParameter` | Value bounds |
| `StrategyRegistry` | Register, get, list |

### 2.2 Strategy Signal Generation

| Strategy | Test File | Tests |
|---------|-----------|-------|
| `EMACrossoverStrategy` | `test_ema_crossover.py` | Bullish cross, bearish cross, no signal |
| `RSIMeanReversionStrategy` | `test_rsi.py` | Oversold, overbought, neutral |
| `MACDStrategy` | `test_macd.py` | Signal line crossover |
| `BollingerBandsStrategy` | `test_bollinger_bands.py` | Mean reversion signals |
| `VolumeBreakoutStrategy` | `test_volume.py` | Volume surge detection |
| `MARibbonStrategy` | `test_ma_ribbon.py` | Multiple MA crossovers |
| `TripleMA` | `test_triple_ma.py` | Three MA system |

### 2.3 Strategy Edge Cases
- Insufficient data
- Parameter boundary conditions
- NaN handling
- All strategies return valid signal range [-1, 0, 1]

### Phase 2 Deliverable
- **30+ strategy tests**
- **Files to create**:
  - `tests/unit/strategies/__init__.py`
  - `tests/unit/strategies/test_base.py`
  - `tests/unit/strategies/test_registry.py`
  - `tests/unit/strategies/test_ema_crossover.py`
  - `tests/unit/strategies/test_rsi.py`
  - `tests/unit/strategies/test_macd.py`
  - `tests/unit/strategies/test_bollinger_bands.py`
  - `tests/unit/strategies/test_volume.py`
  - `tests/unit/strategies/test_ma_ribbon.py`

---

## Phase 3: Unit Tests - Engine & ML (Week 3)

### Goal: Test execution engines and ML module

### 3.1 Backtest Engine

Location: `tests/unit/engine/`

| Component | Tests |
|-----------|-------|
| `BacktestConfig` | Default values, validation |
| `BacktestEngine.run()` | Basic execution, empty data |
| `_execute_signals()` | Long/short logic, commission |
| `_calculate_equity_curve()` | Returns calculation |

### 3.2 Optimizer

| Component | Tests |
|-----------|-------|
| `GridSearchOptimizer` | Parameter grid, results sorting |
| `RandomSearchOptimizer` | Sampling bounds |
| `GeneticAlgorithmOptimizer` | Selection, crossover, mutation |

### 3.3 Walk-Forward

| Component | Tests |
|-----------|-------|
| `WalkForwardAnalyzer` | Rolling windows, expanding windows |
| Stability calculation | OOS vs IS comparison |

### 3.4 ML Module

| Component | Tests |
|-----------|-------|
| `FeatureEngineer` | Feature generation, NaN handling |
| `MLRandomForestStrategy` | Signal generation, model fit |
| `MLGradientBoostingStrategy` | Signal generation |
| `FeatureSelector` | Correlation selection |

### Phase 3 Deliverable
- **40+ engine/ML tests**
- **Files to create**:
  - `tests/unit/engine/__init__.py`
  - `tests/unit/engine/test_backtest_engine.py`
  - `tests/unit/engine/test_optimizer.py`
  - `tests/unit/engine/test_walkforward.py`
  - `tests/unit/ml/__init__.py`
  - `tests/unit/ml/test_features.py`
  - `tests/unit/ml/test_ml_strategies.py`

---

## Phase 4: Integration Tests (Week 4)

### Goal: Test interactions between components

### 4.1 End-to-End Backtest

Location: `tests/integration/test_backtest_workflow.py`

```
test_full_backtest_workflow():
  1. Fetch/create sample data
  2. Initialize strategy
  3. Run backtest
  4. Verify metrics calculated
  5. Verify trade count
```

### 4.2 Data Provider Integration

| Test | Description |
|------|-------------|
| `test_yahoo_provider_fetch` | Real API call (mocked) |
| `test_cache_functionality` | Cache hit/miss |
| `test_provider_error_handling` | Retry logic |
| `test_alpha_vantage_provider` | Alternative provider |

### 4.3 Database Integration

| Test | Description |
|------|-------------|
| `test_save_backtest` | Save to SQLite |
| `test_load_backtest` | Retrieve and verify |
| `test_ohlcv_crud` | Create, read, update, delete |
| `test_trade_repository` | Trade persistence |

### 4.4 Service Layer

| Test | Description |
|------|-------------|
| `test_backtest_service_run` | BacktestService.run_backtest() end-to-end |
| `test_backtest_service_compare` | BacktestService.compare_strategies() |
| `test_data_service_fetch` | DataService.fetch_data() with mocked provider |
| `test_data_service_fallback` | DataService simulated data fallback |

### 4.5 API Integration

| Endpoint | Tests |
|----------|-------|
| `/api/v1/backtests/run` | Full round-trip |
| `/api/v1/backtests/compare` | Multi-strategy comparison |
| `/api/v1/strategies` | List strategies |
| `/api/v1/optimization/*` | Optimization endpoints |

### Phase 4 Deliverable
- **25+ integration tests**
- **Files to create**:
  - `tests/integration/__init__.py`
  - `tests/integration/test_backtest_workflow.py`
  - `tests/integration/test_data_providers.py`
  - `tests/integration/test_database.py`
  - `tests/integration/test_services.py`
  - `tests/integration/test_api.py`

---

## Phase 5: Property-Based Testing (Week 5)

### Goal: Use hypothesis for mathematical property testing

Using **hypothesis** for property-based testing:

| Area | Property | Test File |
|------|----------|-----------|
| Risk Metrics | Sharpe always finite | `test_properties.py` |
| Trade PnL | Symmetric for long/short | `test_properties.py` |
| Strategy Signals | Signals in [-1, 0, 1] | `test_properties.py` |
| Equity Curve | No NaN values | `test_properties.py` |
| Optimizer | Best result improves baseline | `test_properties.py` |

### Example Property Tests
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@given(st.lists(st.floats(min_value=-1, max_value=1)))
def test_sharpe_ratio_finite(returns):
    """Sharpe ratio should always be finite"""
    series = pd.Series(returns)
    result = calculate_sharpe_ratio(series)
    assert np.isfinite(result)
```

### Phase 5 Deliverable
- **20+ property-based tests**
- **Files to create**:
  - `tests/unit/test_properties.py`

---

## Phase 6: Performance & Stress Tests (Week 6)

### Goal: Ensure system handles load

Location: `tests/performance/`

| Test | Description |
|------|-------------|
| Large dataset backtest | 10K+ bars performance |
| Many trades | 1000+ trades handling |
| Concurrent optimization | Multi-process stability |
| Memory usage | No leaks on repeated runs |
| Feature engineering speed | 100+ features generation time |

### Phase 6 Deliverable
- **10+ performance tests**
- **Files to create**:
  - `tests/performance/__init__.py`
  - `tests/performance/test_scalability.py`

---

## Test File Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── test_trade.py
│   │   ├── test_position.py
│   │   ├── test_signal.py
│   │   ├── test_ohlcv.py
│   │   ├── test_metrics.py
│   │   └── test_symbol.py
│   ├── analytics/
│   │   ├── __init__.py
│   │   └── test_risk_metrics.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── test_base.py
│   │   ├── test_registry.py
│   │   ├── test_ema_crossover.py
│   │   ├── test_rsi.py
│   │   ├── test_macd.py
│   │   ├── test_bollinger_bands.py
│   │   ├── test_volume.py
│   │   └── test_ma_ribbon.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── test_backtest_engine.py
│   │   ├── test_optimizer.py
│   │   └── test_walkforward.py
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── test_features.py
│   │   └── test_ml_strategies.py
│   └── test_properties.py
├── integration/
│   ├── __init__.py
│   ├── test_backtest_workflow.py
│   ├── test_data_providers.py
│   ├── test_database.py
│   └── test_api.py
├── fixtures/
│   ├── __init__.py
│   ├── sample_data.py       # Generate synthetic OHLCV
│   └── sample_trades.py     # Sample trade lists
└── performance/
    ├── __init__.py
    └── test_scalability.py
```

---

## Shared Fixtures (conftest.py)

```python
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

@pytest.fixture
def sample_ohlcv():
    """Generate sample OHLCV data for testing"""
    n = 100
    dates = pd.date_range(start='2023-01-01', periods=n, freq='D')
    
    np.random.seed(42)
    price = 100
    prices = []
    for _ in range(n):
        price += np.random.randn() * 2
        prices.append(price)
    
    return pd.DataFrame({
        'open': prices,
        'high': [p + abs(np.random.randn()) for p in prices],
        'low': [p - abs(np.random.randn()) for p in prices],
        'close': prices,
        'volume': [int(np.random.uniform(1e6, 5e6)) for _ in prices],
    }, index=dates)

@pytest.fixture
def sample_trades():
    """List of sample Trade objects"""
    from src.domain.entities.trade import Trade, TradeSide, TradeStatus
    return [
        Trade('AAPL', datetime(2023, 1, 1), 100.0, 10, TradeSide.LONG,
              exit_time=datetime(2023, 1, 5), exit_price=110.0),
        Trade('AAPL', datetime(2023, 1, 10), 105.0, 10, TradeSide.LONG,
              exit_time=datetime(2023, 1, 15), exit_price=102.0),
    ]

@pytest.fixture
def mock_yahoo_provider(mocker):
    """Mock Yahoo Finance provider"""
    # Implementation
    pass

@pytest.fixture
def test_database():
    """In-memory SQLite for testing"""
    # Implementation
    pass
```

---

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run Specific Phase
```bash
pytest tests/unit/domain/ -v
pytest tests/unit/strategies/ -v
pytest tests/integration/ -v
```

### Run with Hypothesis
```bash
pytest tests/unit/test_properties.py -v --hypothesis-show-statistics
```

---

## Coverage Targets

| Phase | Target | Current |
|-------|--------|---------|
| Phase 1 | 90% domain | **159 tests / 60%** ✅ |
| Phase 2 | 85% strategies | 0 tests |
| Phase 3 | 80% engine | 0 tests |
| Phase 4 | 75% integration | 0 tests |
| Phase 5 | Properties | 0 tests |
| Phase 6 | Performance | 0 tests |
| **Total** | **80%** | **60%** |

### Phase 1 Detailed Coverage (Domain Layer)
| File | Coverage |
|------|----------|
| domain/entities/trade.py | 98% |
| domain/entities/position.py | 100% |
| domain/entities/signal.py | 100% |
| domain/entities/ohlcv.py | 100% |
| domain/value_objects/symbol.py | 100% |
| domain/entities/metrics.py | 95% |
| analytics/risk_metrics.py | 78% |

---

## Implementation Order

### Step 1: Setup (Before Phase 1)
- [x] Create test directory structure
- [x] Create `tests/conftest.py` with fixtures
- [x] Verify pytest runs

### Step 2: Phase 1 - Domain Layer
- [x] Create domain test files
- [x] Implement trade tests (18 tests)
- [x] Implement position tests (14 tests)
- [x] Implement signal tests (34 tests)
- [x] Implement ohlcv tests (11 tests)
- [x] Implement symbol tests (18 tests)
- [x] Implement metrics tests (17 tests)
- [x] Implement analytics/risk_metrics tests (24 tests)
- [x] Run and verify 114+ tests pass ✅

### Step 3: Phase 2 - Strategies
- [ ] Create strategy test files
- [ ] Implement base strategy tests
- [ ] Implement individual strategy tests
- [ ] Run and verify 30+ tests pass

### Step 4: Phase 3 - Engine & ML
- [ ] Create engine test files
- [ ] Implement backtest engine tests
- [ ] Implement optimizer tests
- [ ] Implement ML tests
- [ ] Run and verify 40+ tests pass

### Step 5: Phase 4 - Integration
- [ ] Create integration test files
- [ ] Implement workflow tests
- [ ] Implement provider tests
- [ ] Run and verify 20+ tests pass

### Step 6: Phase 5 - Property-Based
- [ ] Create property test file
- [ ] Implement hypothesis tests
- [ ] Run and verify 20+ tests pass

### Step 7: Phase 6 - Performance
- [ ] Create performance test file
- [ ] Implement scalability tests
- [ ] Run and verify 10+ tests pass

---

## Notes

- All test files should use relative imports: `from src.domain.entities.trade import ...`
- Run `PYTHONPATH=. pytest` from project root
- Use `pytest.mark.skip` for slow tests
- Mock external APIs (Yahoo, Alpha Vantage) to avoid network dependency
- Use `@pytest.fixture(scope="session")` for expensive fixtures
- Property-based tests use `hypothesis` for automatic test case generation

---

## Checklist

- [x] Testing strategy planned
- [x] Test directory structure created
- [x] conftest.py with fixtures created
- [x] Phase 1: Domain layer tests (114 tests) ✅
- [ ] Phase 2: Strategy tests (30 tests)
- [ ] Phase 3: Engine & ML tests (40 tests)
- [ ] Phase 4: Integration tests (20 tests)
- [ ] Phase 5: Property-based tests (20 tests)
- [ ] Phase 6: Performance tests (10 tests)
- [ ] CI/CD pipeline setup (optional)
- [ ] Target 80% coverage achieved

---

*This document serves as the implementation guide for TSRL testing strategy.*
