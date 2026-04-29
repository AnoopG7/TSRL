# Strategy Map

## Strategy Families

### Momentum Strategies
| Strategy | File | Description |
|----------|------|-------------|
| `ema_crossover` | `src/strategies/momentum/ema_crossover.py` | EMA fast/slow crossover signals |
| `rsi_mean_reversion` | `src/strategies/momentum/ema_crossover.py` | RSI oversold/overbought |
| `macd` | `src/strategies/momentum/macd_strategy.py` | MACD crossover signals |
| `ma_ribbon` | `src/strategies/momentum/ma_ribbon.py` | Multiple moving average ribbon |
| `triple_ma` | `src/strategies/momentum/ma_ribbon.py` | Triple MA crossover |
| `volume_profile` | `src/strategies/momentum/volume_strategies.py` | Volume-based support/resistance |
| `volume_breakout` | `src/strategies/momentum/volume_strategies.py` | Volume surge breakout |

### Mean Reversion Strategies
| Strategy | File | Description |
|----------|------|-------------|
| `bollinger_bands` | `src/strategies/mean_reversion/bollinger_bands.py` | Bollinger Bands bounce |
| `bbands` | `src/strategies/mean_reversion/bollinger_bands.py` | Bollinger Bands breakout |

### Breakout Strategies
| Strategy | File | Description |
|----------|------|-------------|
| `breakout` | `src/strategies/momentum/ema_crossover.py` | Price breakout above/below recent high/low |

### ML Strategies
| Strategy | File | Description |
|----------|------|-------------|
| `ml_random_forest` | `src/ml/strategies/ml_strategies.py` | Random Forest classifier with 116 features |
| `ml_gradient_boosting` | `src/ml/strategies/ml_strategies.py` | Gradient Boosting classifier |

### Volatility Strategies
- *(placeholder - not yet implemented)*

## Registry Pattern

Strategies are auto-discovered via decorators:

```python
from src.strategies.registry import register_strategy

@register_strategy("ema_crossover")
class EMACrossoverStrategy(BaseStrategy):
    ...
```

All registered strategies are available via:
```python
from src.strategies.registry import StrategyRegistry
StrategyRegistry.get("ema_crossover")  # Returns strategy class
StrategyRegistry.list_all()  # Returns all strategy names
```

## Strategy Base Class

All strategies inherit from `BaseStrategy` (`src/strategies/base.py`):

```python
class BaseStrategy:
    @property
    def name(self) -> str: ...
    
    @property
    def version(self) -> str: ...
    
    @property
    def description(self) -> str: ...
    
    @property
    def parameters(self) -> dict[str, StrategyParameter]: ...
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame: ...
    
    def entry_conditions(self, data: pd.DataFrame, idx: int) -> bool: ...
    
    def exit_conditions(self, data: pd.DataFrame, idx: int) -> bool: ...
```

## Key Parameters by Strategy

| Strategy | Key Parameters |
|----------|---------------|
| EMA Crossover | `fast_period` (default: 12), `slow_period` (default: 26) |
| RSI Mean Reversion | `rsi_period` (default: 14), `oversold` (default: 30), `overbought` (default: 70) |
| MACD | `fast_period` (12), `slow_period` (26), `signal_period` (9) |
| MA Ribbon | `fast_periods` (list), `slow_periods` (list) |
| Bollinger Bands | `period` (20), `std_dev` (2.0) |
| Volume Breakout | `volume_multiplier` (2.0), `lookback` (20) |
| ML Random Forest | `n_estimators` (100), `max_depth` (5), `lookback` (50) |