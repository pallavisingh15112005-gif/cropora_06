import pandas as pd
import streamlit as st

from agmarknet import SOURCE, get_status, sync_live_prices
from data_layer import fmt_inr, live_prices
from ui import data_note, page_header, section

page_header("Live mandi prices")

status = get_status()

if status["snapshot"]:
    synced = pd.to_datetime(status["snapshot_synced_at"], errors="coerce")
    when = (
        f"{synced:%d %b %Y, %H:%M} IST"
        if pd.notna(synced)
        else "an earlier session"
    )
    st.caption(
        f"Showing the bundled Agmarknet snapshot synced {when}. data.gov.in answers "
        "only from Indian networks, so this deployment cannot fetch live prices "
        "itself; the snapshot is refreshed from a local Indian connection."
    )

if not status["configured"] and not status["snapshot"]:
    st.warning(
        "Live sync is not configured, so new prices cannot be fetched. "
        "Cached live rows below are still used if present; otherwise the app uses "
        "the sample dataset.",
        icon=":material/cloud_off:",
    )
    with st.expander("How to enable live Agmarknet prices", expanded=True):
        st.markdown(
            """
1. Create a free **data.gov.in** account and copy your API key from
   [My Account → API key](https://data.gov.in/).
2. Create a Turso database and token:
   `turso db create cropora`, then `turso db show cropora --url` and
   `turso db tokens create cropora`.
3. Add both to `.streamlit/secrets.toml` in the project:

```toml
DATA_GOV_API_KEY = "your-data-gov-in-key"
TURSO_DATABASE_URL = "libsql://your-database.turso.io"
TURSO_AUTH_TOKEN = "your-turso-token"
```

4. Restart Streamlit and press **Sync now** below.
"""
        )
        st.caption(
            "Agmarknet 2.0 protects its own price endpoint with a CAPTCHA. The "
            "data.gov.in resource is the official key-based route to the same daily "
            "mandi prices."
        )
elif status["db_error"]:
    st.error(
        f"Live prices are configured, but the database is unreachable: {status['db_error']}",
        icon=":material/database:",
    )

if status["configured"]:
    left, right = st.columns([1, 3], vertical_alignment="center")
    with left:
        sync_clicked = st.button(
            "Sync now", type="primary", icon=":material/sync:", width="stretch"
        )
    with right:
        st.caption(
            "Fetches the current data.gov.in snapshot and upserts it into the app database "
            "(Turso, or the local libSQL file when Turso is not configured). "
            "Already-cached dates are updated, not duplicated."
        )

    if sync_clicked:
        with st.spinner("Fetching current mandi prices from Agmarknet..."):
            st.session_state["live_sync_result"] = sync_live_prices()
        st.rerun()

result = st.session_state.pop("live_sync_result", None)
if result:
    if result.get("ok"):
        st.success(
            f"{result['message']} Fetched {result.get('fetched', 0):,} API rows; "
            f"matched {result.get('saved', 0):,} across "
            f"{result.get('commodities', 0)} commodities and "
            f"{result.get('mandis', 0)} mandis for {result.get('price_date', '')}."
        )
    else:
        st.error(result.get("message", "Live sync failed."))

if status["last_error"] and status["configured"]:
    st.caption(f"Last sync error: {status['last_error']}")

st.write("")
section(
    "Cached live prices",
    "Latest Agmarknet snapshot per commodity and mandi. The sample data fills any pair without a live row.",
)

live = live_prices()
if live.empty:
    st.info(
        "No live prices cached yet. Add the data.gov.in key and press Sync now. "
        "Turso is optional: without it, prices are cached in the local libSQL file. "
        "Every other page continues to work on the sample dataset."
    )
else:
    latest = live.sort_values("price_date").groupby(["commodity", "mandi_id"]).tail(1)
    latest = latest.sort_values(["commodity", "modal_price"], ascending=[True, False])
    crops = ["All commodities"] + sorted(latest["commodity"].unique())
    crop = st.selectbox("Crop", crops, key="live_crop")
    if crop != "All commodities":
        latest = latest[latest["commodity"] == crop]

    table = latest[
        [
            "commodity",
            "mandi",
            "state",
            "modal_price",
            "min_price",
            "max_price",
            "variety_count",
            "price_date",
            "fetched_at",
        ]
    ].copy()
    table["price_date"] = pd.to_datetime(table["price_date"]).dt.strftime("%d %b %Y")
    table["fetched_at"] = (
        pd.to_datetime(table["fetched_at"], errors="coerce").dt.strftime("%d %b, %H:%M")
    )
    table["modal_price"] = table["modal_price"].map(fmt_inr)
    table["min_price"] = table["min_price"].map(fmt_inr)
    table["max_price"] = table["max_price"].map(fmt_inr)
    table.columns = [
        "Crop",
        "Mandi",
        "State",
        "Modal (₹/qtl)",
        "Min (₹/qtl)",
        "Max (₹/qtl)",
        "Varieties",
        "Price date",
        "Synced",
    ]
    st.dataframe(table, hide_index=True, width="stretch")
    st.download_button(
        "Download CSV",
        table.to_csv(index=False).encode("utf-8"),
        file_name="cropora_live_prices.csv",
        mime="text/csv",
        icon=":material/download:",
    )
    st.caption(
        f"Source: {SOURCE} via data.gov.in. Where a mandi reports several varieties, "
        "the modal price is their median and min/max cover the reported range. "
        "Live prices anchor today's price and the 7-day forecast level across the app; "
        "the forecasting model itself is trained on the sample history."
    )

data_note()
