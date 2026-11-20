"""Deterministic rule-based chatbot for Cropora AI.

Answers are generated from the same data layer, forecasts and curated scheme /
disease knowledge used by the rest of the app. No LLM or API key is required.
"""

from __future__ import annotations

import re

import pandas as pd

import knowledge
from data_layer import (
    crop_outlook,
    fmt_date,
    fmt_inr,
    fmt_pct,
    forecast_path,
    forecast_summary,
    load_locations,
    load_metrics,
    load_model_info,
    mandi_rows_for,
    mandis_with_distance,
    market_date,
    sell_plan,
)

CROP_ALIASES = {
    "wheat": "Wheat",
    "gehun": "Wheat",
    "paddy": "Paddy (Rice)",
    "rice": "Paddy (Rice)",
    "dhan": "Paddy (Rice)",
    "maize": "Maize",
    "makka": "Maize",
    "corn": "Maize",
    "soybean": "Soybean",
    "soyabean": "Soybean",
    "soya": "Soybean",
    "cotton": "Cotton",
    "kapas": "Cotton",
    "onion": "Onion",
    "pyaz": "Onion",
    "tomato": "Tomato",
    "tamatar": "Tomato",
    "potato": "Potato",
    "aloo": "Potato",
    "banana": "Banana",
    "kela": "Banana",
    "mango": "Mango",
    "aam": "Mango",
    "apple": "Apple",
    "seb": "Apple",
    "grapes": "Grapes",
    "grape": "Grapes",
    "angoor": "Grapes",
    "orange": "Orange",
    "santra": "Orange",
}

MANDI_ALIASES = {
    "delhi": "azadpur",
    "bangalore": "bengaluru",
    "mysore": "mysuru",
    "new delhi": "azadpur",
}

LOCATION_ALIASES = {
    "bangalore": "Bengaluru",
    "mysore": "Mysuru",
    "new delhi": "Delhi",
}

CROP_LIST = "wheat, paddy, maize, soybean, cotton, onion, tomato, potato, banana, mango, apple, grapes or orange"

INTENT_WORDS = {
    "disease": [
        "disease", "symptom", "blight", "rust", "rot", "wilt", "pest", "fungus",
        "infection", "remedy", "cure", "insect", "borer", "hopper", "mildew",
        "scab", "canker", "curl", "spot", "spots", "stripe", "stripes", "powder",
        "mosaic", "lesion", "lesions", "yellowing", "pesticide", "spray",
    ],
    "scheme": [
        "scheme", "subsidy", "government", "loan", "credit", "insurance",
        "pm-kisan", "pmkisan", "pmfby", "kcc", "yojana", "sarkari", "apply for",
    ],
    "accuracy": ["accuracy", "accurate", "mape", "model", "prediction error", "reliable", "how correct"],
    "alert": ["alert", "target price", "notify", "reminder", "crosses", "reaches", "target"],
    "nearby": ["nearby", "near me", "nearest", "distance", "closest", "how far", "map", "mandis near", "near"],
    "grow": ["grow", "sow", "plant", "next season", "which crop", "best crop", "profitable", "growing"],
    "sell": ["sell", "hold", "wait", "where should", "best mandi", "which mandi"],
    "forecast": ["forecast", "predict", "next week", "7 day", "seven day", "future", "tomorrow", "expected"],
    "compare": ["compare", "highest", "cheapest", "across mandi", "price difference", "spread"],
    "price": ["price", "rate", "bhav", "mandi", "cost", "today"],
}


