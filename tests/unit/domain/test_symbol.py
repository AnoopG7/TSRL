import pytest
from src.domain.value_objects.symbol import Symbol, Timeframe


class TestTimeframe:
    """Tests for Timeframe enum"""

    def test_timeframe_minute_1(self):
        assert Timeframe.MINUTE_1.value == "1m"
        assert Timeframe.MINUTE_1.minutes == 1

    def test_timeframe_minute_5(self):
        assert Timeframe.MINUTE_5.value == "5m"
        assert Timeframe.MINUTE_5.minutes == 5

    def test_timeframe_minute_15(self):
        assert Timeframe.MINUTE_15.value == "15m"
        assert Timeframe.MINUTE_15.minutes == 15

    def test_timeframe_minute_30(self):
        assert Timeframe.MINUTE_30.value == "30m"
        assert Timeframe.MINUTE_30.minutes == 30

    def test_timeframe_hour_1(self):
        assert Timeframe.HOUR_1.value == "1h"
        assert Timeframe.HOUR_1.minutes == 60

    def test_timeframe_hour_4(self):
        assert Timeframe.HOUR_4.value == "4h"
        assert Timeframe.HOUR_4.minutes == 240

    def test_timeframe_daily(self):
        assert Timeframe.DAILY.value == "1d"
        assert Timeframe.DAILY.minutes == 1440

    def test_timeframe_weekly(self):
        assert Timeframe.WEEKLY.value == "1w"
        assert Timeframe.WEEKLY.minutes == 10080

    def test_timeframe_monthly(self):
        assert Timeframe.MONTHLY.value == "1mo"
        assert Timeframe.MONTHLY.minutes == 43200

    def test_timeframe_pandas_freq(self):
        assert Timeframe.DAILY.pandas_freq == "1d"
        assert Timeframe.HOUR_1.pandas_freq == "1h"

    def test_timeframe_from_minutes(self):
        assert Timeframe.from_minutes(1) == Timeframe.MINUTE_1
        assert Timeframe.from_minutes(60) == Timeframe.HOUR_1
        assert Timeframe.from_minutes(1440) == Timeframe.DAILY

    def test_timeframe_from_minutes_unknown(self):
        assert Timeframe.from_minutes(999) == Timeframe.DAILY  # default


class TestSymbol:
    """Tests for Symbol value object"""

    def test_symbol_creation_basic(self):
        symbol = Symbol(ticker="AAPL")

        assert symbol.ticker == "AAPL"
        assert symbol.currency == "USD"

    def test_symbol_creation_full(self):
        symbol = Symbol(ticker="AAPL", name="Apple Inc", exchange="NASDAQ", currency="USD")

        assert symbol.ticker == "AAPL"
        assert symbol.name == "Apple Inc"
        assert symbol.exchange == "NASDAQ"
        assert symbol.currency == "USD"

    def test_symbol_empty_ticker_raises(self):
        with pytest.raises(ValueError, match="Ticker cannot be empty"):
            Symbol(ticker="")

    def test_symbol_str_without_exchange(self):
        symbol = Symbol(ticker="AAPL")
        assert str(symbol) == "AAPL"

    def test_symbol_str_with_exchange(self):
        symbol = Symbol(ticker="AAPL", exchange="NASDAQ")
        assert str(symbol) == "AAPL.NASDAQ"

    def test_symbol_full_ticker(self):
        symbol = Symbol(ticker="AAPL", exchange="NASDAQ")
        assert symbol.full_ticker == "AAPL.NASDAQ"

    def test_symbol_yahoo_ticker_default(self):
        symbol = Symbol(ticker="AAPL")
        assert symbol.yahoo_ticker == "AAPL"

    def test_symbol_yahoo_ticker_nse(self):
        symbol = Symbol(ticker="RELIANCE", exchange="NS")
        assert symbol.yahoo_ticker == "RELIANCE.NS"

    def test_symbol_yahoo_ticker_bse(self):
        symbol = Symbol(ticker="SBIN", exchange="BO")
        assert symbol.yahoo_ticker == "SBIN.BO"

    def test_symbol_immutable(self):
        symbol = Symbol(ticker="AAPL")
        with pytest.raises(Exception):  # frozen dataclass
            symbol.ticker = "GOOG"
