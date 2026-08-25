"""
Forecast future subsidence using a GRU trained across all valid pixels'
displacement time series from cum.h5, benchmarked against a classical
linear-trend baseline.

Why pixel-as-sample rather than one AOI-average series: this dataset has
only ~33 epochs total. A single averaged time series is far too little
data to train any deep learning model meaningfully. Instead, every
valid pixel's time series becomes its own training sequence, sharing one
GRU across all of them — a standard approach in spatio-temporal
InSAR/remote-sensing deep learning, and honest about what 33 epochs can
actually support (~485 pixels x sliding windows, not 1 series).

Evaluation uses a TEMPORAL split (train on earlier epochs, test on the
most recent ones, for every pixel) rather than a random split — random
splitting would leak future information into training via overlapping
windows and give a misleadingly good score.
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

from config import (
    TS_FILE, FORECAST_WINDOW_SIZE, FORECAST_TEST_EPOCHS,
    FORECAST_GRU_UNITS, FORECAST_EPOCHS, FORECAST_DIR,
    FORECAST_MODEL_PATH, FORECAST_PLOT_PATH,
)


def load_pixel_series():
    """Load cum.h5 and return (n_valid_pixels, n_epochs) array + dates."""
    with h5py.File(TS_FILE, "r") as f:
        cum = f["cum"][:]  # (n_im, length, width), mm
        imdates = f["imdates"][:]

    n_im, length, width = cum.shape
    flat = cum.reshape(n_im, length * width).T  # (n_pixels, n_im)

    # Keep only pixels with a fully valid time series — a handful of
    # short gaps get linearly interpolated, but anything missing more
    # than ~10% of epochs is dropped rather than guessed at.
    valid_rows = []
    for row in flat:
        n_nan = np.isnan(row).sum()
        if n_nan == 0:
            valid_rows.append(row)
        elif n_nan / len(row) < 0.1:
            idx = np.arange(len(row))
            good = ~np.isnan(row)
            interp = np.interp(idx, idx[good], row[good])
            valid_rows.append(interp)

    series = np.array(valid_rows, dtype=np.float32)
    print(f"Loaded {series.shape[0]} valid pixel time series "
          f"(dropped {flat.shape[0] - series.shape[0]} with too many gaps) "
          f"across {n_im} epochs.")
    return series, imdates


def make_windows(series, window_size):
    """Turn each pixel's series into (X, y) sliding-window pairs."""
    X, y = [], []
    for row in series:
        for i in range(len(row) - window_size):
            X.append(row[i:i + window_size])
            y.append(row[i + window_size])
    return np.array(X), np.array(y)


def temporal_train_test_split(series, window_size, test_epochs):
    """Split by TIME: last `test_epochs` of every pixel's series held out."""
    n_epochs = series.shape[1]
    split_point = n_epochs - test_epochs

    train_series = series[:, :split_point]
    # Test inputs need window_size epochs of history immediately before
    # the held-out region, so include the tail of the training portion.
    test_series = series[:, split_point - window_size:]

    X_train, y_train = make_windows(train_series, window_size)
    X_test, y_test = make_windows(test_series, window_size)

    return X_train, y_train, X_test, y_test


def linear_trend_baseline(X):
    """Classical baseline: fit a line to each window, extrapolate one step."""
    preds = []
    t = np.arange(X.shape[1])
    for row in X:
        coef = np.polyfit(t, row, 1)
        preds.append(np.polyval(coef, X.shape[1]))  # one step ahead
    return np.array(preds)


def build_model(window_size, units):
    from tensorflow import keras
    from tensorflow.keras import layers

    model = keras.Sequential([
        layers.Input(shape=(window_size, 1)),
        layers.GRU(units),
        layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


def main():
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)

    series, imdates = load_pixel_series()
    if series.shape[0] < 20:
        print("WARNING: very few valid pixel series — results will be noisy. "
              "Consider widening the AOI or relaxing the interpolation "
              "threshold in load_pixel_series() if this seems too low.")

    X_train, y_train, X_test, y_test = temporal_train_test_split(
        series, FORECAST_WINDOW_SIZE, FORECAST_TEST_EPOCHS
    )
    print(f"Train windows: {X_train.shape[0]}, Test windows: {X_test.shape[0]}")

    # --- Baseline ---
    baseline_preds = linear_trend_baseline(X_test)
    baseline_mae = mean_absolute_error(y_test, baseline_preds)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_preds))

    # --- GRU ---
    model = build_model(FORECAST_WINDOW_SIZE, FORECAST_GRU_UNITS)
    X_train_r = X_train.reshape(-1, FORECAST_WINDOW_SIZE, 1)
    X_test_r = X_test.reshape(-1, FORECAST_WINDOW_SIZE, 1)

    model.fit(
        X_train_r, y_train,
        epochs=FORECAST_EPOCHS,
        batch_size=64,
        validation_split=0.1,
        verbose=1,
    )

    gru_preds = model.predict(X_test_r, verbose=0).flatten()
    gru_mae = mean_absolute_error(y_test, gru_preds)
    gru_rmse = np.sqrt(mean_squared_error(y_test, gru_preds))

    print("\n--- Results (mm, one-step-ahead forecast) ---")
    print(f"{'Model':20s} {'MAE':>8s} {'RMSE':>8s}")
    print(f"{'Linear trend':20s} {baseline_mae:8.3f} {baseline_rmse:8.3f}")
    print(f"{'GRU':20s} {gru_mae:8.3f} {gru_rmse:8.3f}")

    if gru_mae < baseline_mae:
        print(f"\nGRU improves on the linear baseline by "
              f"{(1 - gru_mae / baseline_mae) * 100:.1f}% (MAE).")
    else:
        print("\nGRU did not beat the linear baseline on this dataset — "
              "worth reporting honestly rather than hiding. With only 33 "
              "epochs, a linear trend is a genuinely strong baseline for "
              "short-horizon forecasts; the GRU may do better with more "
              "epochs of data (wider date range) or a longer forecast "
              "horizon where nonlinearity matters more.")

    model.save(FORECAST_MODEL_PATH)
    print(f"\nSaved model to {FORECAST_MODEL_PATH}")

    # --- Plot a few example pixels ---
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    rng = np.random.default_rng(42)
    sample_idx = rng.choice(len(X_test), size=min(4, len(X_test)), replace=False)

    for ax, idx in zip(axes.flat, sample_idx):
        history = X_test[idx]
        actual = y_test[idx]
        gru_pred = gru_preds[idx]
        base_pred = baseline_preds[idx]

        ax.plot(range(FORECAST_WINDOW_SIZE), history, "o-", label="History", color="gray")
        ax.plot(FORECAST_WINDOW_SIZE, actual, "o", label="Actual", color="black", markersize=8)
        ax.plot(FORECAST_WINDOW_SIZE, gru_pred, "s", label="GRU", color="tab:blue")
        ax.plot(FORECAST_WINDOW_SIZE, base_pred, "^", label="Linear trend", color="tab:orange")
        ax.set_xlabel("Epoch (relative)")
        ax.set_ylabel("Cumulative displacement (mm)")
        ax.legend(fontsize=8)

    fig.suptitle("GRU vs. linear-trend one-step forecasts (sample pixels)")
    fig.tight_layout()
    fig.savefig(FORECAST_PLOT_PATH, dpi=150)
    print(f"Saved comparison plot to {FORECAST_PLOT_PATH}")


if __name__ == "__main__":
    main()
