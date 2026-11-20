import streamlit as st

from alerts import add_alert, delete_alert, list_alerts
from data_layer import (
    fmt_date,
    fmt_inr,
    forecast_summary,
    load_crops,
    mandi_name,
    mandi_rows_for,
    market_date,
)
from ui import data_note, page_header, section, status_text

page_header(
    "Price alerts",
    "Set a target price and Cropora AI flags it when the latest price for that crop and mandi reaches it.",
)

summary = forecast_summary()
crops = sorted(summary["commodity"].unique())

alerts = list_alerts()
triggered = alerts[alerts["status"] == "Triggered"] if not alerts.empty else alerts
if len(triggered):
    lines = "\n".join(
        f"- **{row.commodity}** at {row.mandi}: target {fmt_inr(row.target_price)}, now {fmt_inr(row.current_price)}"
        for row in triggered.itertuples()
    )
    st.warning(f"**Triggered now**\n\n{lines}")

section("Set a new target", "Choose a crop and mandi, then enter the price you are waiting for.")
c1, c2 = st.columns(2)
with c1:
    crop = st.selectbox(
        "Crop", crops, index=crops.index("Wheat") if "Wheat" in crops else 0, key="al_crop"
    )
with c2:
    location = st.session_state.get("location", "Ludhiana")
    crop_rows = mandi_rows_for(crop, location).sort_values("distance_km")
    labels = {row.mandi_id: f"{row.mandi} — {row.state}" for row in crop_rows.itertuples()}
    mandi_id = st.selectbox(
        "Mandi",
        crop_rows["mandi_id"].tolist(),
        format_func=lambda value: labels.get(value, value),
        key="al_mandi",
    )

row = crop_rows[crop_rows["mandi_id"] == mandi_id].iloc[0]
current = float(row["modal_price"])
source = row.get("price_source", "Sample")
st.caption(
    f"Current price at {mandi_name(mandi_id)}: **{fmt_inr(current)}/qtl** "
    f"({source}) · day-7 forecast {fmt_inr(row['forecast_price'])}/qtl"
)

with st.form("new_alert_form", clear_on_submit=False):
    c3, c4 = st.columns(2)
    with c3:
        target = st.number_input(
            "Target price (₹ per quintal)",
            min_value=1.0,
            max_value=100000.0,
            value=round(current, 0),
            step=10.0,
            format="%.0f",
        )
    with c4:
        direction_label = st.selectbox(
            "Alert me when the price",
            ["Rises to or above", "Falls to or below"],
        )
    submitted = st.form_submit_button("Save alert", type="primary")

if submitted:
    direction = "above" if direction_label == "Rises to or above" else "below"
    add_alert(crop, mandi_id, float(target), direction)
    st.success(
        f"Alert saved: {crop} at {mandi_name(mandi_id)} when price goes {direction} {fmt_inr(target)}."
    )
    st.rerun()

st.write("")
section("Your alerts", "Checked against the latest cached price every time the app runs.")
alerts = list_alerts()
if alerts.empty:
    st.caption("No alerts saved yet. Create one above.")
else:
    for row in alerts.itertuples():
        with st.container(border=True):
            cols = st.columns([2.3, 2.1, 2.1, 1.7, 0.7], vertical_alignment="center")
            cols[0].markdown(f"**{row.commodity}**\nat **{row.mandi}**")
            direction = "rises to" if row.direction == "above" else "falls to"
            cols[1].markdown(f"Target {fmt_inr(row.target_price)}  \n_(alert when price {direction} target)_")
            cols[2].markdown(
                f"Now {fmt_inr(row.current_price)}  \n_{fmt_date(market_date())} · {row.price_source}_"
            )
            cols[3].markdown(status_text(row.status))
            if cols[4].button("Delete", key=f"delete_alert_{row.id}"):
                delete_alert(row.id)
                st.rerun()

st.caption(
    "Alerts are checked against the latest cached price: Agmarknet when live prices "
    "have been synced, the sample dataset otherwise. Live push notifications and SMS "
    "are future scope."
)
data_note()
