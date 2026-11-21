"""Cropora AI — crop price advisor for farmers.

Run:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from data_layer import load_locations
from ui import inject_styles

st.set_page_config(
    page_title="Cropora AI",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_styles()

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

flat_pages = [page for group in pages.values() for page in group]
page_titles = [page.title for page in flat_pages]

locations = load_locations()["location"].tolist()
default_index = locations.index("Ludhiana") if "Ludhiana" in locations else 0

pg = st.navigation(pages, position="hidden")

segment = (st.context.url or "/").split("?")[0].rstrip("/").split("/")[-1]
current = next(
    (i for i, page in enumerate(flat_pages) if page.url_path == segment), 0
)
nav_col, loc_col = st.columns([1.2, 1], vertical_alignment="bottom")
with nav_col:
    choice = st.selectbox("Page", page_titles, index=current)
with loc_col:
    st.selectbox(
        "Your location",
        locations,
        index=default_index,
        key="location",
        help="Used to calculate mandi distances and transport costs.",
    )
if choice != page_titles[current]:
    st.switch_page(flat_pages[page_titles.index(choice)])

pg.run()
