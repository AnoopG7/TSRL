import logging
import pandas as pd
import numpy as np
from typing import Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from src.strategies.base import BaseStrategy, StrategyParameter
from src.strategies.registry import register_strategy
from src.ml.feature_engineering.features import FeatureEngineer

logger = logging.getLogger(__name__)


@register_strategy("ml_random_forest")
class MLRandomForestStrategy(BaseStrategy):
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 5,
        lookback: int = 50,
        prediction_horizon: int = 5,
        **kwargs,
    ):
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._lookback = lookback
        self._prediction_horizon = prediction_horizon
        self._model = None
        self._scaler = StandardScaler()
        self._feature_columns = None
        self._is_fitted = False
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "ml_random_forest"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Machine Learning Random Forest strategy using technical indicators"

    @property
    def strategy_type(self) -> str:
        return "ml"

    def _set_default_parameters(self) -> None:
        self._params = {
            "n_estimators": StrategyParameter(
                name="n_estimators",
                value=100,
                min_value=10,
                max_value=500,
                step=10,
                description="Number of trees in the forest",
            ),
            "max_depth": StrategyParameter(
                name="max_depth",
                value=5,
                min_value=2,
                max_value=20,
                step=1,
                description="Maximum depth of trees",
            ),
            "lookback": StrategyParameter(
                name="lookback",
                value=50,
                min_value=20,
                max_value=200,
                step=10,
                description="Lookback period for features",
            ),
            "prediction_horizon": StrategyParameter(
                name="prediction_horizon",
                value=5,
                min_value=1,
                max_value=20,
                step=1,
                description="Number of periods to predict ahead",
            ),
        }

    def before_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        if (
            len(data)
            < self._lookback + self._prediction_horizon + 50
        ):
            return data

        features = self._generate_features(data)
        labels = self._generate_labels(data)

        valid_idx = features.dropna().index.intersection(labels.dropna().index)
        if len(valid_idx) < 50:
            return data

        X = features.loc[valid_idx]
        y = labels.loc[valid_idx]

        X_scaled = self._scaler.fit_transform(X)

        self._model = RandomForestClassifier(
            n_estimators=self._n_estimators,
            max_depth=self._max_depth,
            random_state=42,
            n_jobs=-1,
        )
        self._model.fit(X_scaled, y)
        self._feature_columns = X.columns.tolist()
        self._is_fitted = True

        return data

    def _generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        engineer = FeatureEngineer(data)
        features = engineer.add_all_features()

        keep_cols = [
            "rsi_14",
            "rsi_30",
            "momentum_10",
            "momentum_20",
            "volatility_14",
            "atr_14",
            "volume_ratio_20",
            "ema_9_21_diff",
            "bb_position_20",
            "returns",
            "returns_5d",
            "returns_10d",
            "mfi",
        ]

        available_cols = [c for c in keep_cols if c in features.columns]
        return features[available_cols].dropna()

    def _generate_labels(self, data: pd.DataFrame) -> pd.Series:
        horizon = self._prediction_horizon
        future_return = data["close"].shift(-horizon) / data["close"] - 1

        labels = pd.Series(index=data.index, dtype=float)
        labels[future_return > 0.01] = 1
        labels[future_return < -0.01] = -1
        labels[(future_return >= -0.01) & (future_return <= 0.01)] = 0

        return labels

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["signal"] = 0

        if not self._is_fitted or self._model is None:
            return signals

        try:
            features = self._generate_features(data)

            if len(features) == 0:
                return signals

            aligned_signals = signals.loc[features.index].copy()
            aligned_signals["signal"] = 0

            X_scaled = self._scaler.transform(features)

            predictions = self._model.predict(X_scaled)

            aligned_signals["signal"] = predictions

            signals["signal"] = aligned_signals["signal"]

        except Exception as e:
            logger.warning(f"ML RandomForest signal generation failed: {e}")

        return signals

    def get_requirements(self) -> list[str]:
        return ["open", "high", "low", "close", "volume"]


