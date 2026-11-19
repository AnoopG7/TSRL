"""ML training must never see a label whose forward window hasn't closed yet."""

import numpy as np

from src.ml.strategies.ml_strategies import MLRandomForestStrategy


def test_training_rows_are_resolved_before_each_fit(sample_ohlcv_data_large):
    data = sample_ohlcv_data_large
    strategy = MLRandomForestStrategy(
        n_estimators=5, max_depth=3, prediction_horizon=5, min_train_samples=30, retrain_period=10
    )
    position = {ts: i for i, ts in enumerate(data.index)}
    fits: list[tuple[int, int]] = []

    original = strategy._train_model_on_window

    def spy(x_train, y):
        fits.append((max(position[t] for t in x_train.index), len(x_train)))
        original(x_train, y)

    strategy._train_model_on_window = spy  # type: ignore[method-assign]

    signals = strategy.generate_signals(data)
    assert fits, "model should have been fitted at least once"

    # Replay the schedule: a fit happens every retrain_period (10) bars, and the newest
    # training row must be at least prediction_horizon (5) bars older than the fit bar.
    feats = strategy._generate_features(data)
    rows = np.array([position[t] for t in feats.index])
    labels = strategy._generate_labels(data).reindex(feats.index).to_numpy()
    has_label = ~np.isnan(labels)
    expected = []
    last = None
    for bar in rows:
        if last is None or bar - last >= 10:
            mask = has_label & (rows <= bar - 5)
            if mask.sum() >= 30:
                expected.append((rows[mask].max(), int(mask.sum()), bar))
                last = bar
    assert [(a, b) for a, b, _ in expected] == fits
    for newest_row, _, fit_bar in expected:
        assert newest_row + 5 <= fit_bar
    assert set(np.unique(signals["signal"])) <= {-1, 0, 1}
