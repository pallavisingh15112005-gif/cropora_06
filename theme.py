"""Injected CSS polish layered over the Streamlit theme."""

import streamlit as st

_CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1100px 520px at 88% -12%, #F3E8CC 0%, rgba(243,232,204,0) 62%),
        linear-gradient(180deg, #FBF7EC 0%, #F7F1E0 100%);
}
[data-testid="stHeader"] { background: transparent; }

h1 {
    background: linear-gradient(92deg, #1F3D2B 0%, #2F5D3A 42%, #B8862F 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
}
h2 {
    border-left: 5px solid #D6A13A;
    padding-left: 0.65rem;
}
h3 {
    color: #2F5D3A;
    border-left: 4px solid #D6A13A;
    padding-left: 0.55rem;
}
h4 { color: #2F5D3A; }

[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(165deg, #FFFDF7 0%, #FBF4E3 100%) !important;
    border: 1px solid #E3D6BA !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 12px rgba(47, 93, 58, 0.07) !important;
}

[data-testid="stMetricValue"] { color: #2F5D3A; font-weight: 650; }
[data-testid="stMetricLabel"] p {
    color: #6B6353;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.78rem;
    font-weight: 600;
}

.stButton button {
    border-radius: 10px;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
}
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #2F5D3A 0%, #1F3D2B 100%);
    border: none;
    box-shadow: 0 3px 10px rgba(31, 61, 43, 0.28);
}
.stButton button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 5px 16px rgba(31, 61, 43, 0.34);
}

[data-baseweb="select"] > div,
[data-baseweb="input"] { border-radius: 10px !important; }
[data-baseweb="select"] > div:focus-within {
    box-shadow: 0 0 0 3px rgba(214, 161, 58, 0.22);
}

details[data-testid="stExpander"] {
    background: #FDF9EF;
    border: 1px solid #E3D6BA;
    border-radius: 12px;
}
details[data-testid="stExpander"] summary:hover { color: #2F5D3A; }

[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stCaptionContainer"] { color: #7A705C; }

[data-testid="stSidebarContent"] {
    background: linear-gradient(180deg, #1F3D2B 0%, #16301F 100%);
}
</style>
"""


def inject_styles() -> None:
    st.html(_CSS)
