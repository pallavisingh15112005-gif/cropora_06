import pandas as pd
import streamlit as st

from data_layer import (
    fmt_date,
    fmt_inr,
    fmt_pct,
    forecast_path,
    forecast_summary,
    load_metrics,
    mandi_name,
    mandi_rows_for,
)
from ui import page_header, price_forecast_chart, section

page_header("Prices & 7-day forecast")

summary = forecast_summary()
crops = sorted(summary["commodity"].unique())
crop = st.selectbox(
    "Crop", crops, index=crops.index("Wheat") if "Wheat" in crops else 0, key="pf_crop"
)

location = st.session_state.get("location", "Ludhiana")
crop_rows = mandi_rows_for(crop, location).sort_values("distance_km")
labels = {
    row.mandi_id: f"{row.mandi} — {row.state}" for row in crop_rows.itertuples()
}
mandi_id = st.selectbox(
    "Mandi",
    crop_rows["mandi_id"].tolist(),
    format_func=lambda value: labels.get(value, value),
    key="pf_mandi",
)
row = crop_rows[crop_rows["mandi_id"] == mandi_id].iloc[0]
metrics = load_metrics()
metric_row = metrics[metrics["commodity"] == crop].iloc[0]

cards = st.columns(4)
with cards[0]:
    with st.container(border=True):
        st.metric("Modal price today", f"{fmt_inr(row['modal_price'])}/qtl")
        st.caption(f"Range {fmt_inr(row['min_price'])}–{fmt_inr(row['max_price'])}")
with cards[1]:
    with st.container(border=True):
        st.metric(
            "Day-7 forecast",
            f"{fmt_inr(row['forecast_price'])}/qtl",
            delta=f"{row['change_pct']:+.1f}%",
        )
        st.caption(f"For {fmt_date(row['forecast_date'])}")
with cards[2]:
    with st.container(border=True):
        st.metric("80% forecast range", f"{fmt_inr(row['lower'])}–{fmt_inr(row['upper'])}")
        st.caption("Estimated from the rolling-origin backtest")
with cards[3]:
    with st.container(border=True):
        st.metric("Model MAPE (7-day)", f"{metric_row['mape_h7']:.2f}%")

st.write("")
st.plotly_chart(
    price_forecast_chart(crop, mandi_id),
    width="stretch",
    config={"displayModeBar": False},
)

left, right = st.columns([1.15, 1], gap="large")
with left:
    section(
        "Seven-day path",
        f"{crop} at {mandi_name(mandi_id)} · today {fmt_inr(row['modal_price'])}/qtl",
    )
    path = forecast_path(crop, mandi_id)
    table = pd.DataFrame(
        {
            "Date": path["date"].dt.strftime("%d %b %Y"),
            "Forecast": path["forecast_price"].map(fmt_inr),
            "80% low": path["lower"].map(fmt_inr),
            "80% high": path["upper"].map(fmt_inr),
            "Vs today": ((path["forecast_price"] / row["modal_price"] - 1) * 100).map(fmt_pct),
        }
    )
    st.dataframe(table, hide_index=True, width="stretch")
with right:
    section("About this forecast")
    st.markdown(
        f"""
- **Model:** ridge regression trained on daily prices for {crop}.
- **Training data:** the sample Agmarknet-style history. When a live price is cached, today's price and the forecast level are anchored to it.
- **Inputs:** prices from 1–30 days ago, 7/14/30-day averages, short-term momentum, day-of-year seasonality and mandi identity.
- **Validation:** 28 rolling origins with recursive 7-day forecasts, compared with actual prices.
- **Accuracy here:** {metric_row['mape_h7']:.2f}% MAPE at day 7, MAE {fmt_inr(metric_row['mae'])}/qtl.
- **Range:** the shaded band is an estimated 80% interval, not a guarantee.
"""
    )

st.write("")
section("Other mandis for this crop")
others = crop_rows.sort_values("modal_price", ascending=False)[
    ["mandi", "state", "modal_price", "forecast_price", "change_pct"]
].copy()
others["modal_price"] = others["modal_price"].map(fmt_inr)
others["forecast_price"] = others["forecast_price"].map(fmt_inr)
others["change_pct"] = others["change_pct"].map(fmt_pct)
others.columns = ["Mandi", "State", "Today", "Day-7 forecast", "7-day move"]
st.dataframe(others, hide_index=True, width="stretch")
