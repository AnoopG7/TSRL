# Bollinger Bands Strategy

Mean reversion strategy using Bollinger Bands to identify overbought/oversold conditions.

## What It Does

- **Upper Band**: SMA + (N × std)
- **Middle Band**: N-period SMA
- **Lower Band**: SMA - (N × std)

- **Buy signal**: Price touches lower band (oversold)
- **Sell signal**: Price touches upper band (overbought)

## Implementation

Located in: `src/strategies/mean_reversion/bollinger_bands.py`

```python
@register_strategy("bollinger_bands")
class BollingerBandsStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "bollinger_bands"

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate bands
        sma = df["close"].rolling(window=period).mean()
        std = df["close"].rolling(window=period).std()
        
        df["upper_band"] = sma + (std * std_dev)
        df["middle_band"] = sma
        df["lower_band"] = sma - (std * std_dev)
        
        # Buy: price at or below lower band
        df.loc[df["close"] <= df["lower_band"], "signal"] = 1
        # Sell: price at or above upper band
        df.loc[df["close"] >= df["upper_band"], "signal"] = -1
        
        return df
```

## Parameters

| Parameter | Default | Range | Description |
|------------|---------|-------|-------------|
| `period` | 20 | 5-100 | Moving average period |
| `std_dev` | 2.0 | 0.5-4.0 | Standard deviation multiplier |

## Entry Conditions

```python
def entry_conditions(self, data, idx):
    # Price at or below lower band = oversold = buy
    return data["close"].iloc[idx] <= data["lower_band"].iloc[idx]
```

## Exit Conditions

```python
def exit_conditions(self, data, idx):
    # Price at or above middle band = mean reversion target
    return data["close"].iloc[idx] >= data["middle_band"].iloc[idx]
```

## Band Width

The width between bands indicates volatility:

- **Narrow bands**: Low volatility (potential breakout)
- **Wide bands**: High volatility

## Usage

```bash
# CLI
PYTHONPATH=. python -m src.cli backtest --strategy bollinger_bands --symbol AAPL

# API
POST /api/v1/backtests/run
{"strategy_name": "bollinger_bands", "symbol": "AAPL", ...}
```

## Related

- [[Backtesting]] — How to test this strategy
- [[Risk Metrics]] — Metrics produced
- [[EMA Crossover]] — Alternative momentum strategy