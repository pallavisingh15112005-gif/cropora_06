"""Price-target alerts stored in Turso (or a local libSQL fallback)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

import db
from data_layer import latest_prices, mandi_name

ALERT_COLS = [
    "id",
    "commodity",
    "mandi_id",
    "target_price",
    "direction",
    "created_at",
]


def init_db() -> None:
    with db.connect():
        pass


def add_alert(commodity: str, mandi_id: str, target_price: float, direction: str) -> int:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO alerts (commodity, mandi_id, target_price, direction, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                commodity,
                mandi_id,
                float(target_price),
                direction,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT last_insert_rowid()").fetchone()
    return int(row[0]) if row else 0


def delete_alert(alert_id: int) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM alerts WHERE id = ?", (int(alert_id),))
        conn.commit()


def list_alerts() -> pd.DataFrame:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, commodity, mandi_id, target_price, direction, created_at"
            " FROM alerts ORDER BY id DESC"
        ).fetchall()
    df = pd.DataFrame(rows, columns=ALERT_COLS)
    if df.empty:
        return df

    prices = latest_prices()
    current = prices.set_index(["commodity", "mandi_id"])["modal_price"]
    source = (
        prices.set_index(["commodity", "mandi_id"])["price_source"]
        if "price_source" in prices.columns
        else pd.Series(dtype="object")
    )
    df["current_price"] = [
        float(current.get((crop, mandi), float("nan")))
        for crop, mandi in zip(df["commodity"], df["mandi_id"])
    ]
    df["price_source"] = [
        source.get((crop, mandi), "Sample")
        for crop, mandi in zip(df["commodity"], df["mandi_id"])
    ]
    df["mandi"] = df["mandi_id"].map(mandi_name)

    def status(row) -> str:
        if pd.isna(row["current_price"]):
            return "No price"
        if row["direction"] == "above":
            return "Triggered" if row["current_price"] >= row["target_price"] else "Waiting"
        return "Triggered" if row["current_price"] <= row["target_price"] else "Waiting"

    df["status"] = df.apply(status, axis=1)
    df["distance_to_target"] = (df["target_price"] - df["current_price"]).round(0)
    return df


def triggered_alerts() -> pd.DataFrame:
    df = list_alerts()
    return df[df["status"] == "Triggered"] if not df.empty else df
