"""Cropora AI — crop price advisor for farmers.

Run:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from data_layer import haversine_km, load_locations
from drawer import inject_autoclose
from geocode import reverse_location
from theme import inject_styles

st.set_page_config(
    page_title="Cropora AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_styles()
inject_autoclose()

pages = {
    "Overview": [
        st.Page("app_pages/dashboard.py", title="Dashboard", icon=":material/home:", default=True),
    ],
    "Market tools": [
        st.Page("app_pages/prices_forecast.py", title="Prices & forecast", icon=":material/show_chart:"),
        st.Page("app_pages/live_prices.py", title="Live mandi prices", icon=":material/sensors:"),
        st.Page("app_pages/mandi_map.py", title="Mandi map", icon=":material/map:"),
        st.Page("app_pages/compare_mandis.py", title="Compare mandis", icon=":material/compare_arrows:"),
    ],
    "Advisory": [
        st.Page("app_pages/recommendations.py", title="Recommendations", icon=":material/lightbulb:"),
        st.Page("app_pages/price_alerts.py", title="Price alerts", icon=":material/notifications:"),
        st.Page("app_pages/crop_diseases.py", title="Crop diseases", icon=":material/eco:"),
        st.Page("app_pages/photo_diagnosis.py", title="Photo diagnosis", icon=":material/photo_camera:"),
        st.Page("app_pages/schemes.py", title="Government schemes", icon=":material/account_balance:"),
    ],
    "Information": [
        st.Page("app_pages/accuracy.py", title="Model accuracy", icon=":material/verified:"),
        st.Page("app_pages/chat.py", title="Ask Cropora", icon=":material/chat:"),
    ],
}

pg = st.navigation(pages, position="sidebar")

locations_df = load_locations()
locations = locations_df["location"].tolist()
default_index = locations.index("Ludhiana") if "Ludhiana" in locations else 0

gps = st.session_state.get("gps")
if gps is None and "location" not in st.session_state:
    try:
        gps = float(st.query_params.get("lat")), float(st.query_params.get("lon"))
    except (TypeError, ValueError):
        gps = None
    if gps:
        st.session_state["gps"] = gps
        nearest = min(
            locations_df.itertuples(),
            key=lambda r: haversine_km(gps[0], gps[1], r.latitude, r.longitude),
        )
        default_index = locations.index(nearest.location)

with st.sidebar:
    st.selectbox(
        "Your location",
        locations,
        index=default_index,
        key="location",
        help="Used to calculate mandi distances and transport costs.",
    )
    if gps:
        label = reverse_location(gps[0], gps[1])
        if label:
            st.caption(label)

pg.run()
