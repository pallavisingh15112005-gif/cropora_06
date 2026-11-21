"""Fetch live Agmarknet prices from an Indian network and bundle them for deployment.

data.gov.in only answers requests from Indian networks, so the cloud deployment
cannot fetch directly. Run this locally, then commit data/live_snapshot.json.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

import agmarknet

OUT = ROOT / "data" / "live_snapshot.json"
KEEP_DAYS = 14


def main() -> int:
    result = agmarknet.sync_live_prices()
    if not result.get("ok"):
        print(f"Sync failed: {result.get('message')}")
        return 1

    df = agmarknet.load_live_prices()
    if df.empty:
        print("Local live cache is empty after sync.")
        return 1

    cutoff = df["price_date"].max() - pd.Timedelta(days=KEEP_DAYS - 1)
    recent = df[df["price_date"] >= cutoff].sort_values(
        ["price_date", "commodity", "mandi_id"]
    )
    rows = [
        {
            "price_date": row.price_date.strftime("%Y-%m-%d"),
            "commodity": row.commodity,
            "mandi_id": row.mandi_id,
            "mandi": row.mandi,
            "state": row.state,
            "min_price": float(row.min_price),
            "max_price": float(row.max_price),
            "modal_price": float(row.modal_price),
            "variety_count": int(row.variety_count),
            "source": row.source,
            "fetched_at": row.fetched_at,
        }
        for row in recent.itertuples()
    ]
    payload = {
        "synced_at": datetime.now().isoformat(timespec="seconds"),
        "source": agmarknet.SOURCE,
        "rows": rows,
    }
    try:
        previous = json.loads(OUT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        previous = {}
    if previous.get("rows") == rows:
        print("Snapshot unchanged; keeping the existing file.")
        return 0
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(
        f"Wrote {len(rows)} rows ({recent['commodity'].nunique()} commodities, "
        f"{recent['mandi_id'].nunique()} mandis, latest {recent['price_date'].max().date()}) "
        f"to {OUT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
