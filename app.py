"""Cropora AI — crop price advisor for farmers.

Run:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from alerts import triggered_alerts
from data_layer import fmt_date, live_latest, load_locations, market_date

st.set_page_config(
    page_title="Cropora AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

locations = load_locations()["location"].tolist()
default_index = locations.index("Ludhiana") if "Ludhiana" in locations else 0

with st.sidebar:
    st.markdown("## Cropora AI")
    st.caption("Crop price advisor for farmers")
    st.selectbox(
        "Your location",
        locations,
        index=default_index,
        key="location",
        help="Used to calculate mandi distances and transport costs.",
    )
    try:
        triggered = triggered_alerts()
    except Exception:
        st.caption("Alerts database unavailable. Check the Turso settings.")
    else:
        if len(triggered):
            st.caption(f"{len(triggered)} price alert(s) triggered — see Price alerts.")
        else:
            st.caption("No price alerts triggered.")
    st.divider()
    live = live_latest()
    if live.empty:
        st.caption(f"Latest market date: {fmt_date(market_date())}")
        st.caption(
            "Sample data: synthetic Agmarknet-style prices. Sync live prices on "
            "the Live mandi prices page."
        )
    else:
        st.caption(
            f"Live Agmarknet: {len(live)} pairs · "
            f"{fmt_date(live['live_date'].max())}"
        )
        st.caption("History and model training still use the sample dataset.")

pg = st.navigation(pages, position="sidebar")
pg.run()
