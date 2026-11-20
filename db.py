"""Turso/libSQL persistence with a local file fallback.

When TURSO_DATABASE_URL and TURSO_AUTH_TOKEN are configured the app talks to
Turso Cloud. Otherwise it uses data/cropora.db through the same libSQL driver,
so the app still runs before credentials are added.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import libsql

ROOT = Path(__file__).resolve().parent
LOCAL_DB = ROOT / "data" / "cropora.db"

_schema_ready: set[str] = set()


def _secret(name: str) -> str:
    try:
        import streamlit as st

        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except Exception:
        pass
    return (os.environ.get(name) or "").strip()


def turso_config() -> tuple[str, str]:
    return _secret("TURSO_DATABASE_URL"), _secret("TURSO_AUTH_TOKEN")


def is_remote() -> bool:
    return bool(turso_config()[0])


def backend_label() -> str:
    return "Turso Cloud" if is_remote() else "Local libSQL file"


def _init_schema(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commodity TEXT NOT NULL,
            mandi_id TEXT NOT NULL,
            target_price REAL NOT NULL,
            direction TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS live_prices (
            price_date TEXT NOT NULL,
            commodity TEXT NOT NULL,
            mandi_id TEXT NOT NULL,
            mandi TEXT NOT NULL,
            state TEXT NOT NULL,
            min_price REAL,
            max_price REAL,
            modal_price REAL NOT NULL,
            variety_count INTEGER NOT NULL DEFAULT 1,
            source TEXT NOT NULL DEFAULT 'Agmarknet',
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (price_date, commodity, mandi_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_live_prices_pair
        ON live_prices (commodity, mandi_id, price_date DESC)
        """
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    conn.commit()


@contextmanager
def connect():
    url, token = turso_config()
    key = url or str(LOCAL_DB)
    if url:
        conn = libsql.connect(database=url, auth_token=token)
    else:
        LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = libsql.connect(database=str(LOCAL_DB))
    try:
        if key not in _schema_ready:
            _init_schema(conn)
            _schema_ready.add(key)
        yield conn
    finally:
        conn.close()


def meta_get(key: str, default: str = "") -> str:
    try:
        with connect() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return str(row[0]) if row else default
    except Exception:
        return default


def meta_set(conn, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
