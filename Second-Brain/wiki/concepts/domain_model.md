# Domain Model

## Definition
The entity and value object catalog that represents TSRL's core business concepts. These are the data structures that flow through every layer — from data ingestion to strategy execution to persistence.

## Why It Matters
- **Shared vocabulary**: Everyone (code, API, wiki) speaks the same language about trades, positions, signals
- **Immutability contracts**: Entities that change unexpectedly cause silent bugs in backtesting
- **Serialization boundary**: Domain entities define what gets persisted and what gets transmitted via API

## In My System

### Entity Catalog

```
src/domain/entities/
├── trade.py         → Trade, TradeSide, TradeStatus
├── position.py      → Position, PositionSide
├── signal.py        → Signal, SignalType, SignalStrength
├── metrics.py       → RiskMetrics
├── ohlcv.py         → OHLCV bar representation
├── portfolio_metrics.py → PortfolioMetrics
└── fundamental/     → FundamentalReport, HealthScores
```

---

### Trade (`src/domain/entities/trade.py`)

The most important entity — represents a completed round-trip.

```python
@dataclass
class Trade:
    symbol: str
    entry_time: datetime
    entry_price: float
    quantity: float
    side: TradeSide          # LONG or SHORT
    exit_time: datetime
    exit_price: float
    status: TradeStatus       # PENDING, OPEN, CLOSED
    commission: float = 0.0
    slippage: float = 0.0

    @property
    def pnl(self) -> float:
        # LONG: (exit - entry) × qty - costs
        # SHORT: (entry - exit) × qty - costs
```

**Key contract:**
- `pnl` is a computed property, not stored. It derives from entry/exit prices and costs.
- `status` is always `CLOSED` in backtest results (open positions are force-closed)
- `commission` covers BOTH sides (entry + exit)

**Enum values:**
```python
class TradeSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class TradeStatus(Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
```

---

### Position (`src/domain/entities/position.py`)

An open trade in progress. Converted to `Trade` on close.

```python
@dataclass
class Position:
    symbol: str
    entry_time: datetime
    entry_price: float     # Already slippage-adjusted
    quantity: float
    side: PositionSide     # LONG or SHORT
    current_price: float   # Updated each bar? No — only set at entry
```

**Critical detail:** `current_price` is set to `entry_price` at creation and **never updated**. The engine doesn't track mark-to-market during a position's lifetime. This means unrealized P&L is unknown until close.

---

### Signal (`src/domain/entities/signal.py`)

```python
@dataclass
class Signal:
    signal_type: SignalType    # BUY, SELL, HOLD
    strength: SignalStrength   # WEAK, MODERATE, STRONG
    timestamp: datetime
    metadata: dict
```

**Usage gap:** The `Signal` entity exists but the engine reads raw DataFrame columns (`signal == 1`), not `Signal` objects. The entity is used in the domain layer but never instantiated by the engine.

---

### RiskMetrics (`src/domain/entities/metrics.py`)

The comprehensive metrics container — 20+ fields covering returns, risk, and trade statistics.

```python
@dataclass
class RiskMetrics:
    total_return: float = 0.0
    cagr: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    total_trades: int = 0
    # ... 10+ more fields
    
    @classmethod
    def from_trades(cls, trades, initial_capital, returns) -> "RiskMetrics":
        # Delegates to RiskMetricsCalculator for actual computation
```

**Factory pattern:** `RiskMetrics.from_trades()` is the only way to create a populated instance. It calls `RiskMetricsCalculator` methods from `src/analytics/risk_metrics.py`.

---

### PortfolioMetrics (`src/domain/entities/portfolio_metrics.py`)

Portfolio-level metrics that don't exist in single-symbol backtests.

```python
@dataclass
class PortfolioMetrics:
    correlation_matrix: dict = field(default_factory=dict)
    avg_correlation: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0
    tracking_error: float = 0.0
    information_ratio: float = 0.0
    diversification_ratio: float = 0.0
    concentration_hhi: float = 0.0
    asset_contributions: dict = field(default_factory=dict)
    risk_contributions: dict = field(default_factory=dict)
```

---

## Design Principles

### 1. Entities Are Dataclasses
All domain entities use `@dataclass`. No SQLAlchemy models in the domain layer. The ORM models (`src/infrastructure/database/models/`) are separate — they map to/from domain entities.

### 2. `to_dict()` Is The Serialization Boundary
Every entity has `to_dict()`. This is the contract for API responses and database persistence. Any field not in `to_dict()` is implementation-internal.

### 3. No Business Logic In Entities
Entities hold data, not behavior. The exception is computed properties like `Trade.pnl` — but this is a pure calculation, not a side effect.

### 4. Enums For Finite States
`TradeSide`, `TradeStatus`, `PositionSide`, `SignalType`, `SignalStrength` — all use Python enums for type safety and JSON serialization.

---

## Failure Cases

### 1. NaN Propagation in Metrics
**Symptom:** `RiskMetrics.to_dict()` returns `NaN` values, causing JSON serialization to fail

**Fix:** `_sanitize_float()` in `base.py:186-190` replaces `NaN/inf` with `None`

### 2. Position Side Mismatch
**Symptom:** Trade shows wrong P&L direction

**Cause:** `PositionSide.LONG` → `TradeSide.LONG` conversion in `_close_position()`. If this mapping is wrong, short trades report inverted P&L.

### 3. Signal Entity Unused
**Symptom:** Changes to `Signal` entity have no effect on backtesting

**Cause:** Engine reads `signals["signal"]` (integer column), not `Signal` objects

**Impact:** Low — the entity is future-proofing for a more sophisticated signal pipeline

---

## Related Concepts
- [[Trade Lifecycle]] — How these entities flow through the system
- [[Risk Metrics]] — The calculator that populates RiskMetrics
- [[Architecture Decisions]] — ADR-1: Clean Architecture

## Implementation References
- `src/domain/entities/` — All entity definitions
- `src/infrastructure/database/models/orm_models.py` — ORM mapping
- `src/analytics/risk_metrics.py` — RiskMetrics population
