# MACD Strategy

Momentum strategy using MACD (Moving Average Convergence Divergence) crossovers.

## What It Does

- **MACD Line**: Fast EMA - Slow EMA
- **Signal Line**: EMA of MACD line
- **Buy signal**: MACD crosses above signal line
- **Sell signal**: MACD crosses below signal line

## Implementation

Located in: `src/strategies/momentum/macd_strategy.py`

```python
@register_strategy("macd")
class MACDStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "macd"

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate MACD
        ema_fast = df["close"].ewm(span=self._fast_period).mean()
        ema_slow = df["close"].ewm(span=self._slow_period).mean()
        df["macd"] = ema_fast - ema_slow
        df["signal"] = df["macd"].ewm(span=self._signal_period).mean()
        
        # Crossover signals
        df.loc[(df["macd"] > df["signal"]) & (df["macd"].shift(1) <= df["signal"].shift(1)), "signal"] = 1
        df.loc[(df["macd"] < df["signal"]) & (df["macd"].shift(1) >= df["signal"].shift(1)), "signal"] = -1
        
        return df
```

## Parameters

| Parameter | Default | Range | Description |
|------------|---------|-------|-------------|
| `fast_period` | 12 | 5-50 | Fast EMA period |
| `slow_period` | 26 | 10-100 | Slow EMA period |
| `signal_period` | 9 | 5-30 | Signal line EMA period |

## MACD Histogram

The histogram (MACD - Signal) shows momentum:

- **Positive**: Bullish momentum
- **Negative**: Bearish momentum
- **Increasing**: Momentum strengthening

## Usage

```bash
# CLI
PYTHONPATH=. python -m src.cli backtest --strategy macd --symbol AAPL

# API
POST /api/v1/backtests/run
{"strategy_name": "macd", "symbol": "AAPL", ...}
```

## Related

- [[Backtesting]] — How to test this strategy
- [[EMA Crossover]] — Simpler version without signal line
- [[Risk Metrics]] — Metrics produced