@register_strategy("ml_gradient_boosting")
class MLGradientBoostingStrategy(BaseStrategy):
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 3,
        learning_rate: float = 0.1,
        lookback: int = 50,
        prediction_horizon: int = 5,
        **kwargs,
    ):
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._learning_rate = learning_rate
        self._lookback = lookback
        self._prediction_horizon = prediction_horizon
        self._model = None
        self._scaler = StandardScaler()
        self._is_fitted = False
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "ml_gradient_boosting"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Machine Learning Gradient Boosting strategy"

    @property
    def strategy_type(self) -> str:
        return "ml"

    def _set_default_parameters(self) -> None:
        self._params = {
            "n_estimators": StrategyParameter(
                name="n_estimators",
                value=100,
                min_value=10,
                max_value=300,
                step=10,
                description="Number of boosting stages",
            ),
            "max_depth": StrategyParameter(
                name="max_depth",
                value=3,
                min_value=1,
                max_value=10,
                step=1,
                description="Maximum depth of trees",
            ),
            "learning_rate": StrategyParameter(
                name="learning_rate",
                value=0.1,
                min_value=0.01,
                max_value=0.5,
                step=0.01,
                description="Learning rate",
            ),
            "lookback": StrategyParameter(
                name="lookback",
                value=50,
                min_value=20,
                max_value=200,
                step=10,
                description="Lookback period",
            ),
            "prediction_horizon": StrategyParameter(
                name="prediction_horizon",
                value=5,
                min_value=1,
                max_value=20,
                step=1,
                description="Prediction horizon",
            ),
        }

    def before_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        if (
            len(data)
            < self._lookback + self._prediction_horizon + 50
        ):
            return data

        features = self._generate_features(data)
        labels = self._generate_labels(data)

        valid_idx = features.dropna().index.intersection(labels.dropna().index)
        if len(valid_idx) < 50:
            return data

        X = features.loc[valid_idx]
        y = labels.loc[valid_idx]

        X_scaled = self._scaler.fit_transform(X)

        self._model = GradientBoostingClassifier(
            n_estimators=self._n_estimators,
            max_depth=self._max_depth,
            learning_rate=self._learning_rate,
            random_state=42,
        )
        self._model.fit(X_scaled, y)
        self._is_fitted = True

        return data

    def _generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        engineer = FeatureEngineer(data)
        features = engineer.add_all_features()

        keep_cols = [
            "rsi_14",
            "momentum_10",
            "momentum_20",
            "volatility_14",
            "atr_14",
            "volume_ratio_20",
            "ema_9_21_diff",
            "bb_position_20",
            "returns",
            "returns_5d",
            "cci",
        ]

        available_cols = [c for c in keep_cols if c in features.columns]
        return features[available_cols].dropna()

    def _generate_labels(self, data: pd.DataFrame) -> pd.Series:
        horizon = self._prediction_horizon
        future_return = data["close"].shift(-horizon) / data["close"] - 1

        labels = pd.Series(index=data.index, dtype=float)
        labels[future_return > 0.01] = 1
        labels[future_return < -0.01] = -1
        labels[(future_return >= -0.01) & (future_return <= 0.01)] = 0

        return labels

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["signal"] = 0

        if not self._is_fitted or self._model is None:
            return signals

        try:
            features = self._generate_features(data)

            if len(features) == 0:
                return signals

            aligned_signals = signals.loc[features.index].copy()
            aligned_signals["signal"] = 0

            X_scaled = self._scaler.transform(features)

            predictions = self._model.predict(X_scaled)

            aligned_signals["signal"] = predictions

            signals["signal"] = aligned_signals["signal"]

        except Exception as e:
            logger.warning(f"ML GradientBoosting signal generation failed: {e}")

        return signals

    def get_requirements(self) -> list[str]:
        return ["open", "high", "low", "close", "volume"]
