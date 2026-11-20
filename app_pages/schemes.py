import streamlit as st

from data_layer import load_crops
from knowledge import SCHEMES, schemes_for_crop
from ui import data_note, page_header

page_header(
    "Government schemes",
    "Support programmes relevant to farmers, what they offer and where to apply.",
)

crops = load_crops().sort_values("commodity")
options = ["All commodities"] + crops["commodity"].tolist()
crop = st.selectbox("Show schemes for", options, key="scheme_crop")
search = st.text_input(
    "Search schemes",
    placeholder="Try insurance, credit, horticulture or FPO",
    key="scheme_search",
)

category = None
if crop != "All commodities":
    match = crops[crops["commodity"] == crop]
    category = match.iloc[0]["category"] if len(match) else None

schemes = schemes_for_crop(None if crop == "All commodities" else crop, category)
if search:
    needle = search.lower()
    schemes = [
        scheme for scheme in schemes
        if needle in scheme["name"].lower()
        or needle in scheme["benefit"].lower()
        or needle in scheme["category"].lower()
        or needle in scheme["eligibility"].lower()
    ]

st.caption(f"{len(schemes)} of {len(SCHEMES)} schemes shown. Specific schemes are listed before general ones.")

for scheme in schemes:
    with st.expander(f"{scheme['name']} · {scheme['category']}"):
        st.markdown(f"**What you get:** {scheme['benefit']}")
        st.markdown(f"**Who is eligible:** {scheme['eligibility']}")
        st.markdown(f"**How to apply:** {scheme['apply']}")
        st.link_button("Open official portal", scheme["link"], type="secondary")

st.write("")
st.caption(
    "Scheme details are summarized from public information for a student project. "
    "Rules, amounts and portals can change; verify the current terms on the official site or with your block agriculture office."
)
data_note()
