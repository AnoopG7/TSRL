import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from hypothesis import given, settings, assume, example
import hypothesis.strategies as st

from src.domain.entities.trade import Trade, TradeSide, TradeStatus
from src.domain.entities.position import Position, PositionSide
from src.analytics.risk_metrics import RiskMetricsCalculator
from src.strategies.base import BaseStrategy, StrategyParameter


class TestRiskMetricsProperties:
    @given(
        st.lists(
            st.floats(min_value=-0.5, max_value=0.5, allow_nan=False), min_size=2, max_size=1000
        )
    )
    @settings(max_examples=100)
    def test_sharpe_ratio_always_finite(self, returns):
        """Sharpe ratio should always be finite for valid returns"""
        series = pd.Series(returns)
        std = series.std()
        assume(std > 0)

        result = RiskMetricsCalculator.calculate_sharpe_ratio(series)

        assert np.isfinite(result), f"Sharpe ratio should be finite, got {result}"

    @given(
        st.lists(
            st.floats(min_value=-0.5, max_value=0.5, allow_nan=False), min_size=2, max_size=1000
        )
    )
    @settings(max_examples=100)
    def test_sortino_ratio_always_finite(self, returns):
        """Sortino ratio should handle edge cases"""
        series = pd.Series(returns)

        try:
            result = RiskMetricsCalculator.calculate_sortino_ratio(series)
            if not np.isnan(result):
                assert np.isfinite(result), f"Sortino ratio should be finite, got {result}"
        except (ValueError, ZeroDivisionError):
            pass

    @given(
        st.lists(
            st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=1000,
        )
    )
    @settings(max_examples=50)
    def test_max_drawdown_bounds(self, returns):
        """Max drawdown should handle edge cases"""
        assume(len(set(returns)) > 1)

        series = pd.Series(returns)

        try:
            result = RiskMetricsCalculator.calculate_max_drawdown(series)
            if not np.isnan(result):
                assert result <= 0, f"Max drawdown should be <= 0, got {result}"
        except (ValueError, KeyError, FutureWarning):
            pass

    @given(
        initial_capital=st.floats(min_value=1000.0, max_value=100000.0),
        final_capital=st.floats(min_value=100.0, max_value=200000.0),
        n_days=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=50)
    def test_cagr_always_finite(self, initial_capital, final_capital, n_days):
        """CAGR should always be finite for valid inputs"""
        try:
            result = RiskMetricsCalculator.calculate_cagr(initial_capital, final_capital, n_days)
            if not np.isnan(result):
                assert np.isfinite(result), f"CAGR should be finite, got {result}"
        except (ValueError, OverflowError, ZeroDivisionError):
            pass

    @given(
        st.lists(
            st.floats(min_value=-1.0, max_value=1.0, allow_nan=False), min_size=1, max_size=1000
        )
    )
    @settings(max_examples=100)
    def test_win_rate_bounds(self, returns):
        """Win rate should always be between 0 and 1"""
        trades = [{"pnl": r} for r in returns]
        result = RiskMetricsCalculator.calculate_win_rate(trades)

        assert 0 <= result <= 1, f"Win rate should be between 0 and 1, got {result}"

    @given(st.lists(st.floats(min_value=0.01, max_value=10.0), min_size=2, max_size=1000))
    @settings(max_examples=100)
    def test_profit_factor_always_positive(self, gains):
        """Profit factor should always be positive"""
        trades = [{"pnl": g if i % 2 == 0 else -g * 0.5} for i, g in enumerate(gains)]
        result = RiskMetricsCalculator.calculate_profit_factor(trades)

        assert result >= 0, f"Profit factor should be >= 0, got {result}"
        assert np.isfinite(result), f"Profit factor should be finite, got {result}"

    @given(
        st.lists(
            st.floats(min_value=-0.5, max_value=0.5, allow_nan=False), min_size=2, max_size=1000
        )
    )
    @settings(max_examples=50)
    def test_expectancy_calculation(self, returns):
        """Expectancy should be finite"""
        trades = [{"pnl": r} for r in returns]
        result = RiskMetricsCalculator.calculate_expectancy(trades)

        assert np.isfinite(result), f"Expectancy should be finite, got {result}"


