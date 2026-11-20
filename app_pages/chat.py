import streamlit as st

from chatbot import respond
from data_layer import fmt_date, market_date
from ui import page_header

page_header(
    "Ask Cropora",
    "Ask about mandi prices, forecasts, selling decisions, crop problems, schemes or model accuracy in plain language.",
)

location = st.session_state.get("location", "Ludhiana")
top_row = st.columns([4, 1], vertical_alignment="center")
with top_row[0]:
    st.caption(
        f"Answers use your current location: **{location}**. "
        "Mention another city in the question to override it. Latest market date "
        f"{fmt_date(market_date())}."
    )
with top_row[1]:
    if st.button("Clear chat", width="stretch"):
        st.session_state["chat_messages"] = []
        st.rerun()

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

SUGGESTIONS = [
    "Wheat price in Karnal",
    "Should I sell onion near Nashik?",
    "7-day forecast for tomato near Pune",
    "Yellow stripes on wheat leaves",
    "Which crop has the best outlook this week?",
]


def _answer(prompt: str) -> str:
    return respond(prompt, location)


messages = st.session_state["chat_messages"]

if not messages:
    with st.chat_message("assistant", avatar=":material/eco:"):
        st.markdown(
            "Namaste. I can check today's mandi prices, show a seven-day forecast, compare mandis, "
            "suggest where to sell, identify common crop problems, explain government schemes and "
            "report the model's accuracy.\n\nTry one of the questions below, or type your own."
        )
    choice = st.pills(
        "Suggested questions",
        SUGGESTIONS,
        selection_mode="single",
        label_visibility="collapsed",
        key="chat_suggestions",
    )
    if choice:
        messages.append({"role": "user", "content": choice})
        messages.append({"role": "assistant", "content": _answer(choice)})
        st.rerun()

for message in messages:
    with st.chat_message(message["role"], avatar=":material/eco:" if message["role"] == "assistant" else None):
        st.markdown(message["content"])

prompt = st.chat_input("Ask Cropora about a crop, mandi or problem")
if prompt:
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    answer = _answer(prompt)
    with st.chat_message("assistant", avatar=":material/eco:"):
        st.markdown(answer)
    messages.append({"role": "assistant", "content": answer})

st.caption(
    "Rule-based assistant over the app's price data (Agmarknet when synced, sample "
    "otherwise) and curated knowledge base. "
    "It does not use an external AI service. Verify market and pesticide advice locally."
)
