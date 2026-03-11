import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.connection import Base
from src.infrastructure.database.models import orm_models
from src.infrastructure.database.repositories.backtest_repository import (
    BacktestRepository,
    TradeRepository,
)
from src.infrastructure.database.repositories.ohlcv_repository import OHLCVRepository


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_ohlcv_df():
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    np.random.seed(42)

    base_price = 100
    prices = base_price + np.cumsum(np.random.randn(100) * 0.5)

    data = pd.DataFrame(
        {
            "open": prices + np.random.randn(100) * 0.2,
            "high": prices + np.abs(np.random.randn(100)) * 0.5,
            "low": prices - np.abs(np.random.randn(100) * 0.5),
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, 100).astype(float),
        },
        index=dates,
    )

    data["high"] = data[["open", "high", "close"]].max(axis=1)
    data["low"] = data[["open", "low", "close"]].min(axis=1)

    return data


class TestBacktestRepository:
    def test_create_backtest(self, in_memory_db):
        repo = BacktestRepository(session=in_memory_db)

        backtest = repo.create(
            name="test_backtest",
            symbol="AAPL",
            strategy_name="ema_crossover",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 1),
            initial_capital=100000.0,
            config={"timeframe": "1d", "commission": 0.001},
        )

        assert backtest.id is not None
        assert backtest.name == "test_backtest"
        assert backtest.initial_capital == 100000.0

    def test_update_backtest_results(self, in_memory_db):
        repo = BacktestRepository(session=in_memory_db)

        backtest = repo.create(
            name="test_backtest",
            symbol="AAPL",
            strategy_name="ema_crossover",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 1),
            initial_capital=100000.0,
        )

        repo.update_results(
            backtest_id=backtest.id,
            final_capital=110000.0,
            total_return=0.10,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            metrics={"sharpe_ratio": 1.5},
        )

        updated = repo.get(backtest.id)
        assert updated.final_capital == 110000.0
        assert updated.total_return == 0.10
        assert updated.winning_trades == 6

    def test_load_backtest_by_id(self, in_memory_db):
        repo = BacktestRepository(session=in_memory_db)

        created = repo.create(
            name="test_load",
            symbol="MSFT",
            strategy_name="rsi_mean_reversion",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 6, 1),
            initial_capital=50000.0,
        )

        loaded = repo.get(created.id)

        assert loaded is not None
        assert loaded.id == created.id
        assert loaded.name == "test_load"

    def test_list_backtests(self, in_memory_db):
        repo = BacktestRepository(session=in_memory_db)

        repo.create(
            name="test1",
            symbol="AAPL",
            strategy_name="ema_crossover",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 1),
            initial_capital=100000.0,
        )
        repo.create(
            name="test2",
            symbol="GOOGL",
            strategy_name="bollinger_bands",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 1),
            initial_capital=100000.0,
        )

        backtests = repo.get_all()

        assert len(backtests) == 2

    def test_delete_backtest(self, in_memory_db):
        repo = BacktestRepository(session=in_memory_db)

        backtest = repo.create(
            name="test_delete",
            symbol="AAPL",
            strategy_name="ema_crossover",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 1),
            initial_capital=100000.0,
        )

        deleted = repo.delete(backtest.id)

        assert deleted is True
        assert repo.get(backtest.id) is None


class TestTradeRepository:
    def test_create_trade(self, in_memory_db):
        repo = TradeRepository(session=in_memory_db)
        backtest_repo = BacktestRepository(session=in_memory_db)

        backtest = backtest_repo.create(
            name="test_trade",
            symbol="AAPL",
            strategy_name="ema_crossover",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 1),
            initial_capital=100000.0,
        )

        trade = repo.create(
            backtest_id=backtest.id,
            symbol="AAPL",
            entry_time=datetime(2023, 1, 15),
            entry_price=150.0,
            quantity=100,
            side="long",
        )

        assert trade.id is not None
        assert trade.entry_price == 150.0

    def test_close_trade(self, in_memory_db):
        repo = TradeRepository(session=in_memory_db)
        backtest_repo = BacktestRepository(session=in_memory_db)

        backtest = backtest_repo.create(
            name="test_close",
            symbol="AAPL",
            strategy_name="ema_crossover",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 1),
            initial_capital=100000.0,
        )

        trade = repo.create(
            backtest_id=backtest.id,
            symbol="AAPL",
            entry_time=datetime(2023, 1, 15),
            entry_price=150.0,
            quantity=100,
            side="long",
        )

        repo.close_trade(
            trade_id=trade.id,
            exit_time=datetime(2023, 2, 15),
            exit_price=155.0,
            pnl=500.0,
            pnl_pct=3.33,
        )

        closed_trade = in_memory_db.query(orm_models.Trade).filter_by(id=trade.id).first()
        assert closed_trade.exit_price == 155.0
        assert closed_trade.pnl == 500.0

    def test_get_trades_by_backtest(self, in_memory_db):
        repo = TradeRepository(session=in_memory_db)
        backtest_repo = BacktestRepository(session=in_memory_db)

        backtest = backtest_repo.create(
            name="test_list",
            symbol="AAPL",
            strategy_name="ema_crossover",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 1),
            initial_capital=100000.0,
        )

        repo.create(
            backtest_id=backtest.id,
            symbol="AAPL",
            entry_time=datetime(2023, 1, 10),
            entry_price=100.0,
            quantity=50,
            side="long",
        )
        repo.create(
            backtest_id=backtest.id,
            symbol="AAPL",
            entry_time=datetime(2023, 2, 10),
            entry_price=105.0,
            quantity=50,
            side="long",
        )

        trades = repo.get_by_backtest(backtest.id)

        assert len(trades) == 2

    def test_get_open_trades(self, in_memory_db):
        repo = TradeRepository(session=in_memory_db)
        backtest_repo = BacktestRepository(session=in_memory_db)

        backtest = backtest_repo.create(
            name="test_open",
            symbol="AAPL",
            strategy_name="ema_crossover",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 1),
            initial_capital=100000.0,
        )

        repo.create(
            backtest_id=backtest.id,
            symbol="AAPL",
            entry_time=datetime(2023, 1, 10),
            entry_price=100.0,
            quantity=50,
            side="long",
        )

        open_trades = repo.get_open_trades(backtest.id)

        assert len(open_trades) == 1


class TestOHLCVRepository:
    def test_save_ohlcv(self, in_memory_db, sample_ohlcv_df):
        repo = OHLCVRepository(session=in_memory_db)

        records_added = repo.save_ohlcv("AAPL", "1d", sample_ohlcv_df, source="test")

        assert records_added == 100

        ohlcv_count = in_memory_db.query(orm_models.OHLCV).count()
        assert ohlcv_count == 100

    def test_get_ohlcv_by_symbol(self, in_memory_db, sample_ohlcv_df):
        repo = OHLCVRepository(session=in_memory_db)

        repo.save_ohlcv("AAPL", "1d", sample_ohlcv_df.head(50), source="test")

        result = repo.get_ohlcv(
            symbol="AAPL",
            timeframe="1d",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 2, 20),
        )

        assert len(result) == 50

    def test_get_ohlcv_columns(self, in_memory_db, sample_ohlcv_df):
        repo = OHLCVRepository(session=in_memory_db)

        repo.save_ohlcv("AAPL", "1d", sample_ohlcv_df, source="test")

        result = repo.get_ohlcv(
            symbol="AAPL",
            timeframe="1d",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 4, 10),
        )

        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns
