"""7-day price forecasting for Cropora AI.

One ridge-regression model per commodity, trained across all of that
commodity's mandis with lag, rolling-window, momentum and calendar features,
plus mandi indicator columns. Forecasts are produced recursively, seven days
ahead, with an 80% band estimated from a rolling-origin backtest.

Build artifacts:  python scripts/build_artifacts.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[0]
DATA_DIR = ROOT / "data"
ARTIFACT_DIR = ROOT / "artifacts"

HORIZON = 7
ALPHA = 3.0
EVAL_ORIGINS = 28
EVAL_END_OFFSET_DAYS = 7  # keep last week of data as actuals for the backtest
BAND_QUANTILE = 0.80

LAGS = (1, 2, 3, 7, 14, 21, 30)
ROLL_WINDOWS = (7, 14, 30)
BASE_FEATURES = [f"lag_{n}" for n in LAGS] + [
    f"roll_mean_{w}" for w in ROLL_WINDOWS
] + ["roll_std_7", "mom_7", "mom_30", "doy_sin1", "doy_cos1", "doy_sin2", "doy_cos2", "dow_sin", "dow_cos"]


@dataclass
class ModelBundle:
    model: Pipeline
    feat_cols: list[str]
    mandis: list[str]
    q80_abs: np.ndarray
    train_rows: int


def _calendar_features(d: pd.Timestamp) -> dict[str, float]:
    frac = d.dayofyear / 365.25
    angle = 2 * np.pi * frac
    dow = d.dayofweek / 7.0
    return {
        "doy_sin1": float(np.sin(angle)),
        "doy_cos1": float(np.cos(angle)),
        "doy_sin2": float(np.sin(2 * angle)),
        "doy_cos2": float(np.cos(2 * angle)),
        "dow_sin": float(np.sin(2 * np.pi * dow)),
        "dow_cos": float(np.cos(2 * np.pi * dow)),
    }


def _add_training_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["mandi_id", "date"]).copy()
    group = df.groupby("mandi_id", sort=False)["modal_price"]
    for lag in LAGS:
        df[f"lag_{lag}"] = group.shift(lag)
    for window in ROLL_WINDOWS:
        df[f"roll_mean_{window}"] = group.transform(
            lambda s, w=window: s.rolling(w).mean().shift(1)
        )
    df["roll_std_7"] = group.transform(lambda s: s.rolling(7).std().shift(1))
    df["mom_7"] = df["lag_1"] / df["roll_mean_7"] - 1.0
    df["mom_30"] = df["lag_1"] / df["roll_mean_30"] - 1.0

    frac = df["date"].dt.dayofyear / 365.25
    for harmonics in (1, 2):
        df[f"doy_sin{harmonics}"] = np.sin(2 * np.pi * frac * harmonics)
        df[f"doy_cos{harmonics}"] = np.cos(2 * np.pi * frac * harmonics)
    dow = df["date"].dt.dayofweek / 7.0
    df["dow_sin"] = np.sin(2 * np.pi * dow)
    df["dow_cos"] = np.cos(2 * np.pi * dow)

    dummies = pd.get_dummies(df["mandi_id"], prefix="m").astype(float)
    df = pd.concat([df, dummies], axis=1)
    return df.dropna(subset=BASE_FEATURES)


def _fit(train_df: pd.DataFrame, mandis: list[str], q80: np.ndarray | None = None) -> ModelBundle:
    prepared = _add_training_features(train_df)
    dummy_cols = [c for c in prepared.columns if c.startswith("m_")]
    feat_cols = BASE_FEATURES + dummy_cols
    model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=ALPHA))])
    model.fit(prepared[feat_cols], prepared["modal_price"])
    if q80 is None:
        q80 = np.full(HORIZON, 0.02, dtype=float)
    return ModelBundle(model, feat_cols, mandis, q80, int(len(prepared)))


def _row_features(history: np.ndarray, d: pd.Timestamp) -> dict[str, float]:
    row: dict[str, float] = {}
    for lag in LAGS:
        row[f"lag_{lag}"] = float(history[-lag])
    for window in ROLL_WINDOWS:
        row[f"roll_mean_{window}"] = float(np.mean(history[-window:]))
    row["roll_std_7"] = float(np.std(history[-7:], ddof=1))
    row["mom_7"] = row["lag_1"] / row["roll_mean_7"] - 1.0
    row["mom_30"] = row["lag_1"] / row["roll_mean_30"] - 1.0
    row.update(_calendar_features(d))
    return row


def _predict_batch(bundle: ModelBundle, histories: dict[str, np.ndarray],
                   d: pd.Timestamp) -> dict[str, float]:
    rows = []
    for mandi in bundle.mandis:
        row = _row_features(histories[mandi], d)
        has_dummy = set(bundle.feat_cols) - set(BASE_FEATURES)
        for dummy in has_dummy:
            row[dummy] = 1.0 if dummy == f"m_{mandi}" else 0.0
        rows.append(row)
    frame = pd.DataFrame(rows, columns=bundle.feat_cols)
    preds = bundle.model.predict(frame)
    return {mandi: float(p) for mandi, p in zip(bundle.mandis, preds)}


def _recursive_forecast(bundle: ModelBundle, histories: dict[str, np.ndarray],
                        start: date, horizon: int = HORIZON) -> pd.DataFrame:
    history_lists = {m: list(h) for m, h in histories.items()}
    anchors = {m: float(h[-1]) for m, h in histories.items()}
    dummy_set = set(bundle.feat_cols) - set(BASE_FEATURES)
    rows = []
    for h in range(1, horizon + 1):
        d = pd.Timestamp(start + timedelta(days=h - 1))
        feature_rows = []
        for mandi in bundle.mandis:
            row = _row_features(np.asarray(history_lists[mandi]), d)
            for dummy in dummy_set:
                row[dummy] = 1.0 if dummy == f"m_{mandi}" else 0.0
            feature_rows.append(row)
        preds = bundle.model.predict(pd.DataFrame(feature_rows, columns=bundle.feat_cols))

        for mandi, raw in zip(bundle.mandis, preds):
            prev = history_lists[mandi][-1]
            pred = float(np.clip(raw, prev * 0.94, prev * 1.06))
            pred = float(np.clip(pred, anchors[mandi] * 0.75, anchors[mandi] * 1.35))
            history_lists[mandi].append(pred)
            q80 = float(bundle.q80_abs[h - 1])
            rows.append(
                {
                    "date": d,
                    "mandi_id": mandi,
                    "horizon": h,
                    "forecast_price": round(pred, 0),
                    "lower": round(max(0.0, pred - q80), 0),
                    "upper": round(pred + q80, 0),
                }
            )
    return pd.DataFrame(rows)


def backtest_commodity(df: pd.DataFrame, mandis: list[str]) -> tuple[dict, dict]:
    """Rolling-origin backtest: train before the evaluation window, then make
    recursive 7-day forecasts from 28 consecutive origins on unseen actuals."""
    date_array = np.sort(df["date"].unique())
    last = pd.Timestamp(date_array[-1])
    origins_start = last - pd.Timedelta(days=EVAL_ORIGINS + EVAL_END_OFFSET_DAYS - 1)
    cutoff = origins_start - pd.Timedelta(days=1)
    bundle = _fit(df[df["date"] <= cutoff], mandis)

    actual = {(r.mandi_id, r.date): float(r.modal_price) for r in df.itertuples()}
    series = {
        m: df[df["mandi_id"] == m].sort_values("date")["modal_price"].to_numpy()
        for m in mandis
    }
    errors_by_h: list[list[float]] = [[] for _ in range(HORIZON)]
    last_horizon_pairs: list[tuple[float, float]] = []
    preds_all, actuals_all = [], []

    for origin_idx in range(EVAL_ORIGINS):
        origin = origins_start + pd.Timedelta(days=origin_idx)
        n_known = int((date_array <= origin.to_datetime64()).sum())
        if n_known < 40:
            continue
        histories = {m: series[m][:n_known] for m in mandis}
        fc = _recursive_forecast(bundle, histories, origin.date() + timedelta(days=1))
        for row in fc.itertuples():
            key = (row.mandi_id, pd.Timestamp(row.date))
            if key not in actual:
                continue
            err = row.forecast_price - actual[key]
            errors_by_h[row.horizon - 1].append(err)
            preds_all.append(row.forecast_price)
            actuals_all.append(actual[key])
            if row.horizon == HORIZON:
                last_horizon_pairs.append((row.forecast_price, actual[key]))

    y_pred = np.array(preds_all)
    y_true = np.array(actuals_all)
    abs_pct = np.abs((y_pred - y_true) / y_true) * 100
    h7_pct = [abs(p - a) / a * 100 for p, a in last_horizon_pairs]
    metrics = {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "mape": float(abs_pct.mean()),
        "mape_h7": float(np.mean(h7_pct)) if h7_pct else float("nan"),
        "r2": float(r2_score(y_true, y_pred)),
        "predictions": int(len(y_true)),
    }
    q80 = np.array([np.quantile(e, BAND_QUANTILE) if e else 0.02 for e in errors_by_h])
    return metrics, {"q80": q80, "origins": EVAL_ORIGINS}


def build_all(prices: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    if prices is None:
        prices = pd.read_csv(DATA_DIR / "prices.csv", parse_dates=["date"])
    ARTIFACT_DIR.mkdir(exist_ok=True)

    metrics_rows, forecast_rows = [], []
    for commodity, cdf in prices.groupby("commodity", sort=True):
        cdf = cdf.copy()
        mandi_ids = sorted(cdf["mandi_id"].unique())
        metrics, extra = backtest_commodity(cdf, mandi_ids)

        full_bundle = _fit(cdf, mandi_ids, q80=extra["q80"])
        series = {
            m: cdf[cdf["mandi_id"] == m].sort_values("date")["modal_price"].to_numpy()
            for m in mandi_ids
        }
        last_date = pd.Timestamp(cdf["date"].max())
        fc = _recursive_forecast(full_bundle, series, last_date.date() + timedelta(days=1))
        fc.insert(0, "commodity", commodity)
        fc["baseline_price"] = [float(series[m][-1]) for m in fc["mandi_id"]]
        forecast_rows.append(fc)

        metrics_rows.append(
            {
                "commodity": commodity,
                "mae": round(metrics["mae"], 1),
                "rmse": round(metrics["rmse"], 1),
                "mape": round(metrics["mape"], 2),
                "mape_h7": round(metrics["mape_h7"], 2),
                "r2": round(metrics["r2"], 4),
                "predictions": metrics["predictions"],
                "origins": extra["origins"],
                "train_rows": full_bundle.train_rows,
            }
        )

    metrics_df = pd.DataFrame(metrics_rows).sort_values("commodity").reset_index(drop=True)
    forecasts_df = pd.concat(forecast_rows, ignore_index=True)
    forecasts_df["date"] = pd.to_datetime(forecasts_df["date"])
    metrics_df.to_csv(ARTIFACT_DIR / "metrics.csv", index=False)
    forecasts_df.to_csv(ARTIFACT_DIR / "forecasts.csv", index=False)

    info = {
        "model": "Ridge regression (alpha=3.0) with StandardScaler, one model per commodity",
        "features": BASE_FEATURES,
        "horizon_days": HORIZON,
        "backtest": (
            f"Rolling-origin backtest, {EVAL_ORIGINS} consecutive origins, "
            "7-day recursive forecasts, evaluated on unseen actual prices"
        ),
        "trained_on": "Synthetic Agmarknet-style sample prices",
        "data_end": str(prices["date"].max().date()),
        "built_at": pd.Timestamp.now().isoformat(timespec="seconds"),
        "avg_mape": round(float(metrics_df["mape"].mean()), 2),
        "avg_mape_h7": round(float(metrics_df["mape_h7"].mean()), 2),
        "avg_r2": round(float(metrics_df["r2"].mean()), 4),
        "total_predictions": int(metrics_df["predictions"].sum()),
    }
    (ARTIFACT_DIR / "model_info.json").write_text(json.dumps(info, indent=2))
    return {"metrics": metrics_df, "forecasts": forecasts_df, "info": pd.DataFrame([info])}


@lru_cache(maxsize=1)
def load_metrics() -> pd.DataFrame:
    return pd.read_csv(ARTIFACT_DIR / "metrics.csv")


@lru_cache(maxsize=1)
def load_forecasts() -> pd.DataFrame:
    return pd.read_csv(ARTIFACT_DIR / "forecasts.csv", parse_dates=["date"])


@lru_cache(maxsize=1)
def load_model_info() -> dict:
    return json.loads((ARTIFACT_DIR / "model_info.json").read_text())


if __name__ == "__main__":
    out = build_all()
    print(out["metrics"].to_string(index=False))
    print(f"\nAverage MAPE (all horizons): {out['info'].iloc[0]['avg_mape']}%")
    print(f"Average MAPE (7-day ahead): {out['info'].iloc[0]['avg_mape_h7']}%")
    print(f"Average R2: {out['info'].iloc[0]['avg_r2']}")
    print(f"Forecast rows: {len(out['forecasts'])}")
