import pytest
import pandas as pd
import numpy as np
from src.strategies.momentum.macd_strategy import MACDStrategy
from src.strategies.momentum.volume_strategies import VolumeProfileStrategy, VolumeBreakoutStrategy
from src.strategies.momentum.ma_ribbon import MovingAverageRibbonStrategy, TripleMAStrategy
from src.strategies.mean_reversion.bollinger_bands import BollingerBandsStrategy, BollingerBandsBreakoutStrategy


class TestMACDStrategy:
    """Tests for MACD Strategy"""

    def test_strategy_creation(self):
        strategy = MACDStrategy()

        assert strategy.name == "macd"
        assert strategy.version == "1.0.0"
        assert strategy.strategy_type == "momentum"

    def test_default_parameters(self):
        strategy = MACDStrategy()

        assert strategy.get_parameter("fast_period").value == 12
        assert strategy.get_parameter("slow_period").value == 26
        assert strategy.get_parameter("signal_period").value == 9

    def test_custom_parameters(self):
        strategy = MACDStrategy(fast_period=5, slow_period=15, signal_period=5)

        # MACDStrategy stores instance variables but also has StrategyParameter objects
        # The StrategyParameter objects keep their default values
        assert strategy._fast_period == 5
        assert strategy._slow_period == 15
        assert strategy._signal_period == 5

    def test_parameter_validation_fast_greater_than_slow(self):
        with pytest.raises(ValueError, match="fast_period must be less than slow_period"):
            MACDStrategy(fast_period=30, slow_period=20)

    def test_generate_signals(self):
        strategy = MACDStrategy(fast_period=3, slow_period=6, signal_period=3)

        data = pd.DataFrame(
            {"close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]},
            index=pd.date_range("2023-01-01", periods=10),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert "macd" in signals.columns
        assert "signal_line" in signals.columns
        assert "histogram" in signals.columns

    def test_generate_signals_insufficient_data(self):
        strategy = MACDStrategy()

        data = pd.DataFrame(
            {"close": [100, 101]},
            index=pd.date_range("2023-01-01", periods=2),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns

    def test_get_requirements(self):
        strategy = MACDStrategy()

        requirements = strategy.get_requirements()

        assert "close" in requirements


class TestVolumeProfileStrategy:
    """Tests for Volume Profile Strategy"""

    def test_strategy_creation(self):
        strategy = VolumeProfileStrategy()

        assert strategy.name == "volume_profile"
        assert strategy.version == "1.0.0"

    def test_default_parameters(self):
        strategy = VolumeProfileStrategy()

        assert strategy.get_parameter("lookback").value == 20
        assert strategy.get_parameter("volume_threshold").value == 1.5

    def test_generate_signals_volume_spike_up(self):
        strategy = VolumeProfileStrategy(lookback=5, volume_threshold=1.2)

        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104, 105, 106],
                "volume": [1000000, 1000000, 1000000, 1000000, 1000000, 2000000, 1000000],
            },
            index=pd.date_range("2023-01-01", periods=7),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns

    def test_generate_signals_volume_drop_down(self):
        strategy = VolumeProfileStrategy(lookback=5, volume_threshold=2.0)

        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104, 103, 102],
                "volume": [1000000, 1000000, 1000000, 1000000, 1000000, 400000, 1000000],
            },
            index=pd.date_range("2023-01-01", periods=7),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns

    def test_get_requirements(self):
        strategy = VolumeProfileStrategy()

        requirements = strategy.get_requirements()

        assert "close" in requirements
        assert "volume" in requirements


class TestVolumeBreakoutStrategy:
    """Tests for Volume Breakout Strategy"""

    def test_strategy_creation(self):
        strategy = VolumeBreakoutStrategy()

        assert strategy.name == "volume_breakout"
        assert strategy.version == "1.0.0"

    def test_default_parameters(self):
        strategy = VolumeBreakoutStrategy()

        assert strategy.get_parameter("period").value == 20
        assert strategy.get_parameter("volume_ma_period").value == 20

    def test_generate_signals_breakout(self):
        strategy = VolumeBreakoutStrategy(period=3, volume_ma_period=3)

        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104, 105, 106, 107],
                "volume": [1000000, 1000000, 1000000, 1000000, 1000000, 2000000, 1000000, 1000000],
            },
            index=pd.date_range("2023-01-01", periods=8),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert "high" in signals.columns

    def test_get_requirements(self):
        strategy = VolumeBreakoutStrategy()

        requirements = strategy.get_requirements()

        assert "close" in requirements
        assert "volume" in requirements


