"""Train the Cropora AI forecasting models and write evaluation artifacts."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from forecasting import build_all  # noqa: E402


if __name__ == "__main__":
    start = time.perf_counter()
    prices = pd.read_csv(ROOT / "data" / "prices.csv", parse_dates=["date"])
    out = build_all(prices)
    elapsed = time.perf_counter() - start
    print(out["metrics"].to_string(index=False))
    info = out["info"].iloc[0]
    print(f"\nAverage MAPE, all horizons : {info['avg_mape']}%")
    print(f"Average MAPE, 7-day ahead  : {info['avg_mape_h7']}%")
    print(f"Average R2                 : {info['avg_r2']}")
    print(f"Backtest predictions       : {info['total_predictions']:,}")
    print(f"Forecast rows written      : {len(out['forecasts']):,}")
    print(f"Build time                 : {elapsed:.1f}s")
    print(f"Artifacts                  : {ROOT / 'artifacts'}")
