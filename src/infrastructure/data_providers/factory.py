import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from src.infrastructure.data_providers.base import BaseDataProvider, DataProviderError

logger = logging.getLogger(__name__)


class DataProviderFactory:
    _providers: dict[str, BaseDataProvider] = {}
    _default_provider: str = "yahoo"

    @classmethod
    def register(cls, name: str, provider: BaseDataProvider) -> None:
        cls._providers[name] = provider
        logger.info(f"Registered data provider: {name}")

    @classmethod
    def get(cls, name: Optional[str] = None) -> BaseDataProvider:
        provider_name = name or cls._default_provider
        if provider_name not in cls._providers:
            raise ValueError(f"Provider '{provider_name}' not registered")
        return cls._providers[provider_name]

    @classmethod
    def set_default(cls, name: str) -> None:
        if name not in cls._providers:
            raise ValueError(f"Provider '{name}' not registered")
        cls._default_provider = name
        logger.info(f"Default provider set to: {name}")

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())


class UnifiedDataProvider(BaseDataProvider):
    def __init__(self, providers: Optional[dict[str, BaseDataProvider]] = None):
        self.providers = providers or {}
        self._default = "yahoo"

    def add_provider(self, name: str, provider: BaseDataProvider) -> None:
        self.providers[name] = provider
        if not hasattr(self, "_default") or self._default is None:
            self._default = name

    def set_default(self, name: str) -> None:
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not registered")
        self._default = name

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
        provider: Optional[str] = None,
    ) -> pd.DataFrame:
        provider_name = provider or self._default

        if provider_name not in self.providers:
            tried = ", ".join(self.providers.keys()) or "none"
            raise DataProviderError(f"Provider '{provider_name}' not available. Available: {tried}")

        return self.providers[provider_name].fetch_ohlcv(symbol, start_date, end_date, timeframe)

    def get_symbol_info(self, symbol: str, provider: Optional[str] = None) -> dict:
        provider_name = provider or self._default
        if provider_name not in self.providers:
            raise DataProviderError(f"Provider '{provider_name}' not available")
        return self.providers[provider_name].get_symbol_info(symbol)

    def get_recent_price(self, symbol: str, provider: Optional[str] = None) -> Optional[float]:
        provider_name = provider or self._default
        if provider_name not in self.providers:
            return None
        return self.providers[provider_name].get_recent_price(symbol)
