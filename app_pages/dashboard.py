import streamlit as st

from alerts import triggered_alerts
from data_layer import (
    crop_outlook,
    fmt_date,
    fmt_inr,
    fmt_pct,
    load_crops,
    load_model_info,
    market_date,
)
from ui import hero, outlook_table, section

hero()
st.write("")

info = load_model_info()
alerts = triggered_alerts()
stats = st.columns(4)
with stats[0]:
    with st.container(border=True):
        st.metric("Latest market date", fmt_date(market_date()))
with stats[1]:
    with st.container(border=True):
        st.metric("Commodities covered", str(len(load_crops())))
with stats[2]:
    with st.container(border=True):
        st.metric("7-day forecast MAPE", f"{info['avg_mape_h7']}%")
with stats[3]:
    with st.container(border=True):
        st.metric("Triggered alerts", str(len(alerts)))

if len(alerts):
    lines = "\n".join(
        f"- **{row.commodity}** at {row.mandi}: target {fmt_inr(row.target_price)}, "
        f"now {fmt_inr(row.current_price)}"
        for row in alerts.itertuples()
    )
    st.warning(f"**Price alerts triggered**\n\n{lines}")

outlook = crop_outlook()
top = outlook.iloc[0]

st.write("")
section("Best crop of the week")

left, right = st.columns([1.1, 1], gap="large")
with left:
    with st.container(border=True):
        st.markdown("#### Top pick")
        st.markdown(f"## {top['commodity']}")
        st.markdown(
            f"{top['category']} · traded in {int(top['mandi_count'])} mandis · "
            f"average price {fmt_inr(top['current_price'])}/qtl"
        )
        cols = st.columns(3)
        cols[0].metric("Outlook score", f"{int(top['outlook_score'])}/100")
        cols[1].metric("7-day move", fmt_pct(top["change_pct"]))
        cols[2].metric("vs 1-year avg", fmt_pct(top["vs_year_pct"]))
with right:
    st.markdown("#### This week's ranking")
    outlook_table(outlook, 6)

st.write("")
section("Market snapshot", "Today's average price and the seven-day forecast move for every covered commodity.")
outlook_table(outlook)

st.write("")
with st.expander("How to use Cropora AI"):
    st.markdown(
        """
1. Start with **Prices & forecast** to see a crop and mandi in detail.
2. Use **Mandi map** and **Compare mandis** to judge price spread and distance.
3. Set a target in **Price alerts** if you want to wait for a specific price.
4. Open **Recommendations** for sell/hold and where-to-sell guidance.
5. Ask a plain-language question in **Ask Cropora** at any time.
"""
    )