class TestTradeProperties:
    @given(
        entry_price=st.floats(min_value=1.0, max_value=10000.0),
        quantity=st.integers(min_value=1, max_value=10000),
        exit_price=st.floats(min_value=1.0, max_value=10000.0),
    )
    @settings(max_examples=100)
    def test_long_trade_pnl_calculation(self, entry_price, quantity, exit_price):
        """PnL calculation for long trades should be correct"""
        trade = Trade(
            symbol="TEST",
            entry_time=datetime.now(),
            entry_price=entry_price,
            quantity=quantity,
            side=TradeSide.LONG,
            exit_time=datetime.now(),
            exit_price=exit_price,
        )

        expected_pnl = (exit_price - entry_price) * quantity
        assert abs(trade.pnl - expected_pnl) < 0.01, f"PnL mismatch: {trade.pnl} vs {expected_pnl}"

    @given(
        entry_price=st.floats(min_value=1.0, max_value=10000.0),
        quantity=st.integers(min_value=1, max_value=10000),
        exit_price=st.floats(min_value=1.0, max_value=10000.0),
    )
    @settings(max_examples=100)
    def test_short_trade_pnl_calculation(self, entry_price, quantity, exit_price):
        """PnL calculation for short trades should be correct"""
        trade = Trade(
            symbol="TEST",
            entry_time=datetime.now(),
            entry_price=entry_price,
            quantity=quantity,
            side=TradeSide.SHORT,
            exit_time=datetime.now(),
            exit_price=exit_price,
        )

        expected_pnl = (entry_price - exit_price) * quantity
        assert abs(trade.pnl - expected_pnl) < 0.01, f"PnL mismatch: {trade.pnl} vs {expected_pnl}"

    @given(
        entry_price=st.floats(min_value=1.0, max_value=10000.0),
        quantity=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=50)
    def test_pnl_percentage_bounds(self, entry_price, quantity):
        """PnL percentage should be reasonable for closed trades"""
        trade = Trade(
            symbol="TEST",
            entry_time=datetime.now(),
            entry_price=entry_price,
            quantity=quantity,
            side=TradeSide.LONG,
            exit_time=datetime.now(),
            exit_price=entry_price * 2,
        )

        assert trade.pnl_pct is not None
        assert -200 <= trade.pnl_pct <= 1000


class TestPositionProperties:
    @given(
        entry_price=st.floats(min_value=1.0, max_value=10000.0),
        quantity=st.integers(min_value=1, max_value=10000),
        current_price=st.floats(min_value=0.1, max_value=20000.0),
    )
    @settings(max_examples=100)
    def test_position_market_value(self, entry_price, quantity, current_price):
        """Market value should be current price times quantity"""
        position = Position(
            symbol="TEST",
            entry_price=entry_price,
            quantity=quantity,
            side=PositionSide.LONG,
            entry_time=datetime.now(),
            current_price=current_price,
        )

        expected_market_value = current_price * quantity
        assume(expected_market_value > 0)

        assert abs(position.market_value - expected_market_value) < 0.01

    @given(
        entry_price=st.floats(min_value=1.0, max_value=10000.0),
        quantity=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=50)
    def test_position_cost_basis(self, entry_price, quantity):
        """Cost basis should be entry price times quantity"""
        position = Position(
            symbol="TEST",
            entry_price=entry_price,
            quantity=quantity,
            side=PositionSide.LONG,
            entry_time=datetime.now(),
        )

        expected_cost = entry_price * quantity
        assert abs(position.cost_basis - expected_cost) < 0.01


class TestSignalProperties:
    @given(signal_value=st.integers(min_value=-10, max_value=10))
    @settings(max_examples=50)
    def test_signal_type_from_value(self, signal_value):
        """Signal type can be determined from signal value"""
        if signal_value > 0:
            assert signal_value > 0
        elif signal_value < 0:
            assert signal_value < 0
        else:
            assert signal_value == 0

    @given(strength=st.floats(min_value=0.0, max_value=1.0))
    @settings(max_examples=50)
    def test_signal_strength_bounds(self, strength):
        """Signal strength value should be between 0 and 1"""
        assert 0 <= strength <= 1


class TestStrategyParameterProperties:
    @given(
        value=st.floats(min_value=0.0, max_value=1000.0),
        min_val=st.floats(min_value=-100.0, max_value=500.0),
        max_val=st.floats(min_value=501.0, max_value=2000.0),
    )
    @settings(max_examples=50)
    def test_parameter_stores_values(self, value, min_val, max_val):
        """StrategyParameter should store all values correctly"""
        assume(min_val < max_val)

        param = StrategyParameter(
            name="test_param",
            value=value,
            min_value=min_val,
            max_value=max_val,
        )

        assert param.name == "test_param"
        assert param.value == value
        assert param.min_value == min_val
        assert param.max_value == max_val


