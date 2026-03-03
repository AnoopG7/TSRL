import pytest
from datetime import datetime
from src.domain.entities.signal import Signal, SignalType, SignalStrength


class TestSignalType:
    """Tests for SignalType enum"""

    def test_signal_type_buy(self):
        assert SignalType.BUY.value == "BUY"

    def test_signal_type_sell(self):
        assert SignalType.SELL.value == "SELL"

    def test_signal_type_close_long(self):
        assert SignalType.CLOSE_LONG.value == "CLOSE_LONG"

    def test_signal_type_close_short(self):
        assert SignalType.CLOSE_SHORT.value == "CLOSE_SHORT"

    def test_signal_type_neutral(self):
        assert SignalType.NEUTRAL.value == "NEUTRAL"


class TestSignalStrength:
    """Tests for SignalStrength enum"""

    def test_signal_strength_strong_buy(self):
        assert SignalStrength.STRONG_BUY == 1.0

    def test_signal_strength_buy(self):
        assert SignalStrength.BUY == 0.75

    def test_signal_strength_slight_buy(self):
        assert SignalStrength.SLIGHT_BUY == 0.5

    def test_signal_strength_neutral(self):
        assert SignalStrength.NEUTRAL == 0.0

    def test_signal_strength_slight_sell(self):
        assert SignalStrength.SLIGHT_SELL == -0.5

    def test_signal_strength_sell(self):
        assert SignalStrength.SELL == -0.75

    def test_signal_strength_strong_sell(self):
        assert SignalStrength.STRONG_SELL == -1.0


class TestSignal:
    """Tests for Signal dataclass"""

    def test_signal_creation_buy(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.BUY,
            strength=1.0,
            price=100.0,
        )

        assert signal.symbol == "AAPL"
        assert signal.signal_type == SignalType.BUY
        assert signal.strength == 1.0
        assert signal.price == 100.0

    def test_signal_creation_sell(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.SELL,
            strength=-1.0,
            price=100.0,
        )

        assert signal.signal_type == SignalType.SELL
        assert signal.strength == -1.0

    def test_signal_is_buy_true_for_buy(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.BUY,
            strength=1.0,
            price=100.0,
        )

        assert signal.is_buy is True

    def test_signal_is_buy_true_for_close_short(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.CLOSE_SHORT,
            strength=1.0,
            price=100.0,
        )

        assert signal.is_buy is True

    def test_signal_is_buy_false_for_sell(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.SELL,
            strength=-1.0,
            price=100.0,
        )

        assert signal.is_buy is False

    def test_signal_is_sell_true_for_sell(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.SELL,
            strength=-1.0,
            price=100.0,
        )

        assert signal.is_sell is True

    def test_signal_is_sell_true_for_close_long(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.CLOSE_LONG,
            strength=-1.0,
            price=100.0,
        )

        assert signal.is_sell is True

    def test_signal_is_sell_false_for_buy(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.BUY,
            strength=1.0,
            price=100.0,
        )

        assert signal.is_sell is False

    def test_signal_is_entry_true_for_buy(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.BUY,
            strength=1.0,
            price=100.0,
        )

        assert signal.is_entry is True

    def test_signal_is_entry_true_for_sell(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.SELL,
            strength=-1.0,
            price=100.0,
        )

        assert signal.is_entry is True

    def test_signal_is_entry_false_for_close_long(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.CLOSE_LONG,
            strength=-1.0,
            price=100.0,
        )

        assert signal.is_entry is False

    def test_signal_is_exit_true_for_close_long(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.CLOSE_LONG,
            strength=-1.0,
            price=100.0,
        )

        assert signal.is_exit is True

    def test_signal_is_exit_true_for_close_short(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.CLOSE_SHORT,
            strength=1.0,
            price=100.0,
        )

        assert signal.is_exit is True

    def test_signal_is_exit_false_for_buy(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.BUY,
            strength=1.0,
            price=100.0,
        )

        assert signal.is_exit is False

    def test_signal_invalid_strength_too_high(self):
        with pytest.raises(ValueError, match="Signal strength must be between -1.0 and 1.0"):
            Signal(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                signal_type=SignalType.BUY,
                strength=1.5,
                price=100.0,
            )

    def test_signal_invalid_strength_too_low(self):
        with pytest.raises(ValueError, match="Signal strength must be between -1.0 and 1.0"):
            Signal(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                signal_type=SignalType.BUY,
                strength=-1.5,
                price=100.0,
            )

    def test_signal_invalid_price_zero(self):
        with pytest.raises(ValueError, match="Signal price must be positive"):
            Signal(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                signal_type=SignalType.BUY,
                strength=1.0,
                price=0.0,
            )

    def test_signal_invalid_price_negative(self):
        with pytest.raises(ValueError, match="Signal price must be positive"):
            Signal(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                signal_type=SignalType.BUY,
                strength=1.0,
                price=-100.0,
            )

    def test_signal_create_buy(self):
        signal = Signal.create_buy("AAPL", datetime(2023, 1, 1), 100.0)

        assert signal.signal_type == SignalType.BUY
        assert signal.strength == 1.0
        assert signal.price == 100.0

    def test_signal_create_sell(self):
        signal = Signal.create_sell("AAPL", datetime(2023, 1, 1), 100.0)

        assert signal.signal_type == SignalType.SELL
        assert signal.strength == 1.0
        assert signal.price == 100.0

    def test_signal_to_dict(self):
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            signal_type=SignalType.BUY,
            strength=1.0,
            price=100.0,
        )

        d = signal.to_dict()

        assert d["symbol"] == "AAPL"
        assert d["signal_type"] == "BUY"
        assert d["strength"] == 1.0
        assert d["price"] == 100.0
