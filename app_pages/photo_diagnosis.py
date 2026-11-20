import io

import streamlit as st
from PIL import Image

import disease_detector as detector
from ui import page_header, section

page_header(
    "Photo diagnosis",
    "Upload or take a close-up photo of a crop leaf and a local image model suggests the most likely disease, pest or healthy class.",
)

if not detector.available():
    st.error(
        f"The photo model files are missing from `{detector.MODEL_DIR}`. "
        "Restore `model.onnx` and `config.json` to use photo diagnosis.",
        icon=":material/folder_off:",
    )
    st.stop()

upload_tab, camera_tab = st.tabs(["Upload a photo", "Take a photo"])
with upload_tab:
    uploaded = st.file_uploader(
        "Leaf photo",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )
with camera_tab:
    captured = st.camera_input(
        "Take a close-up photo of one leaf",
        label_visibility="collapsed",
    )

photo = captured or uploaded

if photo is None:
    with st.container(border=True):
        st.markdown("#### For a useful photo")
        st.markdown(
            "- Fill the frame with **one leaf**\n"
            "- Plain background, even daylight, no hard shadow\n"
            "- Close and in focus — show the spots you are worried about\n"
            "- Avoid screenshots, drawings or photos of several plants"
        )
    section(
        "Crops in the model",
        "Apple, bell pepper, blueberry, cherry, grape, maize, orange, peach, potato, "
        "raspberry, soybean, squash, strawberry and tomato.",
    )
    st.caption(
        "The model recognises 38 leaf classes from these crops. It does not cover every "
        "disease or every crop grown in India."
    )
    st.stop()

try:
    image = Image.open(io.BytesIO(photo.getvalue()))
    predictions = detector.predict(image, top_k=3)
except Exception:
    st.error(
        "That file could not be read as an image. Try a JPG, PNG or WebP photo.",
        icon=":material/broken_image:",
    )
    st.stop()

top = predictions[0]
confidence = top["confidence"]
healthy = top["healthy"]

left, right = st.columns([1, 1.2], gap="large")
with left:
    st.image(image, caption="Your photo", width="stretch")
with right:
    st.markdown(
        f"### {top['crop']}" + (" — looks healthy" if healthy else f" — {top['disease']}")
    )
    st.metric("Model confidence", f"{confidence:.0%}")
    st.progress(confidence)

    if confidence < detector.LOW_CONFIDENCE:
        st.warning(
            "Low confidence. The photo may not be a clear close-up of a single leaf, "
            "or the problem may not be one of the 38 classes the model knows. "
            "Take another photo in even daylight, or use the symptom guide.",
            icon=":material/help:",
        )
    elif healthy:
        st.success(
            "The strongest match is a healthy leaf. The model found no disease "
            "pattern it recognises.",
            icon=":material/check_circle:",
        )
    else:
        st.warning(
            f"Possible **{top['disease']}** on {top['crop'].lower()}. "
            "Treat this as a screening result, not a diagnosis.",
            icon=":material/eco:",
        )

    st.markdown("**Other possibilities**")
    for match in predictions[1:]:
        st.progress(
            match["confidence"],
            text=f"{match['label']} · {match['confidence']:.1%}",
        )

    st.caption(
        "Confidence is the model's own score, not a tested accuracy figure. "
        "A high score on an unclear photo can still be wrong."
    )

if not healthy:
    st.write("")
    section("What to check and do", "Matching guidance from the app's crop knowledge base.")
    entry = top["knowledge"]
    if entry:
        with st.container(border=True):
            st.markdown(f"#### {entry['name']} · {entry['type']}")
            st.markdown(
                f"**Signs to check:** {', '.join(s.lower() for s in entry['symptoms'])}."
            )
            st.markdown(f"**What to do:** {entry['remedy']}")
            st.markdown(f"**Prevention:** {entry['prevention']}")
    elif top["in_market"]:
        st.info(
            f"The model recognised **{top['label']}**, but the app's remedy library has no "
            "entry for this exact problem yet. Check the symptoms on the crop or take the "
            "leaf to your local Krishi Vigyan Kendra.",
            icon=":material/menu_book:",
        )
    else:
        st.info(
            f"**{top['crop']}** is outside the app's 13-commodity market coverage, so there is "
            "no local price or remedy entry for it. Use the result as a pointer and confirm "
            "with your local Krishi Vigyan Kendra.",
            icon=":material/info:",
        )

    st.page_link(
        "app_pages/crop_diseases.py",
        label="Cross-check the symptoms in Crop diseases",
        icon=":material/eco:",
    )

st.write("")
with st.expander("About the photo model"):
    st.markdown(
        f"- **Model:** {detector.MODEL_NAME}, {detector.MODEL_CLASSES} classes "
        "(26 disease/pest and 12 healthy classes).\n"
        f"- **Source:** [onnx-community plant disease model]({detector.MODEL_SOURCE}) "
        "running locally with onnxruntime.\n"
        "- **Training photos:** PlantVillage leaf photos, mostly one leaf on a plain "
        "background. Accuracy drops with cluttered field photos, several leaves, low "
        "light, blur or a camera angle that hides the spots.\n"
        "- **Not covered:** crops and problems outside its 38 classes, nutrient "
        "deficiencies, herbicide injury and pest damage that does not change leaf colour.\n"
        "- **Privacy:** the photo is processed inside this app on this machine; it is "
        "not sent to an external service."
    )

st.warning(
    "A photo result is a screening aid, not a diagnosis. Pesticide doses must follow the "
    "product label. Confirm with your local Krishi Vigyan Kendra or agriculture officer "
    "before spraying.",
    icon=":material/info:",
)
