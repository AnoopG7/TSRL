import pytest
from datetime import datetime
from src.domain.entities.position import Position, PositionSide


class TestPositionSide:
    """Tests for PositionSide enum"""

    def test_position_side_long(self):
        assert PositionSide.LONG.value == "LONG"

    def test_position_side_short(self):
        assert PositionSide.SHORT.value == "SHORT"


class TestPosition:
    """Tests for Position dataclass"""

    def test_position_creation_long(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
        )

        assert position.symbol == "AAPL"
        assert position.entry_price == 100.0
        assert position.quantity == 10
        assert position.side == PositionSide.LONG

    def test_position_market_value(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
        )

        assert position.market_value == 1000.0

    def test_position_cost_basis(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
        )

        assert position.cost_basis == 1000.0

    def test_position_unrealized_pnl_long_profit(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
            current_price=110.0,
        )

        assert position.unrealized_pnl == 100.0

    def test_position_unrealized_pnl_long_loss(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
            current_price=90.0,
        )

        assert position.unrealized_pnl == -100.0

    def test_position_unrealized_pnl_short_profit(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.SHORT,
            entry_time=datetime(2023, 1, 1),
            current_price=90.0,
        )

        assert position.unrealized_pnl == 100.0

    def test_position_unrealized_pnl_short_loss(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.SHORT,
            entry_time=datetime(2023, 1, 1),
            current_price=110.0,
        )

        assert position.unrealized_pnl == -100.0

    def test_position_unrealized_pnl_pct_long(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
            current_price=110.0,
        )

        assert position.unrealized_pnl_pct == 10.0

    def test_position_unrealized_pnl_pct_short(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.SHORT,
            entry_time=datetime(2023, 1, 1),
            current_price=90.0,
        )

        assert position.unrealized_pnl_pct == 10.0

    def test_position_unrealized_pnl_none_without_price(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
        )

        assert position.unrealized_pnl is None
        assert position.unrealized_pnl_pct is None

    def test_position_update_price(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
        )

        position.update_price(110.0)

        assert position.current_price == 110.0
        assert position.unrealized_pnl == 100.0

    def test_position_is_profitable_none_price(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
        )

        assert position.is_profitable is None

    def test_position_is_profitable_profitable(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
            current_price=110.0,
        )

        assert position.is_profitable is True

    def test_position_is_profitable_not_profitable(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
            current_price=90.0,
        )

        assert position.is_profitable is False

    def test_position_to_dict(self):
        position = Position(
            symbol="AAPL",
            entry_price=100.0,
            quantity=10,
            side=PositionSide.LONG,
            entry_time=datetime(2023, 1, 1),
            current_price=110.0,
        )

        d = position.to_dict()

        assert d["symbol"] == "AAPL"
        assert d["entry_price"] == 100.0
        assert d["quantity"] == 10
        assert d["side"] == "LONG"
        assert d["current_price"] == 110.0
        assert d["unrealized_pnl"] == 100.0

    def test_position_invalid_entry_price(self):
        with pytest.raises(ValueError, match="Entry price must be positive"):
            Position(
                symbol="AAPL",
                entry_price=0.0,
                quantity=10,
                side=PositionSide.LONG,
                entry_time=datetime(2023, 1, 1),
            )

    def test_position_invalid_quantity(self):
        with pytest.raises(ValueError, match="Quantity must be positive"):
            Position(
                symbol="AAPL",
                entry_price=100.0,
                quantity=-5,
                side=PositionSide.LONG,
                entry_time=datetime(2023, 1, 1),
            )
