import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def generate_sample_ohlcv(
    symbol: str = "SAMPLE",
    start_date: datetime = None,
    end_date: datetime = None,
    initial_price: float = 100.0,
    volatility: float = 0.02,
    drift: float = 0.0001,
    n_days: int = 365,
) -> pd.DataFrame:
    if start_date is None:
        start_date = datetime.now() - timedelta(days=n_days)
    if end_date is None:
        end_date = datetime.now()

    n_bars = (end_date - start_date).days

    # Use symbol hash for seed to get different data per symbol
    np.random.seed(hash(symbol) % (2**31))

    returns = np.random.normal(drift, volatility, n_bars)
    returns = np.clip(returns, -0.1, 0.1)

    prices = initial_price * np.cumprod(1 + returns)

    timestamps = pd.date_range(start=start_date, periods=n_bars, freq="D")

    df = pd.DataFrame(index=timestamps)
    df["symbol"] = symbol

    df["open"] = prices * (1 + np.random.uniform(-0.005, 0.005, n_bars))
    df["close"] = prices * (1 + np.random.uniform(-0.005, 0.005, n_bars))
    df["high"] = np.maximum(df["open"], df["close"]) * (
        1 + np.abs(np.random.uniform(0, 0.01, n_bars))
    )
    df["low"] = np.minimum(df["open"], df["close"]) * (
        1 - np.abs(np.random.uniform(0, 0.01, n_bars))
    )

    df["volume"] = np.random.uniform(1000000, 10000000, n_bars).astype(int)

    df.index.name = "timestamp"

    return df
