import pytest
from datetime import datetime
from src.domain.entities.trade import Trade, TradeSide, TradeStatus


class TestTradeSide:
    """Tests for TradeSide enum"""

    def test_trade_side_long(self):
        assert TradeSide.LONG.value == "LONG"

    def test_trade_side_short(self):
        assert TradeSide.SHORT.value == "SHORT"


class TestTradeStatus:
    """Tests for TradeStatus enum"""

    def test_trade_status_pending(self):
        assert TradeStatus.PENDING.value == "PENDING"

    def test_trade_status_open(self):
        assert TradeStatus.OPEN.value == "OPEN"

    def test_trade_status_closed(self):
        assert TradeStatus.CLOSED.value == "CLOSED"

    def test_trade_status_cancelled(self):
        assert TradeStatus.CANCELLED.value == "CANCELLED"


class TestTrade:
    """Tests for Trade dataclass"""

    def test_trade_creation_long(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.LONG,
        )

        assert trade.symbol == "AAPL"
        assert trade.entry_price == 100.0
        assert trade.quantity == 10
        assert trade.side == TradeSide.LONG
        assert trade.status == TradeStatus.OPEN
        assert trade.pnl is None  # No exit yet
        assert trade.pnl_pct is None

    def test_trade_creation_short(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.SHORT,
        )

        assert trade.symbol == "AAPL"
        assert trade.side == TradeSide.SHORT
        assert trade.status == TradeStatus.OPEN

    def test_trade_invalid_entry_price(self):
        with pytest.raises(ValueError, match="Entry price must be positive"):
            Trade(
                symbol="AAPL",
                entry_time=datetime(2023, 1, 1),
                entry_price=0.0,
                quantity=10,
                side=TradeSide.LONG,
            )

    def test_trade_invalid_quantity(self):
        with pytest.raises(ValueError, match="Quantity must be positive"):
            Trade(
                symbol="AAPL",
                entry_time=datetime(2023, 1, 1),
                entry_price=100.0,
                quantity=-5,
                side=TradeSide.LONG,
            )

    def test_trade_pnl_long_winning(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.LONG,
            exit_time=datetime(2023, 1, 5),
            exit_price=110.0,
            status=TradeStatus.CLOSED,
            commission=1.0,
            slippage=0.5,
        )

        # (110 - 100) * 10 - 1 - 0.5 = 98.5
        assert trade.pnl == 98.5
        assert trade.is_winning is True
        assert trade.is_closed is True

    def test_trade_pnl_long_losing(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.LONG,
            exit_time=datetime(2023, 1, 5),
            exit_price=90.0,
            status=TradeStatus.CLOSED,
            commission=1.0,
            slippage=0.5,
        )

        # (90 - 100) * 10 - 1 - 0.5 = -101.5
        assert trade.pnl == -101.5
        assert trade.is_winning is False

    def test_trade_pnl_short_winning(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.SHORT,
            exit_time=datetime(2023, 1, 5),
            exit_price=90.0,
            status=TradeStatus.CLOSED,
            commission=1.0,
            slippage=0.5,
        )

        # (100 - 90) * 10 - 1 - 0.5 = 98.5
        assert trade.pnl == 98.5
        assert trade.is_winning is True

    def test_trade_pnl_short_losing(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.SHORT,
            exit_time=datetime(2023, 1, 5),
            exit_price=110.0,
            status=TradeStatus.CLOSED,
            commission=1.0,
            slippage=0.5,
        )

        # (100 - 110) * 10 - 1 - 0.5 = -101.5
        assert trade.pnl == -101.5
        assert trade.is_winning is False

    def test_trade_pnl_pct_long(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.LONG,
            exit_time=datetime(2023, 1, 5),
            exit_price=110.0,
            status=TradeStatus.CLOSED,
        )

        # (110 - 100) / 100 * 100 = 10% (returns percentage)
        assert trade.pnl_pct == 10.0

    def test_trade_pnl_pct_short(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.SHORT,
            exit_time=datetime(2023, 1, 5),
            exit_price=90.0,
            status=TradeStatus.CLOSED,
        )

        # (100 - 90) / 100 * 100 = 10% (returns percentage)
        assert trade.pnl_pct == 10.0

    def test_trade_open_position(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.LONG,
        )

        assert trade.is_closed is False
        assert trade.is_open is True
        assert trade.status == TradeStatus.OPEN

    def test_trade_to_dict(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.LONG,
            exit_time=datetime(2023, 1, 5),
            exit_price=110.0,
            status=TradeStatus.CLOSED,
            commission=1.0,
            slippage=0.5,
        )

        d = trade.to_dict()

        assert d["symbol"] == "AAPL"
        assert d["entry_price"] == 100.0
        assert d["side"] == "LONG"
        assert d["status"] == "CLOSED"
        assert d["pnl"] == 98.5
        assert d["pnl_pct"] == 9.85

    def test_trade_close_method(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.LONG,
        )

        trade.close(exit_price=110.0, exit_time=datetime(2023, 1, 5))

        assert trade.exit_price == 110.0
        assert trade.status == TradeStatus.CLOSED
        assert trade.is_closed is True
        assert trade.pnl == 100.0  # (110-100) * 10

    def test_trade_trade_value(self):
        trade = Trade(
            symbol="AAPL",
            entry_time=datetime(2023, 1, 1),
            entry_price=100.0,
            quantity=10,
            side=TradeSide.LONG,
        )

        assert trade.trade_value == 1000.0
