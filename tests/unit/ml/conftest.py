import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv_data():
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    np.random.seed(42)

    base_price = 100
    prices = base_price + np.cumsum(np.random.randn(100) * 0.5)

    data = pd.DataFrame(
        {
            "open": prices + np.random.randn(100) * 0.2,
            "high": prices + np.abs(np.random.randn(100)) * 0.5,
            "low": prices - np.abs(np.random.randn(100)) * 0.5,
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, 100).astype(float),
        },
        index=dates,
    )

    data["high"] = data[["open", "high", "close"]].max(axis=1)
    data["low"] = data[["open", "low", "close"]].min(axis=1)

    return data


@pytest.fixture
def sample_ohlcv_data_large():
    dates = pd.date_range(start="2022-01-01", periods=300, freq="D")
    np.random.seed(123)

    base_price = 150
    prices = base_price + np.cumsum(np.random.randn(300) * 0.8)

    data = pd.DataFrame(
        {
            "open": prices + np.random.randn(300) * 0.3,
            "high": prices + np.abs(np.random.randn(300)) * 0.6,
            "low": prices - np.abs(np.random.randn(300)) * 0.6,
            "close": prices,
            "volume": np.random.randint(500000, 15000000, 300).astype(float),
        },
        index=dates,
    )

    data["high"] = data[["open", "high", "close"]].max(axis=1)
    data["low"] = data[["open", "low", "close"]].min(axis=1)

    return data
