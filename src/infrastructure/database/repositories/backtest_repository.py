import json
import logging
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.infrastructure.database.connection import get_session_factory
from src.infrastructure.database.models import orm_models

logger = logging.getLogger(__name__)


class BacktestRepository:
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

    def create(
        self,
        name: str,
        symbol: str,
        strategy_name: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        config: Optional[dict] = None,
    ) -> orm_models.Backtest:
        symbol_obj = self._get_or_create_symbol(symbol)
        strategy_obj = self._get_or_create_strategy(strategy_name)

        backtest = orm_models.Backtest(
            name=name,
            symbol_id=symbol_obj.id,
            strategy_id=strategy_obj.id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            config_json=json.dumps(config) if config else None,
            status="running",
        )
        self.session.add(backtest)
        self.session.commit()
        logger.info(f"Created backtest: {backtest.id}")
        return backtest

    def update_results(
        self,
        backtest_id: int,
        final_capital: float,
        total_return: float,
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        metrics: Optional[dict] = None,
    ) -> orm_models.Backtest:
        backtest = self.session.query(orm_models.Backtest).get(backtest_id)
        if not backtest:
            raise ValueError(f"Backtest {backtest_id} not found")

        backtest.final_capital = final_capital
        backtest.total_return = total_return
        backtest.total_trades = total_trades
        backtest.winning_trades = winning_trades
        backtest.losing_trades = losing_trades
        backtest.status = "completed"

        if metrics:
            existing = json.loads(backtest.config_json) if backtest.config_json else {}
            existing["metrics"] = metrics
            backtest.config_json = json.dumps(existing)

        self.session.commit()
        self.session.refresh(backtest)
        logger.info(f"Updated backtest results: {backtest_id}")
        return backtest

    def get(self, backtest_id: int) -> Optional[orm_models.Backtest]:
        return self.session.query(orm_models.Backtest).get(backtest_id)

    def get_all(self, limit: int = 100) -> list[orm_models.Backtest]:
        return (
            self.session.query(orm_models.Backtest)
            .order_by(orm_models.Backtest.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_symbol(self, symbol: str) -> list[orm_models.Backtest]:
        symbol_obj = self.session.query(orm_models.Symbol).filter_by(ticker=symbol.upper()).first()
        if not symbol_obj:
            return []
        return (
            self.session.query(orm_models.Backtest)
            .filter(orm_models.Backtest.symbol_id == symbol_obj.id)
            .order_by(orm_models.Backtest.created_at.desc())
            .all()
        )

    def delete(self, backtest_id: int) -> bool:
        backtest = self.session.query(orm_models.Backtest).get(backtest_id)
        if backtest:
            self.session.delete(backtest)
            self.session.commit()
            return True
        return False

    def _get_or_create_symbol(self, ticker: str) -> orm_models.Symbol:
        symbol = self.session.query(orm_models.Symbol).filter_by(ticker=ticker.upper()).first()
        if not symbol:
            symbol = orm_models.Symbol(ticker=ticker.upper())
            self.session.add(symbol)
            self.session.flush()
        return symbol

    def _get_or_create_strategy(self, name: str) -> orm_models.Strategy:
        strategy = self.session.query(orm_models.Strategy).filter_by(name=name).first()
        if not strategy:
            strategy = orm_models.Strategy(
                name=name,
                strategy_type="unknown",
                description=f"Auto-created strategy: {name}",
            )
            self.session.add(strategy)
            self.session.flush()
        return strategy

    def close(self) -> None:
        if self._provided_session is None and self._session:
            self._session.close()


class TradeRepository:
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

    def create(
        self,
        backtest_id: int,
        symbol: str,
        entry_time: datetime,
        entry_price: float,
        quantity: float,
        side: str,
    ) -> orm_models.Trade:
        symbol_obj = self._get_or_create_symbol(symbol)

        trade = orm_models.Trade(
            backtest_id=backtest_id,
            symbol_id=symbol_obj.id,
            entry_time=entry_time,
            entry_price=entry_price,
            quantity=quantity,
            side=side,
            status="open",
        )
        self.session.add(trade)
        self.session.commit()
        self.session.refresh(trade)
        return trade

    def close_trade(
        self,
        trade_id: int,
        exit_time: datetime,
        exit_price: float,
        pnl: float,
        pnl_pct: float,
        commission: float = 0,
        slippage: float = 0,
    ) -> orm_models.Trade:
        trade = self.session.query(orm_models.Trade).get(trade_id)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
        trade.commission = commission
        trade.slippage = slippage
        trade.status = "closed"

        self.session.commit()
        self.session.refresh(trade)
        return trade

    def get_by_backtest(self, backtest_id: int) -> list[orm_models.Trade]:
        return (
            self.session.query(orm_models.Trade)
            .filter(orm_models.Trade.backtest_id == backtest_id)
            .order_by(orm_models.Trade.entry_time)
            .all()
        )

    def get_open_trades(self, backtest_id: int) -> list[orm_models.Trade]:
        return (
            self.session.query(orm_models.Trade)
            .filter(
                and_(
                    orm_models.Trade.backtest_id == backtest_id,
                    orm_models.Trade.status == "open",
                )
            )
            .all()
        )

    def get_all_as_dataframe(self, backtest_id: int) -> pd.DataFrame:
        trades = self.get_by_backtest(backtest_id)
        if not trades:
            return pd.DataFrame()

        data = {
            "id": [t.id for t in trades],
            "entry_time": [t.entry_time for t in trades],
            "exit_time": [t.exit_time for t in trades],
            "entry_price": [t.entry_price for t in trades],
            "exit_price": [t.exit_price for t in trades],
            "quantity": [t.quantity for t in trades],
            "side": [t.side for t in trades],
            "pnl": [t.pnl for t in trades],
            "pnl_pct": [t.pnl_pct for t in trades],
            "status": [t.status for t in trades],
        }
        return pd.DataFrame(data)

    def _get_or_create_symbol(self, ticker: str) -> orm_models.Symbol:
        symbol = self.session.query(orm_models.Symbol).filter_by(ticker=ticker.upper()).first()
        if not symbol:
            symbol = orm_models.Symbol(ticker=ticker.upper())
            self.session.add(symbol)
            self.session.flush()
        return symbol

    def close(self) -> None:
        if self._provided_session is None and self._session:
            self._session.close()
