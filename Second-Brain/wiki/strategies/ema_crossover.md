# EMA Crossover Strategy

Momentum strategy using Exponential Moving Average crossovers to generate buy/sell signals.

## What It Does

- **Buy signal**: When fast EMA crosses above slow EMA (bullish)
- **Sell signal**: When fast EMA crosses below slow EMA (bearish)

## Implementation

Located in: `src/strategies/momentum/ema_crossover.py`

```python
@register_strategy("ema_crossover")
class EMACrossoverStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "EMA Crossover"

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        df["ema_fast"] = df["close"].ewm(span=fast_period).mean()
        df["ema_slow"] = df["close"].ewm(span=slow_period).mean()
        
        # Buy: fast crosses above slow
        df.loc[(crossover > 0) & (prev_crossover <= 0), "signal"] = 1
        # Sell: fast crosses below slow
        df.loc[(crossover < 0) & (prev_crossover >= 0), "signal"] = -1
        
        return df
```

## Parameters

| Parameter | Default | Range | Description |
|------------|---------|-------|-------------|
| `fast_period` | 12 | 5-50 | Fast EMA period |
| `slow_period` | 26 | 20-200 | Slow EMA period |

## Entry Conditions

```python
def entry_conditions(self, data, idx):
    # Fast EMA crosses above slow EMA
    return data["ema_fast"].iloc[idx] > data["ema_slow"].iloc[idx] and \
           data["ema_fast"].iloc[idx-1] <= data["ema_slow"].iloc[idx-1]
```

## Exit Conditions

```python
def exit_conditions(self, data, idx):
    # Fast EMA crosses below slow EMA
    return data["ema_fast"].iloc[idx] < data["ema_slow"].iloc[idx] and \
           data["ema_fast"].iloc[idx-1] >= data["ema_slow"].iloc[idx-1]
```

## Usage

```bash
# CLI
PYTHONPATH=. python -m src.cli backtest --strategy ema_crossover --symbol AAPL

# API
POST /api/v1/backtests/run
{"strategy_name": "ema_crossover", "symbol": "AAPL", ...}
```

## Related

- [[Backtesting]] — How to test this strategy
- [[MACD]] — Similar but with signal line
- [[Risk Metrics]] — Metrics produced