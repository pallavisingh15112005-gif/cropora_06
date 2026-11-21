import pandas as pd
import streamlit as st

from data_layer import (
    fmt_inr,
    fmt_pct,
    forecast_summary,
    mandi_rows_for,
)
from ui import mandi_price_chart, page_header, section

page_header("Compare mandis")

summary = forecast_summary()
crops = sorted(summary["commodity"].unique())
crop = st.selectbox(
    "Crop", crops, index=crops.index("Onion") if "Onion" in crops else 0, key="cmp_crop"
)
location = st.session_state.get("location", "Ludhiana")
rows = mandi_rows_for(crop, location).sort_values("net_price_now", ascending=False)

if rows.empty:
    st.warning("No mandi data for this crop.")
    st.stop()

high = rows.loc[rows["modal_price"].idxmax()]
low = rows.loc[rows["modal_price"].idxmin()]
best_net = rows.iloc[0]
spread = high["modal_price"] - low["modal_price"]

cards = st.columns(4)
with cards[0]:
    with st.container(border=True):
        st.metric("Highest price", f"{fmt_inr(high['modal_price'])}/qtl")
        st.caption(high["mandi"])
with cards[1]:
    with st.container(border=True):
        st.metric("Lowest price", f"{fmt_inr(low['modal_price'])}/qtl")
        st.caption(low["mandi"])
with cards[2]:
    with st.container(border=True):
        st.metric("Price spread", f"{fmt_inr(spread)}/qtl")
        st.caption("Between the highest and lowest mandi")
with cards[3]:
    with st.container(border=True):
        st.metric("Best net near you", fmt_inr(best_net["net_price_now"]))
        st.caption(f"{best_net['mandi']} · {best_net['distance_km']:.0f} km · after transport")

st.write("")
st.plotly_chart(
    mandi_price_chart(rows),
    width="stretch",
    config={"displayModeBar": False},
)

section("Full comparison")
table = rows[
    ["mandi", "state", "distance_km", "modal_price", "transport_cost", "net_price_now", "forecast_price", "net_price_d7", "change_pct"]
].copy()
table["distance_km"] = table["distance_km"].round(0).astype(int)
for col in ["modal_price", "transport_cost", "net_price_now", "forecast_price", "net_price_d7"]:
    table[col] = table[col].map(fmt_inr)
table["change_pct"] = table["change_pct"].map(fmt_pct)
table.columns = [
    "Mandi", "State", "Distance (km)", "Today", "Transport", "Net today",
    "Day-7 forecast", "Net day-7", "7-day move",
]
st.dataframe(table, hide_index=True, width="stretch")

st.caption(
    "Transport is an estimate: ₹0.10 per quintal per km, straight-line distance. "
    "Check actual freight and mandi charges before deciding."
)
