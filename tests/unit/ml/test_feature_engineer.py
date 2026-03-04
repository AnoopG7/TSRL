import pytest
import pandas as pd
import numpy as np
from src.ml.feature_engineering.features import FeatureEngineer, LabelGenerator, FeatureSelector


class TestFeatureEngineer:
    def test_initialization(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)

        assert engineer.data is not None
        assert isinstance(engineer.features, pd.DataFrame)
        assert len(engineer.features) == len(sample_ohlcv_data)

    def test_add_all_features(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        features = engineer.add_all_features()

        assert isinstance(features, pd.DataFrame)
        assert len(features) > 0

    def test_add_price_features(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_price_features()

        expected_cols = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "typical_price",
            "weighted_close",
            "price_range",
            "price_change",
            "price_change_pct",
            "high_low_ratio",
            "close_open_ratio",
        ]

        for col in expected_cols:
            assert col in engineer.features.columns

    def test_add_returns_features(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_returns_features()

        expected_cols = ["returns", "log_returns"]
        for window in [5, 10, 20, 50]:
            expected_cols.extend([f"returns_{window}d", f"log_returns_{window}d"])

        for col in expected_cols:
            assert col in engineer.features.columns

    def test_add_momentum_features(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_momentum_features()

        for period in [5, 10, 14, 20, 30, 50]:
            assert f"rsi_{period}" in engineer.features.columns

        for period in [10, 20, 30, 50]:
            assert f"momentum_{period}" in engineer.features.columns
            assert f"momentum_pct_{period}" in engineer.features.columns

        for period in [12, 26]:
            assert f"roc_{period}" in engineer.features.columns

        assert "stochastic_k" in engineer.features.columns
        assert "stochastic_d" in engineer.features.columns
        assert "cci" in engineer.features.columns
        assert "mfi" in engineer.features.columns

    def test_add_volatility_features(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_volatility_features()

        for window in [5, 10, 14, 20, 30, 50]:
            assert f"volatility_{window}" in engineer.features.columns

        for period in [14, 20]:
            assert f"atr_{period}" in engineer.features.columns

        for window in [10, 20, 30]:
            assert f"bb_width_{window}" in engineer.features.columns

        for window in [20, 30, 50]:
            assert f"z_score_{window}" in engineer.features.columns

        assert "parkinson" in engineer.features.columns
        assert "garman_klass" in engineer.features.columns

    def test_add_volume_features(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_volume_features()

        for window in [5, 10, 20, 50]:
            assert f"volume_ma_{window}" in engineer.features.columns
            assert f"volume_ratio_{window}" in engineer.features.columns

        assert "obv" in engineer.features.columns
        assert "vwap" in engineer.features.columns

        for window in [10, 20]:
            assert f"volume_std_{window}" in engineer.features.columns

    def test_add_technical_indicators(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_technical_indicators()

        for short_period, long_period in [(8, 21), (12, 26), (5, 20), (10, 50)]:
            assert f"ema_{short_period}_{long_period}_diff" in engineer.features.columns

        for period in [9, 21, 50]:
            assert f"ema_{period}" in engineer.features.columns

        for period in [10, 20, 30, 50]:
            assert f"sma_{period}" in engineer.features.columns

        assert "bb_upper_20" in engineer.features.columns
        assert "bb_lower_20" in engineer.features.columns
        assert "bb_position_20" in engineer.features.columns

    def test_add_lagged_features(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_price_features()
        engineer.add_returns_features()
        engineer.add_momentum_features()
        original_cols = set(engineer.features.columns)

        engineer.add_lagged_features()

        new_cols = set(engineer.features.columns) - original_cols
        assert len(new_cols) > 0

    def test_add_rolling_features(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_price_features()
        engineer.add_returns_features()
        original_cols = set(engineer.features.columns)

        engineer.add_rolling_features()

        new_cols = set(engineer.features.columns) - original_cols
        assert len(new_cols) > 0

    def test_calculate_rsi(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        rsi = engineer._calculate_rsi(sample_ohlcv_data["close"], period=14)

        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_ohlcv_data)
        assert rsi.max() <= 100
        assert rsi.min() >= 0

    def test_calculate_stochastic(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        k, d = engineer._calculate_stochastic(sample_ohlcv_data)

        assert isinstance(k, pd.Series)
        assert isinstance(d, pd.Series)
        assert len(k) == len(sample_ohlcv_data)
        assert len(d) == len(sample_ohlcv_data)

    def test_calculate_cci(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        cci = engineer._calculate_cci(sample_ohlcv_data, period=20)

        assert isinstance(cci, pd.Series)
        assert len(cci) == len(sample_ohlcv_data)

    def test_calculate_mfi(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        mfi = engineer._calculate_mfi(sample_ohlcv_data, period=14)

        assert isinstance(mfi, pd.Series)
        assert len(mfi) == len(sample_ohlcv_data)
        assert mfi.max() <= 100
        assert mfi.min() >= 0

    def test_calculate_atr(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        atr = engineer._calculate_atr(sample_ohlcv_data, period=14)

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_ohlcv_data)
        assert (atr.dropna() >= 0).all()

    def test_calculate_bollinger_width(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        width = engineer._calculate_bollinger_width(sample_ohlcv_data["close"], period=20)

        assert isinstance(width, pd.Series)
        assert len(width) == len(sample_ohlcv_data)

    def test_calculate_parkinson(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        parkinson = engineer._calculate_parkinson(sample_ohlcv_data, period=20)

        assert isinstance(parkinson, pd.Series)
        assert len(parkinson) == len(sample_ohlcv_data)
        assert (parkinson.dropna() >= 0).all()

    def test_calculate_garman_klass(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        gk = engineer._calculate_garman_klass(sample_ohlcv_data, period=20)

        assert isinstance(gk, pd.Series)
        assert len(gk) == len(sample_ohlcv_data)
        assert (gk.dropna() >= 0).all()

    def test_calculate_obv(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        obv = engineer._calculate_obv(sample_ohlcv_data["close"], sample_ohlcv_data["volume"])

        assert isinstance(obv, pd.Series)
        assert len(obv) == len(sample_ohlcv_data)

    def test_calculate_vwap(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        vwap = engineer._calculate_vwap(sample_ohlcv_data)

        assert isinstance(vwap, pd.Series)
        assert len(vwap) == len(sample_ohlcv_data)


class TestLabelGenerator:
    def test_generate_labels_basic(self, sample_ohlcv_data):
        labels = LabelGenerator.generate_labels(sample_ohlcv_data, forward_periods=5, threshold=0.0)

        assert isinstance(labels, pd.Series)
        assert len(labels) == len(sample_ohlcv_data)
        assert set(labels.dropna().unique()).issubset({-1, 0, 1})

    def test_generate_labels_with_threshold(self, sample_ohlcv_data):
        labels = LabelGenerator.generate_labels(
            sample_ohlcv_data, forward_periods=5, threshold=0.02
        )

        assert isinstance(labels, pd.Series)
        assert len(labels) == len(sample_ohlcv_data)

    def test_generate_labels_different_periods(self, sample_ohlcv_data):
        for period in [1, 5, 10, 20]:
            labels = LabelGenerator.generate_labels(
                sample_ohlcv_data, forward_periods=period, threshold=0.0
            )
            assert len(labels) == len(sample_ohlcv_data)

    def test_generate_regime_labels(self, sample_ohlcv_data):
        returns = sample_ohlcv_data["close"].pct_change()
        labels = LabelGenerator.generate_regime_labels(returns, window=20)

        assert isinstance(labels, pd.Series)
        assert len(labels) == len(returns)
        assert set(labels.dropna().unique()).issubset({-1, 0, 1})

    def test_generate_regime_labels_different_windows(self, sample_ohlcv_data):
        returns = sample_ohlcv_data["close"].pct_change()

        for window in [10, 20, 50]:
            labels = LabelGenerator.generate_regime_labels(returns, window=window)
            assert len(labels) == len(returns)


class TestFeatureSelector:
    def test_select_by_correlation(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        features = engineer.add_all_features()

        target = sample_ohlcv_data["close"].pct_change().shift(-1)

        selected = FeatureSelector.select_by_correlation(features, target, threshold=0.1)

        assert isinstance(selected, list)

    def test_select_by_correlation_empty_threshold(self, sample_ohlcv_data):
        engineer = FeatureEngineer(sample_ohlcv_data)
        features = engineer.add_all_features()

        target = sample_ohlcv_data["close"].pct_change().shift(-1)

        selected = FeatureSelector.select_by_correlation(features, target, threshold=1.0)

        assert isinstance(selected, list)

    def test_select_by_importance(self, sample_ohlcv_data):
        importance_scores = {
            "feature1": 0.5,
            "feature2": 0.3,
            "feature3": 0.1,
            "feature4": -0.2,
            "feature5": 0.0,
        }

        selected = FeatureSelector.select_by_importance(None, importance_scores, top_n=3)

        assert len(selected) == 3
        assert "feature1" in selected

    def test_select_by_importance_top_n(self, sample_ohlcv_data):
        importance_scores = {f"feature_{i}": i * 0.1 for i in range(20)}

        selected = FeatureSelector.select_by_importance(None, importance_scores, top_n=5)

        assert len(selected) == 5
