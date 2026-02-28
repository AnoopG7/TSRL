import pandas as pd
import numpy as np
from typing import Optional


class FeatureEngineer:
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        self.features = pd.DataFrame(index=data.index)

    def add_all_features(self) -> pd.DataFrame:
        self.add_price_features()
        self.add_returns_features()
        self.add_momentum_features()
        self.add_volatility_features()
        self.add_volume_features()
        self.add_technical_indicators()
        self.add_lagged_features()
        self.add_rolling_features()
        return self.features

    def add_price_features(self) -> None:
        df = self.data
        features = self.features

        features["open"] = df["open"]
        features["high"] = df["high"]
        features["low"] = df["low"]
        features["close"] = df["close"]
        features["volume"] = df["volume"]

        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        features["typical_price"] = typical_price
        features["weighted_close"] = (df["close"] + 2 * typical_price) / 3

        features["price_range"] = df["high"] - df["low"]
        features["price_change"] = df["close"].diff()
        features["price_change_pct"] = df["close"].pct_change()

        features["high_low_ratio"] = df["high"] / df["low"]
        features["close_open_ratio"] = df["close"] / df["open"]

    def add_returns_features(self) -> None:
        df = self.data
        features = self.features

        features["returns"] = df["close"].pct_change()
        features["log_returns"] = np.log(df["close"] / df["close"].shift(1))

        for window in [5, 10, 20, 50]:
            features[f"returns_{window}d"] = df["close"].pct_change(window)

        for window in [5, 10, 20, 50]:
            features[f"log_returns_{window}d"] = np.log(df["close"] / df["close"].shift(window))

    def add_momentum_features(self) -> None:
        df = self.data
        features = self.features

        close = df["close"]

        for period in [5, 10, 14, 20, 30, 50]:
            features[f"rsi_{period}"] = self._calculate_rsi(close, period)

        for period in [10, 20, 30, 50]:
            features[f"momentum_{period}"] = close - close.shift(period)
            features[f"momentum_pct_{period}"] = (close / close.shift(period) - 1) * 100

        for period in [12, 26]:
            features[f"roc_{period}"] = ((close - close.shift(period)) / close.shift(period)) * 100

        features["stochastic_k"], features["stochastic_d"] = self._calculate_stochastic(df)

        features["cci"] = self._calculate_cci(df)

        features["mfi"] = self._calculate_mfi(df)

    def add_volatility_features(self) -> None:
        df = self.data
        features = self.features

        close = df["close"]
        typical_price = (df["high"] + df["low"] + df["close"]) / 3

        for window in [5, 10, 14, 20, 30, 50]:
            features[f"volatility_{window}"] = close.pct_change().rolling(window).std()

        for period in [14, 20]:
            features[f"atr_{period}"] = self._calculate_atr(df, period)

        for window in [10, 20, 30]:
            features[f"bb_width_{window}"] = self._calculate_bollinger_width(close, window)

        for window in [20, 30, 50]:
            close_ma = close.rolling(window).mean()
            close_std = close.rolling(window).std()
            features[f"z_score_{window}"] = (close - close_ma) / close_std

        features["parkinson"] = self._calculate_parkinson(df)
        features["garman_klass"] = self._calculate_garman_klass(df)

    def add_volume_features(self) -> None:
        df = self.data
        features = self.features

        volume = df["volume"]
        close = df["close"]

        for window in [5, 10, 20, 50]:
            features[f"volume_ma_{window}"] = volume.rolling(window).mean()
            features[f"volume_ratio_{window}"] = volume / volume.rolling(window).mean()

        features["obv"] = self._calculate_obv(close, volume)
        features["vwap"] = self._calculate_vwap(df)

        for window in [10, 20]:
            features[f"volume_std_{window}"] = volume.rolling(window).std()

    def add_technical_indicators(self) -> None:
        df = self.data
        features = self.features

        close = df["close"]
        high = df["high"]
        low = df["low"]

        for short_period, long_period in [(8, 21), (12, 26), (5, 20), (10, 50)]:
            ema_short = close.ewm(span=short_period, adjust=False).mean()
            ema_long = close.ewm(span=long_period, adjust=False).mean()
            features[f"ema_{short_period}_{long_period}_diff"] = ema_short - ema_long

        for period in [9, 21, 50]:
            features[f"ema_{period}"] = close.ewm(span=period, adjust=False).mean()

        for period in [10, 20, 30, 50]:
            features[f"sma_{period}"] = close.rolling(period).mean()

        for period in [20]:
            sma = close.rolling(period).mean()
            std = close.rolling(period).std()
            features[f"bb_upper_{period}"] = sma + 2 * std
            features[f"bb_lower_{period}"] = sma - 2 * std
            features[f"bb_position_{period}"] = (close - features[f"bb_lower_{period}"]) / (
                features[f"bb_upper_{period}"] - features[f"bb_lower_{period}"]
            )

    def add_lagged_features(self) -> None:
        features = self.features

        lag_cols = ["close", "volume", "returns", "rsi_14", "atr_14"]

        new_cols = {}
        for col in lag_cols:
            if col in features.columns:
                for lag in [1, 2, 3, 5]:
                    new_cols[f"{col}_lag_{lag}"] = features[col].shift(lag)

        if new_cols:
            self.features = pd.concat(
                [self.features, pd.DataFrame(new_cols, index=self.features.index)], axis=1
            )

    def add_rolling_features(self) -> None:
        features = self.features

        new_cols = {}
        for window in [5, 10, 20]:
            new_cols[f"close_ma_{window}"] = features["close"].rolling(window).mean()
            new_cols[f"close_std_{window}"] = features["close"].rolling(window).std()

        for window in [5, 10, 20]:
            if "returns" in features.columns:
                new_cols[f"returns_mean_{window}"] = features["returns"].rolling(window).mean()
                new_cols[f"returns_skew_{window}"] = features["returns"].rolling(window).skew()

        if new_cols:
            self.features = pd.concat(
                [self.features, pd.DataFrame(new_cols, index=self.features.index)], axis=1
            )

    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_stochastic(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        low_min = df["low"].rolling(window=14).min()
        high_max = df["high"].rolling(window=14).max()

        k = 100 * (df["close"] - low_min) / (high_max - low_min)
        d = k.rolling(window=3).mean()

        return k, d

    def _calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        tp = (df["high"] + df["low"] + df["close"]) / 3
        sma = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

        cci = (tp - sma) / (0.015 * mad)
        return cci

    def _calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        tp = (df["high"] + df["low"] + df["close"]) / 3
        money_flow = tp * df["volume"]

        positive_flow = money_flow.where(tp > tp.shift(1), 0)
        negative_flow = money_flow.where(tp < tp.shift(1), 0)

        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()

        mfi = 100 - (100 / (1 + positive_mf / negative_mf))
        return mfi

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def _calculate_bollinger_width(self, close: pd.Series, period: int = 20) -> pd.Series:
        sma = close.rolling(period).mean()
        std = close.rolling(period).std()

        upper = sma + 2 * std
        lower = sma - 2 * std

        return (upper - lower) / sma

    def _calculate_parkinson(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        hl = np.log(df["high"] / df["low"])
        parkinson = np.sqrt((1 / (4 * np.log(2))) * (hl**2).rolling(window=period).mean())
        return parkinson

    def _calculate_garman_klass(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        hl = np.log(df["high"] / df["low"]) ** 2
        co = np.log(df["close"] / df["open"]) ** 2

        gk = (0.5 * hl - (2 * np.log(2) - 1) * co).rolling(window=period).mean()
        return np.sqrt(gk)

    def _calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv

    def _calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        tp = (df["high"] + df["low"] + df["close"]) / 3
        cumulative_tp_volume = (tp * df["volume"]).cumsum()
        cumulative_volume = df["volume"].cumsum()
        vwap = cumulative_tp_volume / cumulative_volume
        return vwap


class LabelGenerator:
    @staticmethod
    def generate_labels(
        data: pd.DataFrame,
        forward_periods: int = 5,
        threshold: float = 0.0,
    ) -> pd.Series:
        future_return = data["close"].shift(-forward_periods) / data["close"] - 1

        labels = pd.Series(index=data.index, dtype=float)
        labels[future_return > threshold] = 1
        labels[future_return < -threshold] = -1
        labels[(future_return >= -threshold) & (future_return <= threshold)] = 0

        return labels

    @staticmethod
    def generate_regime_labels(
        returns: pd.Series,
        window: int = 20,
    ) -> pd.Series:
        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()

        z_score = (returns - rolling_mean) / rolling_std

        labels = pd.Series(index=returns.index, dtype=float)
        labels[z_score > 1] = 1
        labels[z_score < -1] = -1
        labels[(z_score >= -1) & (z_score <= 1)] = 0

        return labels


class FeatureSelector:
    @staticmethod
    def select_by_correlation(
        features: pd.DataFrame,
        target: pd.Series,
        threshold: float = 0.1,
    ) -> list[str]:
        correlations = features.corrwith(target).abs()
        selected = correlations[correlations > threshold].index.tolist()
        return selected

    @staticmethod
    def select_by_importance(
        features: pd.DataFrame,
        importance_scores: dict,
        top_n: int = 20,
    ) -> list[str]:
        sorted_features = sorted(importance_scores.items(), key=lambda x: abs(x[1]), reverse=True)
        return [f[0] for f in sorted_features[:top_n]]
