import pytest
from unittest.mock import patch
import pandas as pd
import numpy as np

@pytest.fixture(autouse=True)
def mock_data_service():
    """Mock DataService to prevent slow network calls during CLI tests."""
    dates = pd.date_range("2023-01-01", periods=252, freq="D")
    np.random.seed(42)
    
    prices = 100 + np.cumsum(np.random.randn(252) * 2)
    df = pd.DataFrame(
        {
            "open": prices,
            "high": prices + 2,
            "low": prices - 2,
            "close": prices + 1,
            "volume": [1000000] * 252,
        },
        index=dates,
    )
    
    with patch("src.application.services.data_service.DataService.fetch_data", return_value=(df, "mock", True)):
        yield
