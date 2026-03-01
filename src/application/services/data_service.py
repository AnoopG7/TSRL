import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from src.infrastructure.data_providers.yahoo_provider import YahooFinanceProvider
from src.infrastructure.data_providers.base import DataProviderError
from src.infrastructure.database.repositories.ohlcv_repository import OHLCVRepository
from src.data.generate_sample_data import generate_sample_ohlcv

logger = logging.getLogger(__name__)


class DataService:
    """Service for data fetching, caching, and persistence."""

    def fetch_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
        source: str = "yahoo",
    ) -> tuple[pd.DataFrame, str]:
        """
        Fetch market data. Returns (dataframe, data_source_label).
        Falls back to simulated data if provider fails.
        """
        try:
            if source == "yahoo":
                provider = YahooFinanceProvider()
            else:
                provider = YahooFinanceProvider()

            df = provider.fetch_ohlcv(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
            )
            logger.info(f"Fetched {len(df)} rows of live data for {symbol}")
            return df, "live"

        except (DataProviderError, Exception) as e:
            logger.warning(f"Data fetch failed for {symbol}: {e}. Using simulated data.")
            n_days = (end_date - start_date).days
            df = generate_sample_ohlcv(symbol=symbol, n_days=max(n_days, 30))
            return df, "simulated"

    def ingest_and_persist(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
        source: str = "yahoo",
        session=None,
    ) -> dict:
        """Fetch data and persist to database."""
        df, data_source = self.fetch_data(symbol, start_date, end_date, timeframe, source)

        repo = OHLCVRepository(session=session)
        records_added = repo.save_ohlcv(symbol, timeframe, df, source=data_source)

        return {
            "symbol": symbol,
            "rows_fetched": len(df),
            "rows_persisted": records_added,
            "data_source": data_source,
            "timeframe": timeframe,
        }
