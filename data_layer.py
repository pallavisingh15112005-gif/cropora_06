"""Data access and market views for Cropora AI.

History comes from data/prices.csv, a synthetic Agmarknet-style sample dataset.
When live Agmarknet prices have been synced to Turso, today's price and the
forecast level are anchored to those live values; the model coefficients and
backtest are still trained on the sample history.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[0]
DATA_DIR = ROOT / "data"
ARTIFACT_DIR = ROOT / "artifacts"

TRANSPORT_RATE = 0.10  # assumed Rs per quintal per km


@lru_cache(maxsize=1)
def load_prices() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "prices.csv", parse_dates=["date"])
    return df.sort_values(["commodity", "mandi_id", "date"]).reset_index(drop=True)


@lru_cache(maxsize=1)
def load_crops() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "crops.csv")


@lru_cache(maxsize=1)
def load_mandis() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "mandis.csv")


@lru_cache(maxsize=1)
def load_locations() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "locations.csv")


@lru_cache(maxsize=1)
def load_forecasts() -> pd.DataFrame:
    return pd.read_csv(ARTIFACT_DIR / "forecasts.csv", parse_dates=["date"])


@lru_cache(maxsize=1)
def load_metrics() -> pd.DataFrame:
    return pd.read_csv(ARTIFACT_DIR / "metrics.csv")


@lru_cache(maxsize=1)
def load_model_info() -> dict:
    import json

    return json.loads((ARTIFACT_DIR / "model_info.json").read_text())


LIVE_SOURCE = "Agmarknet live"


@lru_cache(maxsize=1)
def live_prices() -> pd.DataFrame:
    from agmarknet import load_live_prices

    return load_live_prices()


@lru_cache(maxsize=1)
def live_latest() -> pd.DataFrame:
    from agmarknet import load_latest_live

    return load_latest_live()


def refresh_live_caches() -> None:
    for func in (live_prices, live_latest, forecast_summary, crop_outlook, forecast_path):
        func.cache_clear()


def market_date() -> pd.Timestamp:
    sample = pd.Timestamp(load_prices()["date"].max())
    live = live_latest()
    if live.empty:
        return sample
    return max(sample, pd.Timestamp(live["live_date"].max()))


def latest_prices() -> pd.DataFrame:
    prices = load_prices()
    last = prices[prices["date"] == prices["date"].max()]
    out = last[
        ["commodity", "mandi_id", "modal_price", "min_price", "max_price", "date"]
    ].copy()
    out["sample_modal_price"] = out["modal_price"]
    out["price_date"] = out["date"]
    out["price_source"] = "Sample"
    out = out.drop(columns="date")

    live = live_latest()
    if not live.empty:
        out = out.merge(live, on=["commodity", "mandi_id"], how="left")
        mask = out["live_price"].notna()
        out.loc[mask, "modal_price"] = out.loc[mask, "live_price"]
        out.loc[mask, "min_price"] = out.loc[mask, "live_min_price"].fillna(
            out.loc[mask, "live_price"]
        )
        out.loc[mask, "max_price"] = out.loc[mask, "live_max_price"].fillna(
            out.loc[mask, "live_price"]
        )
        out.loc[mask, "price_date"] = out.loc[mask, "live_date"]
        out.loc[mask, "price_source"] = LIVE_SOURCE
        out = out.drop(
            columns=[
                "live_date",
                "live_price",
                "live_min_price",
                "live_max_price",
                "live_variety_count",
                "fetched_at",
            ]
        )
    out["price_date"] = pd.to_datetime(out["price_date"])
    return out


def mandi_name(mandi_id: str) -> str:
    mandis = load_mandis()
    row = mandis.loc[mandis["mandi_id"] == mandi_id, "mandi"]
    return row.iloc[0] if len(row) else mandi_id.title()


def location_coords(location_name: str) -> tuple[float, float]:
    locs = load_locations()
    row = locs.loc[locs["location"] == location_name]
    if len(row):
        return float(row.iloc[0]["latitude"]), float(row.iloc[0]["longitude"])
    m = load_mandis()
    row = m.loc[m["mandi"] == location_name]
    return float(row.iloc[0]["latitude"]), float(row.iloc[0]["longitude"])


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return float(2 * r * np.arcsin(np.sqrt(a)))


def mandis_with_distance(location_name: str) -> pd.DataFrame:
    lat, lon = location_coords(location_name)
    mandis = load_mandis().copy()
    mandis["distance_km"] = [
        haversine_km(lat, lon, r.latitude, r.longitude) for r in mandis.itertuples()
    ]
    mandis["distance_km"] = mandis["distance_km"].round(1)
    mandis["transport_cost"] = (mandis["distance_km"] * TRANSPORT_RATE).round(0)
    return mandis


def price_history(commodity: str, mandi_id: str, days: int = 180) -> pd.DataFrame:
    prices = load_prices()
    df = prices[(prices["commodity"] == commodity) & (prices["mandi_id"] == mandi_id)]
    df = df.sort_values("date").tail(days)
    out = df[["date", "modal_price", "min_price", "max_price"]].copy()
    if out.empty:
        return out

    live = live_latest()
    pair = live[(live["commodity"] == commodity) & (live["mandi_id"] == mandi_id)]
    if not pair.empty:
        row = pair.iloc[0]
        live_date = pd.Timestamp(row["live_date"])
        if live_date >= out["date"].max():
            live_price = float(row["live_price"])
            lo = row["live_min_price"]
            hi = row["live_max_price"]
            point = {
                "date": live_date,
                "modal_price": live_price,
                "min_price": float(lo) if pd.notna(lo) else live_price,
                "max_price": float(hi) if pd.notna(hi) else live_price,
            }
            if live_date == out["date"].max():
                out.iloc[-1] = point
            else:
                out = pd.concat([out, pd.DataFrame([point])], ignore_index=True)
    return out


@lru_cache(maxsize=256)
def forecast_path(commodity: str, mandi_id: str) -> pd.DataFrame:
    """Recursive forecast scaled to the live price level when one is cached."""
    fc = load_forecasts()
    path = fc[(fc["commodity"] == commodity) & (fc["mandi_id"] == mandi_id)].copy()
    if path.empty:
        return path
    path = path.sort_values("horizon")

    live = live_latest()
    pair = live[(live["commodity"] == commodity) & (live["mandi_id"] == mandi_id)]
    prices = load_prices()
    sample = prices[(prices["commodity"] == commodity) & (prices["mandi_id"] == mandi_id)]
    if not pair.empty and not sample.empty:
        sample_last = sample.sort_values("date").iloc[-1]
        sample_date = pd.Timestamp(sample_last["date"])
        live_date = pd.Timestamp(pair.iloc[0]["live_date"])
        shift = max(0, (live_date - sample_date).days)
        if shift:
            path["date"] = path["date"] + pd.Timedelta(days=shift)
        sample_price = float(sample_last["modal_price"])
        if sample_price > 0:
            ratio = float(pair.iloc[0]["live_price"]) / sample_price
            for col in ("forecast_price", "lower", "upper"):
                path[col] = path[col] * ratio
    return path[["date", "horizon", "forecast_price", "lower", "upper"]].reset_index(drop=True)


@lru_cache(maxsize=1)
def forecast_summary() -> pd.DataFrame:
    latest = latest_prices()
    fc = load_forecasts()
    fc7 = fc[fc["horizon"] == 7][
        ["commodity", "mandi_id", "forecast_price", "lower", "upper", "date"]
    ].rename(columns={"date": "forecast_date"})
    out = latest.merge(fc7, on=["commodity", "mandi_id"], how="left")
    out = out.merge(load_crops()[["commodity", "category"]], on="commodity", how="left")
    out = out.merge(
        load_mandis()[["mandi_id", "mandi", "state", "latitude", "longitude"]],
        on="mandi_id",
        how="left",
    )
    if "sample_modal_price" in out.columns:
        base = out["sample_modal_price"].replace(0, np.nan)
        ratio = (out["modal_price"] / base).fillna(1.0)
        for col in ("forecast_price", "lower", "upper"):
            out[col] = out[col] * ratio
    sample_last = pd.Timestamp(load_prices()["date"].max())
    out["forecast_date"] = pd.to_datetime(out["forecast_date"])
    lag = (pd.to_datetime(out["price_date"]) - sample_last).dt.days.clip(lower=0)
    out["forecast_date"] = out["forecast_date"] + pd.to_timedelta(lag, unit="D")
    out["change_pct"] = (out["forecast_price"] / out["modal_price"] - 1) * 100
    return out.sort_values(["commodity", "modal_price"], ascending=[True, False]).reset_index(drop=True)


@lru_cache(maxsize=1)
def crop_outlook() -> pd.DataFrame:
    """Crop-level summary: 7-day momentum, stability scoring and value rank."""
    summary = forecast_summary()
    latest = market_date()
    prices = load_prices()

    recent = summary[summary["category"].notna()]
    by_crop = recent.groupby("commodity").agg(
        category=("category", "first"),
        current_price=("modal_price", "mean"),
        forecast_price=("forecast_price", "mean"),
        change_pct=("change_pct", "mean"),
        mandi_count=("mandi_id", "nunique"),
        change_dispersion=("change_pct", "std"),
    ).reset_index()

    recent_prices = prices[prices["date"] >= latest - pd.Timedelta(days=365)]
    yearly = recent_prices.groupby("commodity")["modal_price"].mean().rename("year_avg")
    by_crop = by_crop.merge(yearly, left_on="commodity", right_index=True, how="left")
    by_crop["vs_year_pct"] = (by_crop["current_price"] / by_crop["year_avg"] - 1) * 100

    last30 = prices[prices["date"] >= latest - pd.Timedelta(days=30)].copy()
    last30 = last30.sort_values(["commodity", "mandi_id", "date"])
    last30["ret"] = last30.groupby(["commodity", "mandi_id"])["modal_price"].pct_change()
    vol = last30.groupby("commodity")["ret"].std() * 100
    by_crop["volatility_pct"] = by_crop["commodity"].map(vol).fillna(0)
    by_crop["change_dispersion"] = by_crop["change_dispersion"].fillna(0)

    by_crop["momentum_score"] = (by_crop["change_pct"].rank(pct=True) * 100).round(0)
    by_crop["stability_score"] = ((-by_crop["volatility_pct"]).rank(pct=True) * 100).round(0)
    by_crop["value_score"] = (by_crop["vs_year_pct"].rank(pct=True) * 100).round(0)
    by_crop["outlook_score"] = (
        0.50 * by_crop["momentum_score"]
        + 0.25 * by_crop["stability_score"]
        + 0.25 * by_crop["value_score"]
    ).round(0)
    return by_crop.sort_values("outlook_score", ascending=False).reset_index(drop=True)


def outlook_for(commodity: str) -> pd.Series | None:
    outlook = crop_outlook()
    row = outlook[outlook["commodity"] == commodity]
    return row.iloc[0] if len(row) else None


def mandi_rows_for(commodity: str, location_name: str) -> pd.DataFrame:
    """Latest and forecast prices for one crop, with distance and transport cost."""
    summary = forecast_summary()
    df = summary[summary["commodity"] == commodity].copy()
    dist = mandis_with_distance(location_name)[["mandi_id", "distance_km", "transport_cost"]]
    df = df.merge(dist, on="mandi_id", how="left")
    df["net_price_now"] = (df["modal_price"] - df["transport_cost"]).round(0)
    df["net_price_d7"] = (df["forecast_price"] - df["transport_cost"]).round(0)
    return df.sort_values("net_price_d7", ascending=False).reset_index(drop=True)


def sell_plan(commodity: str, location_name: str, mandi_id: str | None = None) -> dict:
    rows = mandi_rows_for(commodity, location_name)
    if mandi_id and mandi_id in set(rows["mandi_id"]):
        rows = rows[rows["mandi_id"] == mandi_id].copy()
    if rows.empty:
        return {}
    best_now = rows.sort_values("net_price_now", ascending=False).iloc[0]
    best_later = rows.sort_values("net_price_d7", ascending=False).iloc[0]
    change = (best_later["net_price_d7"] / best_now["net_price_now"] - 1) * 100
    if change >= 2.0:
        stance = "Hold for about a week"
        reason = "The 7-day forecast is meaningfully higher than today's price."
    elif change <= -2.0:
        stance = "Sell now"
        reason = "The forecast trend is negative over the next week."
    else:
        stance = "Either now or within the week"
        reason = "The forecast move is small, so there is no strong timing advantage."
    return {
        "stance": stance,
        "reason": reason,
        "change_pct": float(change),
        "best_now": best_now,
        "best_later": best_later,
        "rows": rows,
    }


def fmt_inr(value: float | int | None, suffix: str = "") -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "n/a"
    return f"₹{value:,.0f}{suffix}"


def fmt_pct(value: float | None, signed: bool = True) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "n/a"
    rounded = round(float(value), 1)
    if rounded == 0:
        rounded = 0.0
    sign = "+" if signed and rounded > 0 else ""
    return f"{sign}{rounded:.1f}%"


def fmt_date(ts) -> str:
    return pd.Timestamp(ts).strftime("%d %b %Y")
