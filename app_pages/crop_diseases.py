import streamlit as st

from data_layer import load_crops
from knowledge import diseases_for_crop, match_diseases, symptom_options
from ui import data_note, page_header, section

page_header(
    "Crop diseases",
    "Tick the symptoms you see to narrow down common diseases and pests, with practical remedies.",
)

crops = load_crops().sort_values("commodity")
crop = st.selectbox(
    "Crop",
    crops["commodity"].tolist(),
    index=crops["commodity"].tolist().index("Tomato"),
    key="disease_crop",
)
season_note = crops.loc[crops["commodity"] == crop, "season_note"].iloc[0]
st.caption(f"{crop}: {season_note}. Guidance is for common problems; confirm with your local KVK.")

options = symptom_options(crop)
selected = st.pills(
    "Select the symptoms you see",
    options,
    selection_mode="multi",
    key=f"symptoms_{crop}",
    label_visibility="visible",
)

diseases = diseases_for_crop(crop)
if selected:
    matches = [(d, s) for d, s in match_diseases(crop, selected, limit=3) if s > 0]
    if matches:
        st.caption("Closest matches from the knowledge base:")
        for disease, score in matches:
            with st.container(border=True):
                st.markdown(f"#### {disease['name']}")
                st.caption(f"{disease['type']} · symptom match {score * 100:.0f}%")
                st.markdown(f"**Signs to check:** {', '.join(symptom.lower() for symptom in disease['symptoms'])}.")
                st.markdown(f"**What to do:** {disease['remedy']}")
                st.markdown(f"**Prevention:** {disease['prevention']}")
    else:
        st.info(
            "No exact match for the selected symptoms. These are the common problems for this crop — "
            "check them below and confirm with an extension officer.",
            icon=":material/search:",
        )

if not selected or not any(s > 0 for _, s in match_diseases(crop, selected, limit=3)):
    st.write("")
    section("Common problems for this crop", "Open a card to see signs, remedy and prevention.")
    for disease in diseases:
        with st.expander(f"{disease['name']} · {disease['type']}"):
            st.markdown(f"**Signs:** {', '.join(symptom.lower() for symptom in disease['symptoms'])}.")
            st.markdown(f"**What to do:** {disease['remedy']}")
            st.markdown(f"**Prevention:** {disease['prevention']}")

st.write("")
st.warning(
    "This is a symptom-based guide, not a diagnosis. Pesticide doses must follow the product label. "
    "Consult your local Krishi Vigyan Kendra or agriculture officer before spraying.",
    icon=":material/info:",
)
st.page_link(
    "app_pages/photo_diagnosis.py",
    label="Have a clear leaf photo? Try Photo diagnosis",
    icon=":material/photo_camera:",
)
data_note()
