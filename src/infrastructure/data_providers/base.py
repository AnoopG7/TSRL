from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List

import pandas as pd


class DataProviderError(Exception):
    pass


class DataValidationError(Exception):
    pass


class BaseDataProvider(ABC):
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_symbol_info(self, symbol: str) -> dict:
        pass

    @abstractmethod
    def get_recent_price(self, symbol: str) -> Optional[float]:
        pass

    def validate_ohlcv(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise DataValidationError("DataFrame is empty")

        # Support both raw (uppercase) and normalized (lowercase) column names
        if "open" in df.columns:
            o, h, l, c, v = "open", "high", "low", "close", "volume"
        elif "Open" in df.columns:
            o, h, l, c, v = "Open", "High", "Low", "Close", "Volume"
        else:
            raise DataValidationError("Missing required OHLCV columns")

        for col in [o, h, l, c, v]:
            if col not in df.columns:
                raise DataValidationError(f"Missing required column: {col}")

        if df[[o, h, l, c, v]].isnull().values.any():
            null_counts = df[[o, h, l, c, v]].isnull().sum()
            raise DataValidationError(
                f"Null values found: {null_counts[null_counts > 0].to_dict()}"
            )

        if (df[h] < df[l]).any():
            raise DataValidationError("High cannot be less than Low")

        if (df[h] < df[o]).any():
            raise DataValidationError("High cannot be less than Open")

        if (df[h] < df[c]).any():
            raise DataValidationError("High cannot be less than Close")

        if (df[l] > df[o]).any():
            raise DataValidationError("Low cannot be greater than Open")

        if (df[l] > df[c]).any():
            raise DataValidationError("Low cannot be greater than Close")

        if (df[[o, h, l, c]] <= 0).any().any():
            raise DataValidationError("Prices must be positive")

        if (df[v] < 0).any():
            raise DataValidationError("Volume cannot be negative")

        return df

    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Adj Close": "adj_close",
        }
        df = df.rename(columns=rename_map)
        df.index = pd.to_datetime(df.index)
        df.index.name = "timestamp"
        return df

    def handle_missing_values(self, df: pd.DataFrame, max_consecutive: int = 5) -> pd.DataFrame:
        null_counts = df.isnull().sum(axis=1)
        for idx, count in null_counts.items():
            if count > max_consecutive:
                raise DataValidationError(f"Too many consecutive missing values at {idx}")

        df = df.ffill(limit=max_consecutive)
        df = df.bfill(limit=max_consecutive)
        return df

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        duplicates = df.index.duplicated()
        if duplicates.any():
            df = df.loc[~duplicates]
        return df
