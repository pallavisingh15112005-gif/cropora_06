"""Shared visual helpers for the Cropora AI Streamlit pages."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_layer import (
    fmt_date,
    fmt_inr,
    fmt_pct,
    forecast_path,
    live_latest,
    load_forecasts,
    load_model_info,
    market_date,
    price_history,
)

GREEN = "#2F5D3A"
DEEP_GREEN = "#1F3D2B"
GOLD = "#B8862F"
LIGHT_GOLD = "#D6A13A"
RUST = "#A64B2A"
INK = "#2B2419"
MUTED = "#6B6353"
GRID = "#E4D9C2"
CREAM = "#FBF7EC"

ASSETS = Path(__file__).resolve().parent / "assets"


def page_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def section(title: str, caption: str | None = None) -> None:
    st.subheader(title)
    if caption:
        st.caption(caption)


def chart_frame(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        template="streamlit",
        height=height,
        margin=dict(l=8, r=8, t=24, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans 3, Segoe UI, sans-serif", color=INK, size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="#FFFDF6", font_color=INK, bordercolor=GRID),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def price_forecast_chart(commodity: str, mandi_id: str) -> go.Figure:
    hist = price_history(commodity, mandi_id, 120)
    fc = forecast_path(commodity, mandi_id)
    last_date = hist["date"].iloc[-1]
    last_price = float(hist["modal_price"].iloc[-1])
    x = [last_date] + fc["date"].tolist()
    y = [last_price] + fc["forecast_price"].tolist()
    lower = [last_price] + fc["lower"].tolist()
    upper = [last_price] + fc["upper"].tolist()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x, y=upper, mode="lines", line=dict(width=0),
            hoverinfo="skip", showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x, y=lower, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(184, 134, 47, 0.16)",
            name="80% forecast range", hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hist["date"], y=hist["modal_price"], mode="lines",
            name="Modal price", line=dict(color=GREEN, width=2.6),
            hovertemplate="%{x|%d %b %Y}<br>₹%{y:,.0f}/qtl<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x, y=y, mode="lines+markers", name="7-day forecast",
            line=dict(color=GOLD, width=2.6, dash="dash"),
            marker=dict(size=6, color=GOLD),
            hovertemplate="%{x|%d %b %Y}<br>Forecast ₹%{y:,.0f}/qtl<extra></extra>",
        )
    )
    fig.add_vline(
        x=last_date, line_dash="dot", line_color="#8A7A5C", line_width=1,
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (₹ per quintal)",
        hovermode="x unified",
    )
    return chart_frame(fig, 400)


def mandi_price_chart(rows: pd.DataFrame) -> go.Figure:
    data = rows.sort_values("modal_price")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=data["modal_price"],
            y=data["mandi"],
            orientation="h",
            name="Today",
            marker=dict(color=GREEN, line=dict(width=0)),
            text=[f"₹{v:,.0f}" for v in data["modal_price"]],
            textposition="outside",
            customdata=list(zip(data["distance_km"], data["net_price_now"], data["forecast_price"], data["change_pct"])),
            hovertemplate=(
                "%{y}<br>Today ₹%{x:,.0f}/qtl<br>"
                "%{customdata[0]:.0f} km · net ₹%{customdata[1]:,.0f}<br>"
                "Day 7 ₹%{customdata[2]:,.0f} (%{customdata[3]:+.1f}%)<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["forecast_price"],
            y=data["mandi"],
            mode="markers",
            name="Day-7 forecast",
            marker=dict(color=GOLD, size=10, symbol="diamond"),
            hovertemplate="%{y}<br>Day-7 forecast ₹%{x:,.0f}/qtl<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="Price (₹ per quintal)",
        yaxis_title=None,
        height=max(340, 38 * len(data) + 120),
        margin=dict(l=8, r=60, t=24, b=8),
    )
    fig.update_xaxes(gridcolor=GRID)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    return chart_frame(fig, max(340, 38 * len(data) + 120))


def mandi_map(rows: pd.DataFrame, location: str, lat: float, lon: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scattermap(
            lat=rows["latitude"],
            lon=rows["longitude"],
            mode="markers+text",
            text=rows["mandi"],
            textposition="top center",
            textfont=dict(size=11, color=INK),
            marker=dict(
                size=16,
                color=rows["modal_price"],
                colorscale=[[0, "#A8C09A"], [0.5, "#6F9153"], [1, DEEP_GREEN]],
                showscale=True,
                colorbar=dict(title=dict(text="₹/qtl", font=dict(size=12)), thickness=10, len=0.55),
            ),
            customdata=list(zip(rows["state"], rows["distance_km"], rows["modal_price"])),
            hovertemplate=(
                "<b>%{text}</b><br>%{customdata[0]}<br>"
                "₹%{customdata[2]:,.0f}/qtl · %{customdata[1]:.0f} km<extra></extra>"
            ),
            name="Mandis",
        )
    )
    fig.add_trace(
        go.Scattermap(
            lat=[lat],
            lon=[lon],
            mode="markers",
            marker=dict(size=22, color=LIGHT_GOLD),
            text=[f"You — {location}"],
            hovertemplate="%{text}<extra></extra>",
            name="Your location",
        )
    )
    fig.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(lat=lat, lon=lon),
            zoom=4.1,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=520,
        showlegend=False,
    )
    return chart_frame(fig, 520)


def outlook_table(df: pd.DataFrame, rows: int | None = None) -> None:
    data = df if rows is None else df.head(rows)
    show = pd.DataFrame(
        {
            "Crop": data["commodity"],
            "Type": data["category"],
            "Today (₹/qtl)": data["current_price"].map(fmt_inr),
            "7-day move": data["change_pct"].map(fmt_pct),
            "Outlook score": data["outlook_score"],
        }
    )
    st.dataframe(
        show,
        hide_index=True,
        width="stretch",
        column_config={
            "Outlook score": st.column_config.ProgressColumn(
                "Outlook score", min_value=0, max_value=100, format="%d"
            ),
        },
    )


def data_note(extra: str | None = None) -> None:
    live = live_latest()
    if live.empty:
        text = (
            f"Sample data: synthetic Agmarknet-style daily modal prices (fixed seed), "
            f"latest market date {fmt_date(market_date())}. No live Agmarknet sync yet."
        )
    else:
        text = (
            f"Live prices: Agmarknet via data.gov.in for {len(live)} commodity-mandi "
            f"pairs, latest {fmt_date(live['live_date'].max())}; sample data fills the "
            f"remaining pairs. Price history and model training use the sample dataset."
        )
    if extra:
        text = f"{extra} {text}"
    st.caption(text)


def accuracy_metrics_row() -> None:
    info = load_model_info()
    cols = st.columns(4)
    cols[0].metric("7-day forecast MAPE", f"{info['avg_mape_h7']}%")
    cols[1].metric("Average R²", f"{info['avg_r2']:.2f}")
    cols[2].metric("Backtest predictions", f"{info['total_predictions']:,}")
    cols[3].metric("Commodities modelled", f"{len(load_forecasts()['commodity'].unique())}")


def status_text(status: str) -> str:
    if status == "Triggered":
        return ":green[**Triggered**]"
    if status == "Waiting":
        return ":orange[**Waiting**]"
    return f":gray[**{status}**]"


def hero() -> None:
    hero_path = ASSETS / "hero.png"
    left, right = st.columns([1.55, 1], vertical_alignment="center")
    with left:
        st.title("Cropora AI")
        st.markdown("#### फसल से फायदा तक, Cropora AI के साथ")
    with right:
        if hero_path.exists():
            st.image(str(hero_path), width="stretch")
