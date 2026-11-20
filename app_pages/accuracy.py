import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_layer import load_metrics, load_model_info
from ui import GREEN, GOLD, chart_frame, data_note, page_header, section

page_header(
    "Model accuracy",
    "How well the seven-day price forecast performs on unseen data from the rolling-origin backtest.",
)

info = load_model_info()
metrics = load_metrics()

cards = st.columns(4)
with cards[0]:
    with st.container(border=True):
        st.metric("Average MAPE, 7-day", f"{info['avg_mape_h7']}%")
        st.caption("Mean absolute percentage error at day 7")
with cards[1]:
    with st.container(border=True):
        st.metric("Average MAPE, all horizons", f"{info['avg_mape']}%")
        st.caption("Horizons 1 through 7 pooled")
with cards[2]:
    with st.container(border=True):
        st.metric("Average R²", f"{info['avg_r2']:.2f}")
        st.caption("Pooled predictions versus actuals")
with cards[3]:
    with st.container(border=True):
        st.metric("Backtest predictions", f"{info['total_predictions']:,}")
        st.caption("28 rolling origins × 7 days × 13 crops")

section("Error by commodity", "Lower MAPE means the seven-day forecast was closer to the actual price.")
chart_data = metrics.sort_values("mape_h7")
fig = go.Figure(
    go.Bar(
        x=chart_data["mape_h7"],
        y=chart_data["commodity"],
        orientation="h",
        marker=dict(color=GREEN),
        text=[f"{value:.2f}%" for value in chart_data["mape_h7"]],
        textposition="outside",
        hovertemplate="%{y}<br>7-day MAPE %{x:.2f}%<extra></extra>",
    )
)
fig.update_layout(
    xaxis_title="MAPE at day 7 (%)",
    yaxis_title=None,
    height=460,
    margin=dict(l=8, r=55, t=16, b=8),
    showlegend=False,
)
st.plotly_chart(chart_frame(fig), width="stretch", config={"displayModeBar": False})

table = pd.DataFrame(
    {
        "Commodity": metrics["commodity"],
        "MAE (₹/qtl)": metrics["mae"].map(lambda value: f"{value:,.1f}"),
        "RMSE (₹/qtl)": metrics["rmse"].map(lambda value: f"{value:,.1f}"),
        "MAPE all horizons": metrics["mape"].map(lambda value: f"{value:.2f}%"),
        "MAPE day 7": metrics["mape_h7"].map(lambda value: f"{value:.2f}%"),
        "R²": metrics["r2"].map(lambda value: f"{value:.2f}"),
        "Test predictions": metrics["predictions"].map(lambda value: f"{value:,}"),
    }
)
st.dataframe(table, hide_index=True, width="stretch")

st.write("")
left, right = st.columns(2, gap="large")
with left:
    section("How the backtest works")
    st.markdown(
        f"""
- One ridge-regression model is trained per commodity.
- Features: prices lagged 1–30 days, 7/14/30-day rolling means, rolling volatility, short-term momentum, day-of-year seasonality and mandi identity.
- The model is trained up to a cutoff date, then asked for recursive seven-day forecasts from **28 consecutive origins**.
- Those forecasts are compared with actual, unseen prices. The band on the charts uses the 80th percentile of absolute errors by horizon.
- Built on {info['data_end']}. Artifacts rebuilt at {info['built_at'].replace('T', ' ')}.
"""
    )
with right:
    section("Honest limitations")
    st.markdown(
        """
- The model is trained on **synthetic sample data** modelled on Agmarknet patterns. When live prices are synced, today's price and the forecast level are anchored to Agmarknet, but the coefficients and backtest still come from the sample history. Real mandi prices are noisier, so live accuracy will be lower.
- The model is linear and short-term. It cannot anticipate policy changes, sudden transport strikes or extreme weather.
- R² is high partly because mandi price levels differ and prices are strongly autocorrelated; MAPE is the more useful headline.
- Forecasts are one input to a selling decision, not a guarantee. Check local mandi rates and expected arrivals.
"""
    )

data_note()
