"""Generate reproducible Agmarknet-style sample data for Cropora AI.

Live Agmarknet / data.gov.in feeds require API keys or are captcha-protected,
so this project ships with a deterministic synthetic dataset that mimics the
shape of real mandi modal prices: harvest seasonality, harvest-time price dips,
festival demand, mandi-level price spreads and day-to-day volatility.

Run:  python scripts/generate_sample_data.py
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
END_DATE = date(2026, 11, 20)
N_DAYS = 730
SEED = 20261120

# commodity | category | base price (Rs/quintal) | harvest month (price trough)
# | seasonal amplitude | daily volatility | annual drift | festival bump
CROPS = [
    ("Wheat", "Crop", 2450, 4, 0.06, 0.004, 0.04, 0.00),
    ("Paddy (Rice)", "Crop", 2250, 10, 0.06, 0.004, 0.03, 0.00),
    ("Maize", "Crop", 2100, 9, 0.09, 0.006, 0.04, 0.02),
    ("Soybean", "Crop", 4700, 10, 0.10, 0.007, 0.05, 0.01),
    ("Cotton", "Crop", 7300, 11, 0.08, 0.006, 0.03, 0.01),
    ("Onion", "Crop", 1850, 4, 0.30, 0.016, 0.05, 0.06),
    ("Tomato", "Crop", 1600, 1, 0.32, 0.020, 0.05, 0.03),
    ("Potato", "Crop", 1450, 2, 0.18, 0.009, 0.04, 0.05),
    ("Banana", "Fruit", 1900, 7, 0.10, 0.008, 0.04, 0.02),
    ("Mango", "Fruit", 6200, 5, 0.30, 0.012, 0.05, 0.00),
    ("Apple", "Fruit", 8200, 10, 0.15, 0.006, 0.04, 0.04),
    ("Grapes", "Fruit", 5600, 3, 0.22, 0.014, 0.05, 0.00),
    ("Orange", "Fruit", 4100, 12, 0.18, 0.010, 0.04, 0.02),
]

MANDIS = [
    ("khanna", "Khanna", "Punjab", 30.7046, 76.2225),
    ("ludhiana", "Ludhiana", "Punjab", 30.9010, 75.8573),
    ("karnal", "Karnal", "Haryana", 29.6857, 76.9905),
    ("azadpur", "Azadpur", "Delhi", 28.7169, 77.1703),
    ("jaipur", "Jaipur", "Rajasthan", 26.9124, 75.7873),
    ("kota", "Kota", "Rajasthan", 25.2138, 75.8648),
    ("indore", "Indore", "Madhya Pradesh", 22.7196, 75.8577),
    ("nashik", "Nashik", "Maharashtra", 19.9975, 73.7898),
    ("pune", "Pune", "Maharashtra", 18.5204, 73.8567),
    ("nagpur", "Nagpur", "Maharashtra", 21.1458, 79.0882),
    ("hyderabad", "Hyderabad", "Telangana", 17.3850, 78.4867),
    ("guntur", "Guntur", "Andhra Pradesh", 16.3067, 80.4365),
    ("bengaluru", "Bengaluru", "Karnataka", 13.0284, 77.5197),
    ("mysuru", "Mysuru", "Karnataka", 12.2958, 76.6394),
    ("ahmedabad", "Ahmedabad", "Gujarat", 23.0225, 72.5714),
    ("kolkata", "Kolkata", "West Bengal", 22.5726, 88.3639),
    ("lucknow", "Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    ("patna", "Patna", "Bihar", 25.5941, 85.1376),
]

AVAILABILITY = {
    "Wheat": ["khanna", "ludhiana", "karnal", "jaipur", "kota", "indore", "lucknow", "patna", "ahmedabad"],
    "Paddy (Rice)": ["karnal", "ludhiana", "patna", "kolkata", "lucknow", "hyderabad", "guntur"],
    "Maize": ["indore", "lucknow", "patna", "hyderabad", "guntur", "jaipur", "kota"],
    "Soybean": ["indore", "nagpur", "kota", "jaipur", "pune"],
    "Cotton": ["ahmedabad", "nagpur", "guntur", "indore"],
    "Onion": ["nashik", "pune", "ahmedabad", "jaipur", "azadpur", "kolkata", "bengaluru", "indore"],
    "Tomato": ["nashik", "pune", "bengaluru", "mysuru", "azadpur", "hyderabad", "indore"],
    "Potato": ["lucknow", "patna", "azadpur", "kolkata", "indore", "ahmedabad"],
    "Banana": ["hyderabad", "bengaluru", "mysuru", "nashik", "kolkata", "ahmedabad"],
    "Mango": ["hyderabad", "bengaluru", "azadpur", "lucknow", "ahmedabad", "mysuru"],
    "Apple": ["azadpur", "jaipur", "ahmedabad", "pune", "bengaluru"],
    "Grapes": ["nashik", "pune", "bengaluru", "hyderabad", "azadpur"],
    "Orange": ["nagpur", "pune", "hyderabad", "bengaluru", "jaipur", "azadpur"],
}

SEASON_NOTES = {
    "Wheat": "Rabi crop; harvested Mar-Apr",
    "Paddy (Rice)": "Kharif crop; harvested Oct-Nov",
    "Maize": "Kharif and rabi; peak arrival Sep-Oct",
    "Soybean": "Kharif crop; harvested Oct",
    "Cotton": "Kharif crop; picking Oct-Jan",
    "Onion": "Rabi harvest Mar-Apr; storage crop",
    "Tomato": "Year-round; peak supply Dec-Feb",
    "Potato": "Rabi crop; harvested Jan-Feb",
    "Banana": "Year-round harvest",
    "Mango": "Summer crop; harvested Apr-Jun",
    "Apple": "Autumn crop; harvested Sep-Nov",
    "Grapes": "Harvested Feb-Apr",
    "Orange": "Harvested Nov-Jan",
}


def _harvest_doy(month: int) -> int:
    return date(2026, month, 15).timetuple().tm_yday


def _festival_bump(doy: np.ndarray) -> np.ndarray:
    gap = np.minimum(np.abs(doy - 296), 365 - np.abs(doy - 296))
    return np.exp(-0.5 * (gap / 12.0) ** 2)


def generate() -> pd.DataFrame:
    DATA_DIR.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    dates = [END_DATE - timedelta(days=N_DAYS - 1 - i) for i in range(N_DAYS)]
    doy = np.array([d.timetuple().tm_yday for d in dates], dtype=float)
    t = np.arange(N_DAYS, dtype=float)
    dow = np.array([d.weekday() for d in dates], dtype=float)

    mandi_ids = {m[0] for m in MANDIS}
    unknown = {m for ids in AVAILABILITY.values() for m in ids} - mandi_ids
    if unknown:
        raise ValueError(f"Unknown mandi ids: {unknown}")

    rows = []
    for name, category, base, harvest_month, amp, sigma, drift, festival in CROPS:
        harvest = _harvest_doy(harvest_month)
        season = -amp * np.cos(2 * np.pi * (doy - harvest) / 365.25)
        season += festival * _festival_bump(doy)
        market_cycle = 0.015 * np.sin(2 * np.pi * t / 420.0 + base % 7)
        for mandi_id in AVAILABILITY[name]:
            local_mult = float(np.clip(rng.normal(1.0, 0.028), 0.92, 1.09))
            level = np.log(base * local_mult) + season + market_cycle
            level += drift * (t / 365.0)
            noise = np.zeros(N_DAYS)
            eps = 0.0
            phi = 0.88
            for i in range(N_DAYS):
                eps = phi * eps + sigma * rng.normal()
                if rng.random() < 0.004:
                    eps += rng.normal(0.0, 0.035)
                noise[i] = eps
            weekend = 1.0 + 0.004 * np.sin(2 * np.pi * dow / 7.0)
            price = np.exp(level + noise) * weekend
            price = np.clip(price, 0.55 * base, 2.6 * base)
            modal = np.round(price / 5.0) * 5.0
            spread = rng.uniform(0.012, 0.035, N_DAYS)
            min_price = np.round(modal * (1 - spread) / 5.0) * 5.0
            max_price = np.round(modal * (1 + spread * 0.8) / 5.0) * 5.0
            for i, d in enumerate(dates):
                rows.append(
                    (
                        d.isoformat(),
                        name,
                        mandi_id,
                        int(modal[i]),
                        int(min_price[i]),
                        int(max_price[i]),
                    )
                )

    prices = pd.DataFrame(
        rows, columns=["date", "commodity", "mandi_id", "modal_price", "min_price", "max_price"]
    )
    prices["date"] = pd.to_datetime(prices["date"])
    prices = prices.sort_values(["commodity", "mandi_id", "date"]).reset_index(drop=True)
    prices.to_csv(DATA_DIR / "prices.csv", index=False)

    crops = pd.DataFrame(
        [
            {
                "commodity": name,
                "category": category,
                "base_price": base,
                "season_note": SEASON_NOTES[name],
            }
            for name, category, base, *_ in CROPS
        ]
    )
    crops.to_csv(DATA_DIR / "crops.csv", index=False)

    mandis = pd.DataFrame(MANDIS, columns=["mandi_id", "mandi", "state", "latitude", "longitude"])
    mandis.to_csv(DATA_DIR / "mandis.csv", index=False)

    locations = mandis[["mandi", "state", "latitude", "longitude"]].copy()
    locations = locations.rename(columns={"mandi": "location"})
    locations.to_csv(DATA_DIR / "locations.csv", index=False)

    return prices


if __name__ == "__main__":
    prices = generate()
    print(f"Wrote {len(prices):,} price rows for {prices['commodity'].nunique()} commodities")
    print(f"Mandis: {prices['mandi_id'].nunique()}, dates: {prices['date'].min().date()} to {prices['date'].max().date()}")
    print(f"Output: {DATA_DIR}")
