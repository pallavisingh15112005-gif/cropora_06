import pandas as pd
import streamlit as st

from data_layer import (
    fmt_inr,
    fmt_pct,
    forecast_summary,
    location_coords,
    mandi_rows_for,
)
from ui import mandi_map, page_header, section

page_header("Mandi map & distance")

summary = forecast_summary()
crops = sorted(summary["commodity"].unique())
crop = st.selectbox("Crop", crops, index=crops.index("Wheat") if "Wheat" in crops else 0, key="map_crop")
location = st.session_state.get("location", "Ludhiana")
rows = mandi_rows_for(crop, location).sort_values("distance_km").reset_index(drop=True)
lat, lon = location_coords(location)

if rows.empty:
    st.warning("No mandis trade this crop in the app's data.")
    st.stop()

metrics = st.columns(3)
nearest = rows.iloc[0]
with metrics[0]:
    with st.container(border=True):
        st.metric("Nearest mandi", nearest["mandi"])
        st.caption(f"{nearest['distance_km']:.0f} km from {location}")
with metrics[1]:
    with st.container(border=True):
        st.metric("Price range today", f"{fmt_inr(rows['modal_price'].min())}–{fmt_inr(rows['modal_price'].max())}")
        st.caption(f"{len(rows)} mandis trade {crop}")
with metrics[2]:
    with st.container(border=True):
        st.metric("Average 7-day move", fmt_pct(rows["change_pct"].mean()))
        st.caption("Across the mandis shown on the map")

st.plotly_chart(
    mandi_map(rows, location, lat, lon),
    width="stretch",
    config={"displayModeBar": False},
)

section("Distances and prices", f"From your selected location: {location}.")
table = rows[
    ["mandi", "state", "distance_km", "transport_cost", "modal_price", "forecast_price", "change_pct"]
].copy()
table["transport_cost"] = table["transport_cost"].map(fmt_inr)
table["modal_price"] = table["modal_price"].map(fmt_inr)
table["forecast_price"] = table["forecast_price"].map(fmt_inr)
table["change_pct"] = table["change_pct"].map(fmt_pct)
table["distance_km"] = table["distance_km"].round(0).astype(int)
table.columns = ["Mandi", "State", "Distance (km)", "Est. transport", "Today", "Day-7 forecast", "7-day move"]
st.dataframe(table, hide_index=True, width="stretch")

st.caption(
    "Distance is straight-line (Haversine) from your selected location, not road distance. "
    "Transport cost uses an assumed ₹0.10 per quintal per km."
)