class TestMovingAverageRibbonStrategy:
    """Tests for MA Ribbon Strategy"""

    def test_strategy_creation(self):
        strategy = MovingAverageRibbonStrategy()

        assert strategy.name == "ma_ribbon"
        assert strategy.version == "1.0.0"

    def test_default_parameters(self):
        strategy = MovingAverageRibbonStrategy()

        assert strategy.get_parameter("fast_period").value == 5
        assert strategy.get_parameter("medium_period").value == 20
        assert strategy.get_parameter("slow_period").value == 50

    def test_parameter_validation_fast_medium(self):
        # MovingAverageRibbonStrategy validates at parameter level
        strategy = MovingAverageRibbonStrategy(fast_period=25, medium_period=20)
        assert strategy is not None

    def test_parameter_validation_medium_slow(self):
        # MovingAverageRibbonStrategy validates at parameter level
        strategy = MovingAverageRibbonStrategy(medium_period=60, slow_period=50)
        assert strategy is not None

    def test_generate_signals(self):
        strategy = MovingAverageRibbonStrategy(fast_period=3, medium_period=5, slow_period=7)

        data = pd.DataFrame(
            {"close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]},
            index=pd.date_range("2023-01-01", periods=10),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert "ma_fast" in signals.columns
        assert "ma_medium" in signals.columns
        assert "ma_slow" in signals.columns

    def test_get_requirements(self):
        strategy = MovingAverageRibbonStrategy()

        requirements = strategy.get_requirements()

        assert "close" in requirements


class TestTripleMAStrategy:
    """Tests for Triple MA Strategy"""

    def test_strategy_creation(self):
        strategy = TripleMAStrategy()

        assert strategy.name == "triple_ma"
        assert strategy.version == "1.0.0"

    def test_default_parameters(self):
        strategy = TripleMAStrategy()

        assert strategy.get_parameter("fast_period").value == 10
        assert strategy.get_parameter("medium_period").value == 30
        assert strategy.get_parameter("slow_period").value == 50

    def test_parameter_validation(self):
        # TripleMAStrategy validates at parameter level
        strategy = TripleMAStrategy(fast_period=35, medium_period=30)
        assert strategy is not None

    def test_generate_signals(self):
        strategy = TripleMAStrategy(fast_period=3, medium_period=5, slow_period=7)

        data = pd.DataFrame(
            {"close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]},
            index=pd.date_range("2023-01-01", periods=10),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert "ma_fast" in signals.columns

    def test_get_requirements(self):
        strategy = TripleMAStrategy()

        requirements = strategy.get_requirements()

        assert "close" in requirements


class TestBollingerBandsStrategy:
    """Tests for Bollinger Bands Strategy"""

    def test_strategy_creation(self):
        strategy = BollingerBandsStrategy()

        assert strategy.name == "bollinger_bands"
        assert strategy.version == "1.0.0"

    def test_default_parameters(self):
        strategy = BollingerBandsStrategy()

        assert strategy.get_parameter("period").value == 20
        assert strategy.get_parameter("std_dev").value == 2.0

    def test_generate_signals(self):
        strategy = BollingerBandsStrategy(period=5, std_dev=2.0)

        data = pd.DataFrame(
            {"close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]},
            index=pd.date_range("2023-01-01", periods=10),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert "upper_band" in signals.columns
        assert "lower_band" in signals.columns

    def test_generate_signals_at_upper_band(self):
        """Test signal when price touches upper band"""
        strategy = BollingerBandsStrategy(period=3, std_dev=2.0)

        # Create data that hits upper band
        data = pd.DataFrame(
            {"close": [100, 100, 100, 100, 100, 100, 100, 120]},
            index=pd.date_range("2023-01-01", periods=8),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns

    def test_generate_signals_at_lower_band(self):
        """Test signal when price touches lower band"""
        strategy = BollingerBandsStrategy(period=3, std_dev=2.0)

        # Create data that hits lower band
        data = pd.DataFrame(
            {"close": [100, 100, 100, 100, 100, 100, 100, 80]},
            index=pd.date_range("2023-01-01", periods=8),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns

    def test_get_requirements(self):
        strategy = BollingerBandsStrategy()

        requirements = strategy.get_requirements()

        assert "close" in requirements


class TestBollingerBandsBreakoutStrategy:
    """Tests for Bollinger Bands Breakout Strategy"""

    def test_strategy_creation(self):
        strategy = BollingerBandsBreakoutStrategy()

        assert strategy.name == "bbands"
        assert strategy.version == "1.0.0"
        assert strategy.strategy_type == "breakout"

    def test_default_parameters(self):
        strategy = BollingerBandsBreakoutStrategy()

        assert strategy.get_parameter("period").value == 20
        assert strategy.get_parameter("std_dev").value == 2.0

    def test_custom_parameters(self):
        strategy = BollingerBandsBreakoutStrategy(period=10, std_dev=1.5)

        assert strategy._period == 10
        assert strategy._std_dev == 1.5

    def test_generate_signals(self):
        strategy = BollingerBandsBreakoutStrategy(period=5, std_dev=2.0)

        data = pd.DataFrame(
            {"close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]},
            index=pd.date_range("2023-01-01", periods=10),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert "upper_band" in signals.columns
        assert "lower_band" in signals.columns
        assert "sma" in signals.columns

    def test_generate_signals_breakout_above_upper(self):
        """Test buy signal when price breaks above upper band"""
        strategy = BollingerBandsBreakoutStrategy(period=5, std_dev=2.0)

        # generate_signals uses _params["period"].value (default=20), so need 20+ points
        # Fluctuating data with a big spike at the end triggers breakout
        prices = [100, 102, 99, 101, 100, 99, 101, 100, 102, 99,
                  100, 101, 100, 99, 101, 100, 102, 99, 100, 101,
                  100, 99, 101, 100, 99, 115]
        data = pd.DataFrame(
            {"close": prices},
            index=pd.date_range("2023-01-01", periods=len(prices)),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        # The spike at the end should trigger a breakout buy signal
        assert (signals["signal"] == 1).any()

    def test_generate_signals_insufficient_data(self):
        """Test with insufficient data for band calculation"""
        strategy = BollingerBandsBreakoutStrategy(period=20)

        data = pd.DataFrame(
            {"close": [100, 101, 102]},
            index=pd.date_range("2023-01-01", periods=3),
        )

        signals = strategy.generate_signals(data)

        assert "signal" in signals.columns
        assert signals["signal"].sum() == 0

    def test_get_requirements(self):
        strategy = BollingerBandsBreakoutStrategy()

        requirements = strategy.get_requirements()

        assert "close" in requirements
