import logging
import pandas as pd
import numpy as np
from typing import Optional, Dict
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
        min_train_samples: int = 100,
        retrain_period: int = 20,
        **kwargs,
    ):
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._lookback = lookback
        self._prediction_horizon = prediction_horizon
        self._min_train_samples = min_train_samples
        self._retrain_period = retrain_period  # Retrain every N bars
        self._model = None
        self._scaler = StandardScaler()
        self._feature_columns = None
        self._is_fitted = False
        self._model_cache: Dict[int, tuple] = {}  # Cache models by index
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
            "min_train_samples": StrategyParameter(
                name="min_train_samples",
                value=100,
                min_value=50,
                max_value=500,
                step=10,
                description="Minimum samples required before trading",
            ),
            "retrain_period": StrategyParameter(
                name="retrain_period",
                value=20,
                min_value=5,
                max_value=50,
                step=5,
                description="Retrain model every N bars",
            ),
        }

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

    def _train_model_on_window(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train the model on a specific window of data."""
        if len(X) < self._min_train_samples:
            self._is_fitted = False
            return

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

    def before_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        # Don't train on full data - just prepare the data
        # Actual training happens incrementally in generate_signals
        if len(data) < self._lookback + self._prediction_horizon + self._min_train_samples:
            return data
        return data

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["signal"] = 0

        # Generate features for the entire dataset
        features = self._generate_features(data)
        labels = self._generate_labels(data)

        if len(features) == 0:
            return signals

        # Find valid indices where both features and labels are available
        valid_idx = features.dropna().index.intersection(labels.dropna().index)
        if len(valid_idx) < self._min_train_samples:
            return signals

        # Sort valid indices
        valid_idx = valid_idx.sort_values()
        valid_list = valid_idx.tolist()

        # Walk-forward training: train on expanding window, predict on next period
        # Only use data available up to each point
        last_train_idx = -1

        for i, current_idx in enumerate(valid_list):
            # Determine position in the original data
            if current_idx not in features.index:
                continue

            # Find training window: use only data BEFORE current point
            # Training window ends at current_idx - retrain_period (to avoid lookahead)
            train_end_pos = max(0, i - self._retrain_period)

            if train_end_pos > 0 and train_end_pos != last_train_idx:
                # Retrain model on expanding window
                train_indices = valid_list[:train_end_pos]
                X_train = features.loc[train_indices]
                y_train = labels.loc[train_indices]

                self._train_model_on_window(X_train, y_train)
                last_train_idx = train_end_pos

            # Predict if we have a trained model
            if self._is_fitted and self._model is not None:
                try:
                    X_current = features.loc[[current_idx]]
                    if len(X_current.columns) != len(self._feature_columns):
                        # Align columns
                        X_current = X_current[self._feature_columns]

                    X_scaled = self._scaler.transform(X_current)
                    prediction = self._model.predict(X_scaled)[0]
                    signals.loc[current_idx, "signal"] = prediction
                except Exception as e:
                    logger.debug(f"Prediction failed at {current_idx}: {e}")

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
        min_train_samples: int = 100,
        retrain_period: int = 20,
        **kwargs,
    ):
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._learning_rate = learning_rate
        self._lookback = lookback
        self._prediction_horizon = prediction_horizon
        self._min_train_samples = min_train_samples
        self._retrain_period = retrain_period
        self._model = None
        self._scaler = StandardScaler()
        self._is_fitted = False
        self._feature_columns = None
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
            "min_train_samples": StrategyParameter(
                name="min_train_samples",
                value=100,
                min_value=50,
                max_value=500,
                step=10,
                description="Minimum samples required before trading",
            ),
            "retrain_period": StrategyParameter(
                name="retrain_period",
                value=20,
                min_value=5,
                max_value=50,
                step=5,
                description="Retrain model every N bars",
            ),
        }

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

    def _train_model_on_window(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train the model on a specific window of data."""
        if len(X) < self._min_train_samples:
            self._is_fitted = False
            return

        X_scaled = self._scaler.fit_transform(X)
        self._model = GradientBoostingClassifier(
            n_estimators=self._n_estimators,
            max_depth=self._max_depth,
            learning_rate=self._learning_rate,
            random_state=42,
        )
        self._model.fit(X_scaled, y)
        self._feature_columns = X.columns.tolist()
        self._is_fitted = True

    def before_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        # Don't train on full data - just prepare the data
        # Actual training happens incrementally in generate_signals
        if len(data) < self._lookback + self._prediction_horizon + self._min_train_samples:
            return data
        return data

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"]

        signals = pd.DataFrame(index=data.index)
        signals["close"] = close
        signals["signal"] = 0

        # Generate features for the entire dataset
        features = self._generate_features(data)
        labels = self._generate_labels(data)

        if len(features) == 0:
            return signals

        # Find valid indices where both features and labels are available
        valid_idx = features.dropna().index.intersection(labels.dropna().index)
        if len(valid_idx) < self._min_train_samples:
            return signals

        # Sort valid indices
        valid_idx = valid_idx.sort_values()
        valid_list = valid_idx.tolist()

        # Walk-forward training: train on expanding window, predict on next period
        last_train_idx = -1

        for i, current_idx in enumerate(valid_list):
            # Find training window: use only data BEFORE current point
            train_end_pos = max(0, i - self._retrain_period)

            if train_end_pos > 0 and train_end_pos != last_train_idx:
                # Retrain model on expanding window
                train_indices = valid_list[:train_end_pos]
                X_train = features.loc[train_indices]
                y_train = labels.loc[train_indices]

                self._train_model_on_window(X_train, y_train)
                last_train_idx = train_end_pos

            # Predict if we have a trained model
            if self._is_fitted and self._model is not None:
                try:
                    X_current = features.loc[[current_idx]]
                    if len(X_current.columns) != len(self._feature_columns):
                        X_current = X_current[self._feature_columns]

                    X_scaled = self._scaler.transform(X_current)
                    prediction = self._model.predict(X_scaled)[0]
                    signals.loc[current_idx, "signal"] = prediction
                except Exception as e:
                    logger.debug(f"Prediction failed at {current_idx}: {e}")

        return signals

    def get_requirements(self) -> list[str]:
        return ["open", "high", "low", "close", "volume"]
