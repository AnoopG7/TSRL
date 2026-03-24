import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from src.infrastructure.data_providers.yahoo_provider import YahooFinanceProvider
from src.infrastructure.data_providers.alpha_vantage_provider import AlphaVantageProvider
from src.infrastructure.data_providers.base import DataProviderError
from src.infrastructure.database.repositories.ohlcv_repository import OHLCVRepository

logger = logging.getLogger(__name__)


class DataService:
    """Service for data fetching, caching, and persistence."""

    def fetch_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
        source: str = "alpha_vantage",
    ) -> tuple[pd.DataFrame, str, dict]:
        """
        Fetch market data. Returns (dataframe, data_source_label, quality_metadata).
        Raises an error if the provider fails.

        Metadata includes:
        - is_simulated: bool - True if using generated/simulated data
        - warning_message: str - Description of any issues encountered
        - original_exception: str - The exception that triggered fallback (if any)
        """
        try:
            if source == "yahoo":
                provider = YahooFinanceProvider()
            elif source == "alpha_vantage":
                provider = AlphaVantageProvider()
            else:
                logger.warning(f"Unknown source '{source}', defaulting to Yahoo Finance")
                provider = YahooFinanceProvider()

            df = provider.fetch_ohlcv(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
            )
            logger.info(f"Fetched {len(df)} rows of live data for {symbol}")
            return df, "live", {
                "is_simulated": False,
                "warning_message": None,
                "original_exception": None,
            }

        except Exception as e:
            error_msg = f"Data fetch failed for {symbol}: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def ingest_and_persist(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
        source: str = "yahoo",
        session=None,
    ) -> dict:
        """Fetch data and persist to database.

        Returns metadata including data quality flags.
        """
        df, data_source, quality = self.fetch_data(symbol, start_date, end_date, timeframe, source)

        repo = OHLCVRepository(session=session)
        records_added = repo.save_ohlcv(symbol, timeframe, df, source=data_source)

        return {
            "symbol": symbol,
            "rows_fetched": len(df),
            "rows_persisted": records_added,
            "data_source": data_source,
            "timeframe": timeframe,
            "is_simulated": quality["is_simulated"],
            "warning_message": quality["warning_message"],
        }
