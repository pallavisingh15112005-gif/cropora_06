"""Small-screen guards so the layout never overflows a phone width."""

import streamlit as st

_CSS = """
<style>
html, body { overflow-x: hidden; }
@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"], .block-container {
    padding-left: 0.9rem !important;
    padding-right: 0.9rem !important;
    max-width: 100vw !important;
  }
  h1 { font-size: 2rem !important; line-height: 1.2 !important; }
  [data-testid="stVerticalBlock"], [data-testid="stElementContainer"] { min-width: 0 !important; }
  [data-testid="stImage"] img { max-width: 100% !important; height: auto !important; }
}
</style>
"""


def inject_mobile_css() -> None:
    st.html(_CSS)
