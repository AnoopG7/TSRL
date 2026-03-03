import pytest
import pandas as pd
from datetime import datetime
from src.domain.entities.ohlcv import OHLCV


class TestOHLCV:
    """Tests for OHLCV dataclass"""

    def test_ohlcv_creation(self):
        ohlcv = OHLCV(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000000,
        )

        assert ohlcv.symbol == "AAPL"
        assert ohlcv.open == 100.0
        assert ohlcv.high == 105.0
        assert ohlcv.low == 98.0
        assert ohlcv.close == 103.0
        assert ohlcv.volume == 1000000

    def test_ohlcv_typical_price(self):
        ohlcv = OHLCV(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000000,
        )

        # (105 + 98 + 103) / 3 = 102.0
        assert ohlcv.typical_price == 102.0

    def test_ohlcv_range(self):
        ohlcv = OHLCV(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000000,
        )

        # 105 - 98 = 7.0
        assert ohlcv.range == 7.0

    def test_ohlcv_is_bullish_true(self):
        ohlcv = OHLCV(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000000,
        )

        assert ohlcv.is_bullish is True

    def test_ohlcv_is_bullish_false(self):
        ohlcv = OHLCV(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=103.0,
            high=105.0,
            low=98.0,
            close=100.0,
            volume=1000000,
        )

        assert ohlcv.is_bullish is False

    def test_ohlcv_is_bullish_neutral(self):
        ohlcv = OHLCV(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=98.0,
            close=100.0,
            volume=1000000,
        )

        assert ohlcv.is_bullish is True  # close == open

    def test_ohlcv_to_dict(self):
        ohlcv = OHLCV(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000000,
        )

        d = ohlcv.to_dict()

        assert d["symbol"] == "AAPL"
        assert d["open"] == 100.0
        assert d["high"] == 105.0
        assert d["low"] == 98.0
        assert d["close"] == 103.0
        assert d["volume"] == 1000000

    def test_ohlcv_from_dict(self):
        data = {
            "symbol": "AAPL",
            "timestamp": "2023-01-01",
            "open": 100.0,
            "high": 105.0,
            "low": 98.0,
            "close": 103.0,
            "volume": 1000000,
        }

        ohlcv = OHLCV.from_dict(data)

        assert ohlcv.symbol == "AAPL"
        assert ohlcv.open == 100.0
        assert ohlcv.high == 105.0
        assert ohlcv.low == 98.0
        assert ohlcv.close == 103.0

    def test_ohlcv_from_pandas_row(self):
        row = pd.Series(
            {
                "open": 100.0,
                "high": 105.0,
                "low": 98.0,
                "close": 103.0,
                "volume": 1000000,
            },
            name=datetime(2023, 1, 1),
        )

        ohlcv = OHLCV.from_pandas_row(row, "AAPL")

        assert ohlcv.symbol == "AAPL"
        assert ohlcv.open == 100.0
        assert ohlcv.close == 103.0
        assert ohlcv.volume == 1000000

    def test_ohlcv_immutable(self):
        ohlcv = OHLCV(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000000,
        )

        with pytest.raises(Exception):  # frozen dataclass
            ohlcv.close = 200.0

    def test_ohlcv_invalid_high_less_than_low(self):
        with pytest.raises(ValueError, match="High price cannot be less than low price"):
            OHLCV(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=95.0,
                low=98.0,
                close=103.0,
                volume=1000000,
            )

    def test_ohlcv_invalid_negative_volume(self):
        with pytest.raises(ValueError, match="Volume cannot be negative"):
            OHLCV(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=105.0,
                low=98.0,
                close=103.0,
                volume=-100,
            )

    def test_ohlcv_from_pandas_row_string_timestamp(self):
        row = pd.Series(
            {
                "open": 100.0,
                "high": 105.0,
                "low": 98.0,
                "close": 103.0,
                "volume": 1000000,
            },
            name="2023-01-01",
        )

        ohlcv = OHLCV.from_pandas_row(row, "AAPL")

        assert ohlcv.symbol == "AAPL"
        assert ohlcv.close == 103.0
