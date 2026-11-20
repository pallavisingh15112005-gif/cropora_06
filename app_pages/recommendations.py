import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_layer import (
    crop_outlook,
    fmt_date,
    fmt_inr,
    fmt_pct,
    load_crops,
    sell_plan,
)
from ui import GREEN, GOLD, INK, RUST, chart_frame, data_note, outlook_table, page_header, section

page_header(
    "Recommendations",
    "A short-term market view: sell now or wait, where to take the crop, and which crop has the strongest outlook.",
)

location = st.session_state.get("location", "Ludhiana")
outlook = crop_outlook()
crops = sorted(load_crops()["commodity"].tolist())
default_crop = outlook.iloc[0]["commodity"]

section("Sell or hold", "Based on the best mandi reachable from your selected location.")
crop = st.selectbox(
    "Crop", crops, index=crops.index(default_crop), key="rec_crop"
)
plan = sell_plan(crop, location)

if not plan:
    st.warning("No market data for this crop.")
else:
    with st.container(border=True):
        st.markdown(f"### {plan['stance']}")
        st.caption(plan["reason"])
        cols = st.columns(4)
        cols[0].metric("Best mandi today", plan["best_now"]["mandi"])
        cols[1].metric("Net today", f"{fmt_inr(plan['best_now']['net_price_now'])}/qtl")
        cols[2].metric(
            "Day-7 net",
            f"{fmt_inr(plan['best_later']['net_price_d7'])}/qtl",
            delta=f"{plan['change_pct']:+.1f}%",
        )
        cols[3].metric("Distance", f"{plan['best_now']['distance_km']:.0f} km")
        st.caption(
            f"Net = modal price minus estimated transport at ₹0.10 per quintal per km. "
            f"Forecast date {fmt_date(plan['best_later']['forecast_date'])}."
        )

    rows = plan["rows"].sort_values("net_price_d7", ascending=False)
    show = pd.DataFrame(
        {
            "Mandi": rows["mandi"],
            "Distance (km)": rows["distance_km"].round(0).astype(int),
            "Today (₹/qtl)": rows["modal_price"].map(fmt_inr),
            "Transport": rows["transport_cost"].map(fmt_inr),
            "Net today": rows["net_price_now"].map(fmt_inr),
            "Day-7 forecast": rows["forecast_price"].map(fmt_inr),
            "Net day-7": rows["net_price_d7"].map(fmt_inr),
            "7-day move": rows["change_pct"].map(fmt_pct),
        }
    )
    st.dataframe(show, hide_index=True, width="stretch")
    st.caption(
        "Sell/hold thresholds: hold if the expected net price improves by 2% or more, "
        "sell now if it falls by 2% or more, otherwise the difference is small. "
        "Verify actual mandi charges and freight locally."
    )

st.write("")
section(
    "What to grow this week",
    "Commodity ranking for a seven-day market outlook. This is not a full crop-planning or agronomy recommendation.",
)

top = outlook.iloc[0]
with st.container(border=True):
    st.markdown(f"### Top outlook: {top['commodity']}")
    cols = st.columns(4)
    cols[0].metric("Category", top["category"])
    cols[1].metric("7-day move", fmt_pct(top["change_pct"]))
    cols[2].metric("Realised volatility", f"{top['volatility_pct']:.2f}%")
    cols[3].metric("Outlook score", f"{int(top['outlook_score'])}/100")
    st.caption(
        "Score = 50% price momentum + 25% stability (lower 30-day volatility is better) "
        "+ 25% value (current price relative to its one-year average)."
    )

chart_data = outlook.sort_values("change_pct")
bar_colors = [GREEN if value >= 0 else RUST for value in chart_data["change_pct"]]
fig = go.Figure(
    go.Bar(
        x=chart_data["change_pct"],
        y=chart_data["commodity"],
        orientation="h",
        marker=dict(color=bar_colors),
        text=[fmt_pct(value) for value in chart_data["change_pct"]],
        textposition="outside",
        hovertemplate="%{y}<br>7-day forecast move %{x:+.2f}%<extra></extra>",
    )
)
fig.update_layout(
    xaxis_title="Expected 7-day price change (%)",
    yaxis_title=None,
    height=430,
    margin=dict(l=8, r=50, t=16, b=8),
    showlegend=False,
)
fig.add_vline(x=0, line_color="#8A7A5C", line_width=1)
st.plotly_chart(chart_frame(fig), width="stretch", config={"displayModeBar": False})

outlook_table(outlook, 10)
data_note()
