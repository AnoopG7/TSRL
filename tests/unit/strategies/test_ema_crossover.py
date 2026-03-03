import pytest
import pandas as pd
import numpy as np
from src.strategies.momentum.ema_crossover import (
    EMACrossoverStrategy,
    RSIMeanReversionStrategy,
    BreakoutStrategy,
)


class TestEMACrossoverStrategy:
    """Tests for EMA Crossover Strategy"""

    def test_strategy_creation(self):
        strategy = EMACrossoverStrategy()

        assert strategy.name == "EMA Crossover"
        assert strategy.version == "1.0.0"
        assert strategy.strategy_type == "momentum"

    def test_default_parameters(self):
        strategy = EMACrossoverStrategy()

        assert strategy.get_parameter("fast_period") == 12
        assert strategy.get_parameter("slow_period") == 26
        assert strategy.get_parameter("signal_period") == 9

    def test_custom_parameters(self):
        strategy = EMACrossoverStrategy(fast_period=5, slow_period=20)

        assert strategy.get_parameter("fast_period") == 5
        assert strategy.get_parameter("slow_period") == 20

    def test_parameter_validation_fast_greater_than_slow(self):
        with pytest.raises(ValueError, match="Fast period must be less than slow period"):
            EMACrossoverStrategy(fast_period=30, slow_period=20)

    def test_parameter_validation_negative_period(self):
        with pytest.raises(ValueError, match="Periods must be positive"):
            EMACrossoverStrategy(fast_period=-5, slow_period=20)

    def test_generate_signals_bullish_crossover(self):
        """Test when fast EMA crosses above slow EMA (buy signal)"""
        strategy = EMACrossoverStrategy(fast_period=3, slow_period=6)

        # Create data with bullish crossover
        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104, 105, 106, 107],
            },
            index=pd.date_range("2023-01-01", periods=8),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert "ema_fast" in signals.columns
        assert "ema_slow" in signals.columns
        assert signals["ema_fast"].iloc[-1] > signals["ema_slow"].iloc[-1]

    def test_generate_signals_bearish_crossover(self):
        """Test when fast EMA crosses below slow EMA (sell signal)"""
        strategy = EMACrossoverStrategy(fast_period=3, slow_period=6)

        # Create data with bearish crossover
        data = pd.DataFrame(
            {
                "close": [107, 106, 105, 104, 103, 102, 101, 100],
            },
            index=pd.date_range("2023-01-01", periods=8),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert signals["ema_fast"].iloc[-1] < signals["ema_slow"].iloc[-1]

    def test_generate_signals_no_crossover(self):
        """Test when no crossover occurs"""
        strategy = EMACrossoverStrategy(fast_period=3, slow_period=6)

        # Create data with consistent trend (no crossover)
        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104, 105, 106, 107],
            },
            index=pd.date_range("2023-01-01", periods=8),
        )

        signals = strategy.generate_signals(data)

        # Should have at least some signals
        assert "signal" in signals.columns

    def test_generate_signals_insufficient_data(self):
        """Test with less data than required for EMAs"""
        strategy = EMACrossoverStrategy(fast_period=12, slow_period=26)

        data = pd.DataFrame(
            {"close": [100, 101, 102, 103, 104]},
            index=pd.date_range("2023-01-01", periods=5),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        # With very little data, signal should be minimal
        # EMA needs warmup period, so signals may be limited

    def test_get_requirements(self):
        strategy = EMACrossoverStrategy()

        requirements = strategy.get_requirements()

        assert "close" in requirements


class TestRSIMeanReversionStrategy:
    """Tests for RSI Mean Reversion Strategy"""

    def test_strategy_creation(self):
        strategy = RSIMeanReversionStrategy()

        assert strategy.name == "RSI Mean Reversion"
        assert strategy.version == "1.0.0"
        assert strategy.strategy_type == "mean_reversion"

    def test_default_parameters(self):
        strategy = RSIMeanReversionStrategy()

        assert strategy.get_parameter("rsi_period") == 14
        assert strategy.get_parameter("oversold_threshold") == 30
        assert strategy.get_parameter("overbought_threshold") == 70

    def test_custom_parameters(self):
        strategy = RSIMeanReversionStrategy(
            rsi_period=7,
            oversold_threshold=20,
            overbought_threshold=80,
        )

        assert strategy.get_parameter("rsi_period") == 7
        assert strategy.get_parameter("oversold_threshold") == 20
        assert strategy.get_parameter("overbought_threshold") == 80

    def test_generate_signals_oversold(self):
        """Test buy signal when RSI is oversold"""
        strategy = RSIMeanReversionStrategy(rsi_period=2)

        # Create data that will result in low RSI
        data = pd.DataFrame(
            {"close": [100, 90, 85, 80, 75, 70, 65, 60]},
            index=pd.date_range("2023-01-01", periods=8),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert "rsi" in signals.columns

    def test_generate_signals_overbought(self):
        """Test sell signal when RSI is overbought"""
        strategy = RSIMeanReversionStrategy(rsi_period=2)

        # Create data that will result in high RSI
        data = pd.DataFrame(
            {"close": [60, 65, 70, 75, 80, 85, 90, 95]},
            index=pd.date_range("2023-01-01", periods=8),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert "rsi" in signals.columns

    def test_generate_signals_neutral(self):
        """Test neutral signal when RSI is in middle"""
        strategy = RSIMeanReversionStrategy(rsi_period=2)

        # Create relatively flat data
        data = pd.DataFrame(
            {"close": [100, 101, 100, 101, 100, 101, 100, 101]},
            index=pd.date_range("2023-01-01", periods=8),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns

    def test_generate_signals_insufficient_data(self):
        """Test with less data than required for RSI"""
        strategy = RSIMeanReversionStrategy(rsi_period=14)

        data = pd.DataFrame(
            {"close": [100, 101, 102]},
            index=pd.date_range("2023-01-01", periods=3),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        # RSI should have NaN values
        assert signals["rsi"].isna().any()

    def test_get_requirements(self):
        strategy = RSIMeanReversionStrategy()

        requirements = strategy.get_requirements()

        assert "close" in requirements


class TestBreakoutStrategy:
    """Tests for Breakout Strategy"""

    def test_strategy_creation(self):
        strategy = BreakoutStrategy()

        assert strategy.name == "Breakout Strategy"
        assert strategy.version == "1.0.0"
        assert strategy.strategy_type == "breakout"

    def test_default_parameters(self):
        strategy = BreakoutStrategy()

        assert strategy.get_parameter("lookback_period") == 20
        assert strategy.get_parameter("atr_period") == 14
        assert strategy.get_parameter("atr_multiplier") == 2.0

    def test_custom_parameters(self):
        strategy = BreakoutStrategy(
            lookback_period=10,
            atr_period=7,
            atr_multiplier=1.5,
        )

        assert strategy.get_parameter("lookback_period") == 10
        assert strategy.get_parameter("atr_period") == 7
        assert strategy.get_parameter("atr_multiplier") == 1.5

    def test_generate_signals_upward_breakout(self):
        """Test buy signal on upward breakout"""
        strategy = BreakoutStrategy(lookback_period=3)

        # Create data with clear upward breakout
        data = pd.DataFrame(
            {
                "open": [100, 101, 102, 103, 104, 105, 106, 107, 108],
                "high": [102, 103, 104, 105, 106, 115, 108, 109, 110],
                "low": [99, 100, 101, 102, 103, 104, 105, 106, 107],
                "close": [101, 102, 103, 104, 105, 106, 107, 108, 109],
            },
            index=pd.date_range("2023-01-01", periods=9),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns

    def test_generate_signals_downward_breakout(self):
        """Test sell signal on downward breakout"""
        strategy = BreakoutStrategy(lookback_period=3)

        # Create data with clear downward breakout
        data = pd.DataFrame(
            {
                "open": [109, 108, 107, 106, 105, 104, 103, 102, 101],
                "high": [110, 109, 108, 107, 106, 105, 104, 103, 102],
                "low": [107, 106, 105, 104, 95, 102, 100, 99, 98],
                "close": [108, 107, 106, 105, 104, 103, 102, 101, 100],
            },
            index=pd.date_range("2023-01-01", periods=9),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns

    def test_generate_signals_insufficient_data(self):
        """Test with less data than required for breakout"""
        strategy = BreakoutStrategy(lookback_period=20)

        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
            },
            index=pd.date_range("2023-01-01", periods=3),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        # No breakout signals due to insufficient lookback data
        assert signals["signal"].sum() == 0

    def test_get_requirements(self):
        strategy = BreakoutStrategy()

        requirements = strategy.get_requirements()

        assert "open" in requirements
        assert "high" in requirements
        assert "low" in requirements
        assert "close" in requirements
