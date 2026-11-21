"""Live Agmarknet mandi prices through the official data.gov.in API.

Agmarknet 2.0 protects its own JSON endpoints with a CAPTCHA, so this module
uses the government's open-data resource instead. It needs a free API key from
data.gov.in. Fetched prices are cached in Turso (or the local libSQL file).
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

import db

SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "live_snapshot.json"

RESOURCE_ID = os.getenv(
    "DATA_GOV_RESOURCE_ID", "9ef84268-d588-465a-a308-a864a43d0070"
).strip()
API_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
PAGE_LIMIT = 1000
MAX_PAGES = 8
SOURCE = "Agmarknet"

LIVE_COLS = [
    "price_date",
    "commodity",
    "mandi_id",
    "mandi",
    "state",
    "min_price",
    "max_price",
    "modal_price",
    "variety_count",
    "source",
    "fetched_at",
]

_MANDI_ALIASES = {
    "bangalore": "bengaluru",
    "mysore": "mysuru",
    "nasik": "nashik",
}


def _secret(name: str) -> str:
    try:
        import streamlit as st

        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except Exception:
        pass
    return (os.environ.get(name) or "").strip()


def api_key() -> str:
    return _secret("DATA_GOV_API_KEY")


def _redact(text: str) -> str:
    key = api_key()
    if key:
        text = text.replace(key, "***")
    return re.sub(r"(api-key=)[^&\s)]+", r"\1***", text)


def is_configured() -> bool:
    return bool(api_key())


_CLOUD_ENV_VARS = ("RENDER", "STREAMLIT_SHARING_MODE", "K_SERVICE")


def can_sync_here() -> bool:
    """data.gov.in only answers hosts on Indian networks, so cloud hosts cannot fetch."""
    return not any(os.environ.get(var) for var in _CLOUD_ENV_VARS)


def _load_snapshot() -> tuple[pd.DataFrame, str | None]:
    try:
        payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        df = pd.DataFrame(payload.get("rows") or [], columns=LIVE_COLS)
    except (OSError, ValueError):
        return pd.DataFrame(columns=LIVE_COLS), None
    if df.empty:
        return df, None
    df["price_date"] = pd.to_datetime(df["price_date"])
    for col in ("min_price", "max_price", "modal_price", "variety_count"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df, payload.get("synced_at")


def _norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").replace("₹", "").strip()
    if text.lower() in {"", "na", "n/a", "none", "null", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_date(value: object) -> pd.Timestamp | None:
    text = str(value or "").strip()
    if not text:
        return None
    for dayfirst in (True, False):
        parsed = pd.to_datetime(text, dayfirst=dayfirst, errors="coerce")
        if not pd.isna(parsed):
            return pd.Timestamp(parsed).normalize()
    return None


def _map_commodity(name: object) -> str | None:
    n = _norm(name)
    if not n:
        return None
    if n.startswith("paddy"):
        return "Paddy (Rice)"
    if n.startswith("soy"):
        return "Soybean"
    if n.startswith("cotton"):
        return "Cotton"
    if n.startswith("wheat"):
        return "Wheat"
    if n.startswith("maize"):
        return "Maize"
    if n.startswith("onion"):
        return "Onion"
    if n.startswith("tomato"):
        return "Tomato"
    if n.startswith("potato"):
        return "Potato"
    if n.startswith("banana"):
        return "Banana"
    if n.startswith("mango"):
        return "Mango"
    if n.startswith("apple"):
        return "Apple"
    if n.startswith("grapes"):
        return "Grapes"
    if "orange" in n:
        return "Orange"
    return None


def _mandi_index() -> dict[str, list[tuple[str, str]]]:
    from data_layer import load_mandis

    index: dict[str, list[tuple[str, str]]] = {}
    for row in load_mandis().itertuples():
        key = _norm(row.mandi)
        index.setdefault(key, []).append((row.mandi_id, row.state))
    for alias, target in _MANDI_ALIASES.items():
        if target in {mid for mid, _ in index.get(target, [])}:
            index.setdefault(alias, []).append(index[target][0])
    return index


def _map_mandi(market: object, state: object, index: dict) -> tuple[str, str] | None:
    n = _norm(market)
    if not n:
        return None
    candidates: list[tuple[str, str]] = []
    if n in index:
        candidates.extend(index[n])
    for key, pairs in index.items():
        if len(key) >= 5 and n.startswith(key):
            candidates.extend(pairs)
    seen: set[str] = set()
    unique = []
    for pair in candidates:
        if pair[0] not in seen:
            seen.add(pair[0])
            unique.append(pair)
    if not unique:
        return None
    if len(unique) > 1 and state:
        wanted = _norm(state)
        for mandi_id, mandi_state in unique:
            actual = _norm(mandi_state)
            if actual and (actual in wanted or wanted in actual):
                return mandi_id, mandi_state
    return unique[0]


def _fetch_records() -> list[dict]:
    key = api_key()
    if not key:
        raise RuntimeError("DATA_GOV_API_KEY is not configured.")
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "CroporaAI/1.0 (student project; data.gov.in Agmarknet)"}
    )
    records: list[dict] = []
    offset = 0
    for _ in range(MAX_PAGES):
        params = {
            "api-key": key,
            "format": "json",
            "limit": PAGE_LIMIT,
            "offset": offset,
        }
        response = session.get(API_URL, params=params, timeout=45)
        if response.status_code == 401:
            raise RuntimeError("data.gov.in rejected the API key (401).")
        if response.status_code == 403:
            raise RuntimeError("data.gov.in denied access (403). Check the API key.")
        if response.status_code != 200:
            raise RuntimeError(
                f"data.gov.in returned HTTP {response.status_code}: {response.text[:160]}"
            )
        payload = response.json()
        if payload.get("error"):
            raise RuntimeError(str(payload["error"])[:200])
        batch = payload.get("records") or []
        records.extend(batch)

        total = payload.get("total")
        try:
            total = int(str(total))
        except (TypeError, ValueError):
            total = None
        if not batch or len(batch) < PAGE_LIMIT:
            break
        if total is not None and offset + len(batch) >= total:
            break
        offset += PAGE_LIMIT
        time.sleep(0.2)
    return records


def map_records(records: list[dict]) -> pd.DataFrame:
    from data_layer import load_mandis

    mandis = load_mandis().set_index("mandi_id")
    index = _mandi_index()
    rows = []
    for record in records:
        commodity = _map_commodity(record.get("commodity"))
        mapped = _map_mandi(record.get("market"), record.get("state"), index)
        price_date = _parse_date(record.get("arrival_date") or record.get("date"))
        modal = _to_float(record.get("modal_price"))
        if not commodity or not mapped or price_date is None or modal is None:
            continue
        if modal <= 0:
            continue
        mandi_id, state = mapped
        rows.append(
            {
                "price_date": price_date,
                "commodity": commodity,
                "mandi_id": mandi_id,
                "mandi": mandis.loc[mandi_id, "mandi"]
                if mandi_id in mandis.index
                else str(record.get("market") or mandi_id),
                "state": mandis.loc[mandi_id, "state"]
                if mandi_id in mandis.index
                else state,
                "min_price": _to_float(record.get("min_price")),
                "max_price": _to_float(record.get("max_price")),
                "modal_price": modal,
                "variety": str(record.get("variety") or ""),
            }
        )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    agg = (
        df.groupby(["price_date", "commodity", "mandi_id"], as_index=False)
        .agg(
            mandi=("mandi", "first"),
            state=("state", "first"),
            min_price=("min_price", "min"),
            max_price=("max_price", "max"),
            modal_price=("modal_price", "median"),
            variety_count=("variety", "nunique"),
        )
        .reset_index(drop=True)
    )
    agg["min_price"] = agg["min_price"].fillna(agg["modal_price"]).round(0)
    agg["max_price"] = agg["max_price"].fillna(agg["modal_price"]).round(0)
    agg["modal_price"] = agg["modal_price"].round(0)
    return agg.sort_values(["price_date", "commodity", "mandi_id"])


def _save(df: pd.DataFrame) -> int:
    fetched_at = datetime.now().isoformat(timespec="seconds")
    columns = LIVE_COLS
    values = df.assign(
        price_date=pd.to_datetime(df["price_date"]).dt.strftime("%Y-%m-%d"),
        variety_count=df["variety_count"].astype(int),
        source=SOURCE,
        fetched_at=fetched_at,
    )[columns].copy()
    for col in ("min_price", "max_price", "modal_price"):
        values[col] = values[col].astype(float)
    placeholders = "(" + ",".join(["?"] * len(columns)) + ")"
    updates = ", ".join(
        f"{col}=excluded.{col}"
        for col in columns
        if col not in {"price_date", "commodity", "mandi_id"}
    )
    saved = 0
    with db.connect() as conn:
        for start in range(0, len(values), 50):
            chunk = values.iloc[start : start + 50]
            sql = (
                f"INSERT INTO live_prices ({','.join(columns)}) VALUES "
                + ",".join([placeholders] * len(chunk))
                + f" ON CONFLICT(price_date, commodity, mandi_id) DO UPDATE SET {updates}"
            )
            params = [
                value.item() if hasattr(value, "item") else value
                for row in chunk.itertuples(index=False)
                for value in row
            ]
            conn.execute(sql, params)
            saved += len(chunk)
        conn.commit()
        db.meta_set(conn, "live_last_sync", fetched_at)
        db.meta_set(conn, "live_last_error", "")
        db.meta_set(conn, "live_last_source_date", str(df["price_date"].max().date()))
        db.meta_set(
            conn,
            "live_last_counts",
            json.dumps(
                {
                    "rows": int(len(df)),
                    "commodities": int(df["commodity"].nunique()),
                    "mandis": int(df["mandi_id"].nunique()),
                }
            ),
        )
    return saved


def sync_live_prices() -> dict:
    """Fetch, map and cache current Agmarknet prices. Returns a status dict."""
    if not is_configured():
        return {
            "ok": False,
            "configured": False,
            "message": "Add DATA_GOV_API_KEY to .streamlit/secrets.toml to fetch live prices.",
        }
    try:
        records = _fetch_records()
        mapped = map_records(records)
        if mapped.empty:
            raise RuntimeError(
                "No records matched the app's 13 commodities and 18 mandis. "
                "The API may be reporting different market names today."
            )
        saved = _save(mapped)
        from data_layer import refresh_live_caches

        refresh_live_caches()
        return {
            "ok": True,
            "configured": True,
            "message": f"Synced {saved:,} live prices from Agmarknet.",
            "fetched": len(records),
            "saved": saved,
            "commodities": int(mapped["commodity"].nunique()),
            "mandis": int(mapped["mandi_id"].nunique()),
            "price_date": str(mapped["price_date"].max().date()),
        }
    except Exception as exc:
        message = _redact(str(exc))
        lowered = message.lower()
        if any(
            part in lowered
            for part in ("no route to host", "connection refused", "timed out", "timeout")
        ):
            message += (
                " - data.gov.in only accepts requests from Indian networks, so cloud "
                "deployments cannot fetch directly. They show the bundled snapshot; "
                "refresh it with `python scripts/export_live_snapshot.py` from an "
                "Indian network and push the commit."
            )
        try:
            with db.connect() as conn:
                db.meta_set(conn, "live_last_error", message[:400])
        except Exception:
            pass
        return {"ok": False, "configured": True, "message": message}


def load_live_prices() -> pd.DataFrame:
    """Cached live rows, falling back to the bundled snapshot. Oldest first."""
    df = pd.DataFrame(columns=LIVE_COLS)
    try:
        with db.connect() as conn:
            rows = conn.execute(
                f"SELECT {','.join(LIVE_COLS)} FROM live_prices ORDER BY price_date"
            ).fetchall()
        df = pd.DataFrame(rows, columns=LIVE_COLS)
    except Exception:
        pass
    if df.empty:
        snapshot, _ = _load_snapshot()
        return snapshot
    df["price_date"] = pd.to_datetime(df["price_date"])
    for col in ("min_price", "max_price", "modal_price", "variety_count"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_latest_live() -> pd.DataFrame:
    df = load_live_prices()
    if df.empty:
        return df
    idx = df.groupby(["commodity", "mandi_id"])["price_date"].idxmax()
    latest = df.loc[idx].copy()
    return latest.rename(
        columns={
            "price_date": "live_date",
            "min_price": "live_min_price",
            "max_price": "live_max_price",
            "modal_price": "live_price",
            "variety_count": "live_variety_count",
        }
    )[
        [
            "commodity",
            "mandi_id",
            "live_date",
            "live_price",
            "live_min_price",
            "live_max_price",
            "live_variety_count",
            "fetched_at",
        ]
    ].reset_index(drop=True)


def get_status() -> dict:
    snapshot, snapshot_synced = _load_snapshot()
    status = {
        "configured": is_configured(),
        "backend": db.backend_label(),
        "last_sync": db.meta_get("live_last_sync"),
        "last_error": _redact(db.meta_get("live_last_error")),
        "rows": 0,
        "commodities": 0,
        "mandis": 0,
        "latest_date": None,
        "db_error": "",
        "snapshot": False,
        "snapshot_synced_at": snapshot_synced,
    }
    try:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT commodity), COUNT(DISTINCT mandi_id),"
                " MAX(price_date) FROM live_prices"
            ).fetchone()
        if row:
            status["rows"] = int(row[0] or 0)
            status["commodities"] = int(row[1] or 0)
            status["mandis"] = int(row[2] or 0)
            status["latest_date"] = row[3]
    except Exception as exc:
        status["db_error"] = str(exc)
    if status["rows"] == 0 and not snapshot.empty:
        status["rows"] = int(len(snapshot))
        status["commodities"] = int(snapshot["commodity"].nunique())
        status["mandis"] = int(snapshot["mandi_id"].nunique())
        status["latest_date"] = str(snapshot["price_date"].max().date())
        status["snapshot"] = True
    return status