def _has(text: str, words: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def find_location(text: str) -> str | None:
    text = text.lower()
    locations = load_locations()["location"].tolist()
    for name in sorted(locations, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name.lower())}\b", text):
            return name
    for alias, canonical in sorted(LOCATION_ALIASES.items(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return canonical
    return None


def find_crop(text: str) -> str | None:
    text = text.lower()
    for alias in sorted(CROP_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return CROP_ALIASES[alias]
    return None


def find_mandi(text: str, mandi_ids: list[str] | None = None) -> str | None:
    text = text.lower()
    aliases = {**MANDI_ALIASES}
    for mandi_id in (mandi_ids or []):
        aliases.setdefault(mandi_id, mandi_id)
    names = {
        "khanna": "khanna", "ludhiana": "ludhiana", "karnal": "karnal",
        "azadpur": "azadpur", "jaipur": "jaipur", "kota": "kota",
        "indore": "indore", "nashik": "nashik", "pune": "pune", "nagpur": "nagpur",
        "hyderabad": "hyderabad", "guntur": "guntur", "bengaluru": "bengaluru",
        "mysuru": "mysuru", "ahmedabad": "ahmedabad", "kolkata": "kolkata",
        "lucknow": "lucknow", "patna": "patna",
    }
    aliases.update(names)
    for alias in sorted(aliases, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return aliases[alias]
    return None


def _pick_row(commodity: str, location: str, requested_mandi: str | None) -> pd.Series | None:
    rows = mandi_rows_for(commodity, location)
    if rows.empty:
        return None
    if requested_mandi and requested_mandi in set(rows["mandi_id"]):
        return rows[rows["mandi_id"] == requested_mandi].iloc[0]
    return rows.sort_values("distance_km").iloc[0]


def _today_label() -> str:
    return fmt_date(market_date())


def _price_answer(commodity: str, location: str, requested_mandi: str | None) -> str:
    rows = mandi_rows_for(commodity, location)
    row = _pick_row(commodity, location, requested_mandi)
    if row is None:
        return f"I do not have {commodity} prices for that mandi."
    top = rows.assign(
        distance_km=rows["distance_km"]
    ).sort_values("net_price_now", ascending=False).head(3)
    where = "" if requested_mandi else f" · {row['distance_km']:.0f} km from {location}"
    lines = [
        f"**{commodity} — {_today_label()}**",
        "",
        f"- {row['mandi']} ({row['state']}): **{fmt_inr(row['modal_price'])}/qtl**{where}",
    ]
    for other in top.itertuples():
        if other.mandi_id != row["mandi_id"]:
            lines.append(
                f"- {other.mandi}: {fmt_inr(other.modal_price)}/qtl"
                f" · {other.distance_km:.0f} km"
            )
    lines.append(
        f"- 7-day forecast at {row['mandi']}: {fmt_inr(row['forecast_price'])}/qtl "
        f"({fmt_pct(row['change_pct'])})"
    )
    lines.append("")
    if row.get("price_source") == "Agmarknet live":
        lines.append("_Live Agmarknet price via data.gov.in. Confirm before selling._")
    else:
        lines.append("_Sample data for this mandi, not a live feed. Confirm before selling._")
    return "\n".join(lines)


def _forecast_answer(commodity: str, location: str, requested_mandi: str | None) -> str:
    row = _pick_row(commodity, location, requested_mandi)
    if row is None:
        return f"I do not have a forecast for {commodity}."
    fc = forecast_path(commodity, row["mandi_id"])
    series = fc.sort_values("horizon")
    metrics = load_metrics()
    mrow = metrics[metrics["commodity"] == commodity]
    path = " → ".join(f"{int(r.forecast_price):,}" for r in series.itertuples())
    lines = [
        f"**7-day forecast — {commodity} at {row['mandi']}**",
        "",
        f"- Today: {fmt_inr(row['modal_price'])}/qtl · Day 7 ({fmt_date(row['forecast_date'])}): "
        f"**{fmt_inr(row['forecast_price'])}** ({fmt_pct(row['change_pct'])})",
        f"- 80% range on day 7: {fmt_inr(row['lower'])}–{fmt_inr(row['upper'])}/qtl",
        f"- Daily path: {path}",
    ]
    if len(mrow):
        lines.append(
            f"- Model accuracy for {commodity}: MAPE {mrow.iloc[0]['mape_h7']:.2f}% over the 7-day backtest"
        )
    lines.append("")
    lines.append(
        "_Forecast level is anchored to the latest cached price; the model is "
        "trained on the sample history. Use it as one input, not a guarantee._"
    )
    return "\n".join(lines)


def _compare_answer(commodity: str, location: str) -> str:
    rows = mandi_rows_for(commodity, location).sort_values("net_price_now", ascending=False)
    if rows.empty:
        return f"I do not have mandi prices for {commodity}."
    top = rows.head(5)
    lines = [f"**{commodity} across mandis — {_today_label()}**", ""]
    lines.append("| Mandi | Price | Distance | Net after transport |")
    lines.append("|---|---|---|---|")
    for r in top.itertuples():
        lines.append(
            f"| {r.mandi} | {fmt_inr(r.modal_price)} | {r.distance_km:.0f} km | "
            f"{fmt_inr(r.net_price_now)} |"
        )
    spread = rows["modal_price"].max() - rows["modal_price"].min()
    best = top.iloc[0]
    lines.append("")
    lines.append(
        f"Spread between the highest and lowest price is **{fmt_inr(spread)}/qtl**. "
        f"Best net price near {location}: **{best['mandi']}** at {fmt_inr(best['net_price_now'])}/qtl."
    )
    lines.append("Transport assumed at ₹0.10 per quintal per km.")
    return "\n".join(lines)


def _sell_answer(commodity: str, location: str, requested_mandi: str | None = None) -> str:
    plan = sell_plan(commodity, location, mandi_id=requested_mandi)
    if not plan:
        return f"I do not have enough data for {commodity}."
    now = plan["best_now"]
    later = plan["best_later"]
    lines = [
        f"**Sell or hold — {commodity} near {location}**",
        "",
        f"- Best today: **{now['mandi']}** at {fmt_inr(now['modal_price'])}/qtl "
        f"({fmt_inr(now['net_price_now'])} net after {fmt_inr(now['transport_cost'])} transport)",
        f"- Best 7-day option: **{later['mandi']}** at {fmt_inr(later['net_price_d7'])} net "
        f"({fmt_date(later['forecast_date'])})",
        f"- Expected change in net price: {fmt_pct(plan['change_pct'])}",
        f"- **Advice: {plan['stance']}.** {plan['reason']}",
        "",
        "Transport is assumed at ₹0.10/qtl/km. This is a short-term market view, not a guarantee.",
    ]
    return "\n".join(lines)


def _where_answer(commodity: str, location: str) -> str:
    rows = mandi_rows_for(commodity, location).sort_values("net_price_d7", ascending=False).head(3)
    if rows.empty:
        return f"I do not have mandi prices for {commodity}."
    lines = [f"**Where to sell {commodity} near {location}**", ""]
    for i, r in enumerate(rows.itertuples(), start=1):
        lines.append(
            f"{i}. {r.mandi} ({r.distance_km:.0f} km): today {fmt_inr(r.modal_price)}, "
            f"day-7 forecast {fmt_inr(r.forecast_price)}, net {fmt_inr(r.net_price_d7)} after transport."
        )
    lines.append("")
    lines.append("Ranked by forecast net price after an assumed ₹0.10/qtl/km transport cost.")
    return "\n".join(lines)


def _grow_answer() -> str:
    outlook = crop_outlook().head(4)
    lines = ["**Strongest 7-day market outlook this week**", ""]
    for i, row in enumerate(outlook.itertuples(), start=1):
        lines.append(
            f"{i}. **{row.commodity}** — outlook score {int(row.outlook_score)}/100, "
            f"7-day move {fmt_pct(row.change_pct)}, volatility {row.volatility_pct:.2f}%, "
            f"{fmt_pct(row.vs_year_pct)} vs its 1-year average."
        )
    lines.append("")
    lines.append(
        "Score = 50% price momentum + 25% stability + 25% value versus the yearly average. "
        "This is a market outlook for the week, not a full-season crop plan; check soil, water and local agronomy advice."
    )
    return "\n".join(lines)


def _nearby_answer(location: str, crop: str | None) -> str:
    dist = mandis_with_distance(location).sort_values("distance_km").head(4)
    lines = [f"**Nearest mandis to {location}**", ""]
    for r in dist.itertuples():
        line = f"- {r.mandi} ({r.state}) — {r.distance_km:.0f} km"
        if crop:
            price = forecast_summary()
            match = price[(price["commodity"] == crop) & (price["mandi_id"] == r.mandi_id)]
            if len(match):
                line += f" · {crop}: {fmt_inr(match.iloc[0]['modal_price'])}/qtl"
        lines.append(line)
    if not crop:
        lines.append("")
        lines.append("Ask for a crop price at any of these mandis, for example: wheat in Karnal.")
    return "\n".join(lines)


def _disease_answer(crop: str | None, text: str) -> str:
    if crop is None:
        return (
            "Which crop's problem are you seeing? I cover wheat, paddy, maize, soybean, cotton, "
            "onion, tomato, potato, banana, mango, apple, grapes and orange. You can also use the "
            "Crop diseases page to tick symptoms."
        )
    matches = knowledge.find_diseases_by_text(crop, text)
    lines = [f"**{crop} — likely issues**", ""]
    for disease in matches:
        lines.append(f"**{disease['name']}** ({disease['type']})")
        lines.append(f"- Signs: {', '.join(disease['symptoms'][:2]).lower()}.")
        lines.append(f"- What to do: {disease['remedy']}")
    lines.append("")
    lines.append(
        "Use the Crop diseases page for a symptom-based check. Spray only at label doses and confirm with your local KVK or agriculture officer."
    )
    return "\n".join(lines)


def _scheme_answer(crop: str | None) -> str:
    category = None
    if crop:
        from data_layer import load_crops

        rows = load_crops()
        match = rows[rows["commodity"] == crop]
        category = match.iloc[0]["category"] if len(match) else None
    schemes = knowledge.schemes_for_crop(crop, category)[:4]
    title = f"**Government schemes for {crop}**" if crop else "**Government schemes for farmers**"
    lines = [title, ""]
    for s in schemes:
        lines.append(f"**{s['name']}** — {s['benefit']}")
        lines.append(f"- Eligibility: {s['eligibility']}")
        lines.append(f"- How to apply: {s['apply']}")
        lines.append(f"- Portal: {s['link']}")
        lines.append("")
    lines.append("Scheme rules change; verify current terms on the official portal.")
    return "\n".join(lines)


def _accuracy_answer() -> str:
    info = load_model_info()
    metrics = load_metrics()
    best = metrics.sort_values("mape_h7").iloc[0]
    worst = metrics.sort_values("mape_h7").iloc[-1]
    return "\n".join(
        [
            "**How accurate is the price forecast?**",
            "",
            f"- 7-day-ahead average MAPE: **{info['avg_mape_h7']}%** across {len(metrics)} commodities",
            f"- Best: {best['commodity']} at {best['mape_h7']}% · Hardest: {worst['commodity']} at {worst['mape_h7']}%",
            f"- Average R²: {info['avg_r2']}",
            f"- Evaluated with {info['total_predictions']:,} predictions from a rolling-origin backtest",
            "",
            "The model is ridge regression using lagged prices, rolling averages, momentum and seasonality. "
            "Metrics come from synthetic sample data, so real mandi accuracy will differ.",
        ]
    )


def _alert_answer(text: str) -> str:
    numbers = re.findall(r"\b(\d{3,6})\b", text)
    lines = ["**Setting a price alert**", ""]
    lines.append(
        "Open the **Price alerts** page, choose the crop and mandi, enter your target price and whether you want to be alerted when the price rises to it or falls to it."
    )
    if numbers:
        lines.append("")
        lines.append(
            f"I noticed {numbers[0]} in your message — enter that as the target. Alerts are checked against the latest cached market price ({_today_label()})."
        )
    else:
        lines.append("")
        lines.append(
            "Example: for wheat at Karnal today, set a target of ₹2,800 with 'Rises to or above'. "
            "The alert appears on the dashboard when the latest price crosses it."
        )
    return "\n".join(lines)


def _help_answer() -> str:
    return "\n".join(
        [
            "**I can help with:**",
            "",
            "- Today's mandi prices and 7-day forecasts",
            "- Where to sell, and which crop has the strongest outlook",
            "- Nearby mandis and distances",
            "- Crop disease symptoms and remedies",
            "- Government schemes and how to apply",
            "- How accurate the price model is",
            "",
            "Try: \"tomato price in Nashik\", \"forecast wheat near Ludhiana\", "
            "\"yellow spots on tomato leaves\" or \"should I sell paddy now?\"",
        ]
    )


def respond(question: str, location: str = "Ludhiana") -> str:
    text = (question or "").strip().lower()
    if not text:
        return _help_answer()

    crop = find_crop(text)
    requested_mandi = find_mandi(text)
    resolved_location = find_location(text) or location

    if _has(text, INTENT_WORDS["disease"]):
        return _disease_answer(crop, text)
    if _has(text, INTENT_WORDS["scheme"]):
        return _scheme_answer(crop)
    if _has(text, INTENT_WORDS["accuracy"]):
        return _accuracy_answer()
    if _has(text, INTENT_WORDS["alert"]):
        return _alert_answer(text)
    if _has(text, INTENT_WORDS["grow"]):
        return _grow_answer()
    if _has(text, INTENT_WORDS["sell"]):
        if crop is None:
            top = crop_outlook().iloc[0]
            return (
                f"Tell me which crop you want to sell. For a quick view, **{top['commodity']}** "
                f"has the strongest 7-day outlook right now ({fmt_pct(top['change_pct'])}).\n\n"
                + _sell_answer(top["commodity"], resolved_location, requested_mandi)
            )
        if "where" in text:
            return _where_answer(crop, resolved_location)
        return _sell_answer(crop, resolved_location, requested_mandi)
    if _has(text, INTENT_WORDS["forecast"]):
        if crop is None:
            top = crop_outlook().iloc[0]["commodity"]
            return (
                f"I picked **{top}**, the strongest crop outlook this week. "
                "Ask about another crop by name.\n\n"
                + _forecast_answer(top, resolved_location, requested_mandi)
            )
        return _forecast_answer(crop, resolved_location, requested_mandi)
    if _has(text, INTENT_WORDS["compare"]):
        if crop is None:
            return "Which crop should I compare across mandis? For example: \"compare onion across mandis\"."
        return _compare_answer(crop, resolved_location)
    if _has(text, INTENT_WORDS["nearby"]):
        return _nearby_answer(resolved_location, crop)
    if _has(text, INTENT_WORDS["price"]):
        if crop is None:
            return f"Which crop's price do you want? I cover {CROP_LIST}."
        return _price_answer(crop, resolved_location, requested_mandi)
    if re.search(r"\b(hi|hello|hey|namaste|namaskar)\b", text):
        return "Namaste. Ask me about crop prices, a 7-day forecast, where to sell, diseases, schemes or the model's accuracy."
    if re.search(r"\b(thanks|thank you|dhanyavad|shukriya)\b", text):
        return "You're welcome. Ask another question whenever you like."
    if _has(text, ["help", "what can you do", "how to use", "guide"]):
        return _help_answer()
    return (
        "I could not map that to a market question. I can help with prices, 7-day forecasts, "
        "sell or hold advice, nearby mandis, crop diseases, government schemes and model accuracy. "
        "Try: \"onion price in Nashik\" or \"best crop to grow this week\"."
    )
