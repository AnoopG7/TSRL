import logging
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.infrastructure.database.connection import get_session_factory
from src.infrastructure.database.models import orm_models

logger = logging.getLogger(__name__)


class OHLCVRepository:
    def __init__(self, session: Optional[Session] = None):
        self._provided_session = session
        self._session = None

    @property
    def session(self) -> Session:
        if self._provided_session:
            return self._provided_session
        if self._session is None:
            self._session_factory = get_session_factory()
            self._session = self._session_factory()
        return self._session

    def get_or_create_symbol(
        self,
        ticker: str,
        name: Optional[str] = None,
        exchange: str = "UNKNOWN",
        currency: str = "USD",
    ) -> orm_models.Symbol:
        symbol = self.session.query(orm_models.Symbol).filter_by(ticker=ticker.upper()).first()
        if symbol:
            return symbol

        symbol = orm_models.Symbol(
            ticker=ticker.upper(),
            name=name or ticker.upper(),
            exchange=exchange,
            currency=currency,
        )
        self.session.add(symbol)
        self.session.flush()
        return symbol

    def get_or_create_timeframe(self, name: str, minutes: int) -> orm_models.Timeframe:
        tf = self.session.query(orm_models.Timeframe).filter_by(name=name).first()
        if tf:
            return tf

        tf = orm_models.Timeframe(name=name, minutes=minutes)
        self.session.add(tf)
        self.session.flush()
        return tf

    def save_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame,
        source: str = "yahoo",
    ) -> int:
        symbol_obj = self.get_or_create_symbol(symbol)
        timeframe_obj = self.get_or_create_timeframe(
            timeframe, self._timeframe_to_minutes(timeframe)
        )

        records_added = 0
        for idx, row in data.iterrows():
            existing = (
                self.session.query(orm_models.OHLCV)
                .filter(
                    and_(
                        orm_models.OHLCV.symbol_id == symbol_obj.id,
                        orm_models.OHLCV.timeframe_id == timeframe_obj.id,
                        orm_models.OHLCV.timestamp == idx,
                    )
                )
                .first()
            )

            if not existing:
                ohlcv = orm_models.OHLCV(
                    symbol_id=symbol_obj.id,
                    timeframe_id=timeframe_obj.id,
                    timestamp=idx,
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                    source=source,
                    validated=True,
                )
                self.session.add(ohlcv)
                records_added += 1

        self.session.commit()
        logger.info(f"Saved {records_added} OHLCV records for {symbol}")
        return records_added

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        symbol_obj = self.session.query(orm_models.Symbol).filter_by(ticker=symbol.upper()).first()
        if not symbol_obj:
            return pd.DataFrame()

        timeframe_obj = self.session.query(orm_models.Timeframe).filter_by(name=timeframe).first()
        if not timeframe_obj:
            return pd.DataFrame()

        query = self.session.query(orm_models.OHLCV).filter(
            and_(
                orm_models.OHLCV.symbol_id == symbol_obj.id,
                orm_models.OHLCV.timeframe_id == timeframe_obj.id,
            )
        )

        if start_date:
            query = query.filter(orm_models.OHLCV.timestamp >= start_date)
        if end_date:
            query = query.filter(orm_models.OHLCV.timestamp <= end_date)

        results = query.order_by(orm_models.OHLCV.timestamp).all()

        if not results:
            return pd.DataFrame()

        data = {
            "timestamp": [r.timestamp for r in results],
            "open": [r.open for r in results],
            "high": [r.high for r in results],
            "low": [r.low for r in results],
            "close": [r.close for r in results],
            "volume": [r.volume for r in results],
        }
        df = pd.DataFrame(data)
        df = df.set_index("timestamp")
        return df

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        mapping = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
        }
        return mapping.get(timeframe, 1440)

    def close(self) -> None:
        if self._provided_session is None and self._session:
            self._session.close()