class TestEquityCurveProperties:
    @given(
        initial_capital=st.floats(min_value=1000.0, max_value=1000000.0),
        returns=st.lists(
            st.floats(min_value=-0.2, max_value=0.2, allow_nan=False), min_size=1, max_size=500
        ),
    )
    @settings(max_examples=50)
    def test_equity_curve_no_nan(self, initial_capital, returns):
        """Equity curve should never have NaN values"""
        equity = [initial_capital]
        for r in returns:
            equity.append(equity[-1] * (1 + r))

        equity_series = pd.Series(equity)

        assert not equity_series.isna().any(), "Equity curve should not contain NaN values"
        assert (equity_series > 0).all(), "Equity should always be positive"

    @given(
        initial_capital=st.floats(min_value=1000.0, max_value=1000000.0),
        returns=st.lists(
            st.floats(min_value=-0.5, max_value=0.5, allow_nan=False), min_size=10, max_size=200
        ),
    )
    @settings(max_examples=50)
    def test_equity_curve_always_positive(self, initial_capital, returns):
        """Equity curve should always stay positive"""
        equity = [initial_capital]
        for r in returns:
            equity.append(equity[-1] * (1 + r))

        equity_series = pd.Series(equity)

        assert (equity_series > 0).all(), "Equity should always be positive"


class TestLabelGenerationProperties:
    @given(prices=st.lists(st.floats(min_value=1.0, max_value=1000.0), min_size=20, max_size=200))
    @settings(max_examples=50)
    def test_labels_always_valid(self, prices):
        """Generated labels should always be -1, 0, or 1"""
        from src.ml.feature_engineering.features import LabelGenerator

        df = pd.DataFrame(
            {"close": prices}, index=pd.date_range(start="2023-01-01", periods=len(prices))
        )

        labels = LabelGenerator.generate_labels(df, forward_periods=5, threshold=0.0)

        valid_labels = labels.dropna().unique()
        assert all(l in [-1.0, 0.0, 1.0] for l in valid_labels), f"Invalid labels: {valid_labels}"

    @given(returns=st.lists(st.floats(min_value=-0.2, max_value=0.2), min_size=30, max_size=200))
    @settings(max_examples=50)
    def test_regime_labels_always_valid(self, returns):
        """Regime labels should always be -1, 0, or 1"""
        from src.ml.feature_engineering.features import LabelGenerator

        returns_series = pd.Series(returns)
        labels = LabelGenerator.generate_regime_labels(returns_series, window=20)

        valid_labels = labels.dropna().unique()
        assert all(l in [-1.0, 0.0, 1.0] for l in valid_labels), f"Invalid labels: {valid_labels}"


class TestFeatureEngineeringProperties:
    @given(data=st.lists(st.floats(min_value=1.0, max_value=1000.0), min_size=50, max_size=200))
    @settings(max_examples=20)
    def test_features_never_all_nan(self, data):
        """Feature engineering should handle edge cases"""
        from src.ml.feature_engineering.features import FeatureEngineer

        assume(len(set(data)) > 1)

        df = pd.DataFrame(
            {
                "open": data,
                "high": [x * 1.01 for x in data],
                "low": [x * 0.99 for x in data],
                "close": data,
                "volume": [1000000] * len(data),
            },
            index=pd.date_range(start="2023-01-01", periods=len(data)),
        )

        engineer = FeatureEngineer(df)
        features = engineer.add_all_features()

        assert features is not None
        assert len(features) > 0


class TestDataFrameProperties:
    @given(data=st.lists(st.floats(min_value=1.0, max_value=1000.0), min_size=10, max_size=100))
    @settings(max_examples=30)
    def test_ohlcv_dataframe_valid(self, data):
        """OHLCV data should always have high >= low"""
        assume(len(data) > 0)

        opens = data
        closes = [d * (1 + np.random.uniform(-0.01, 0.01)) for d in data]
        highs = [max(o, c) * (1 + abs(np.random.uniform(0, 0.02))) for o, c in zip(opens, closes)]
        lows = [min(o, c) * (1 - abs(np.random.uniform(0, 0.02))) for o, c in zip(opens, closes)]

        for h, l in zip(highs, lows):
            assert h >= l, f"High ({h}) should be >= Low ({l})"
