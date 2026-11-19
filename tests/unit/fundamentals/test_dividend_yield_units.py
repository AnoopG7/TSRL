"""yfinance reports dividendYield in percent; the app stores every ratio as a fraction."""

from src.infrastructure.data_providers.fundamental_provider import YFinanceFundamentalProvider

normalise = YFinanceFundamentalProvider._normalise_info


def test_prefers_rate_over_price():
    info = normalise({"dividendYield": 0.31, "dividendRate": 1.08, "currentPrice": 360.0})
    assert abs(info["dividendYield"] - 0.003) < 1e-9


def test_falls_back_to_trailing_yield():
    info = normalise({"dividendYield": 0.31, "trailingAnnualDividendYield": 0.0030})
    assert info["dividendYield"] == 0.0030


def test_converts_percent_when_nothing_else_available():
    info = normalise({"dividendYield": 2.5})
    assert abs(info["dividendYield"] - 0.025) < 1e-12


def test_leaves_missing_yield_alone():
    assert normalise({"shortName": "X"}).get("dividendYield") is None


def test_does_not_mutate_input():
    raw = {"dividendYield": 0.31}
    normalise(raw)
    assert raw["dividendYield"] == 0.31
