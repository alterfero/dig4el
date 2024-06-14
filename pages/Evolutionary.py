import streamlit as st
import json
from exploration import evolutionary101

if "loaded_existing" not in st.session_state:
    st.session_state["loaded_existing"] = False
if "knowledge_graph" not in st.session_state:
    st.session_state["knowledge_graph"] = {}

concept_kson = json.load(open("./data/concepts.json"))

delimiters = {
    "french": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "english": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "marquesan (Nuku Hiva)": [" ", ".", ",", ";", ":", "!", "?", "…"]
}


if not st.session_state["loaded_existing"]:
    with st.expander("Load knowledge graph"):
        existing_kg = st.file_uploader("Load an existing knowledge graph", type="json")
        if existing_kg is not None:
            st.session_state["knowledge_graph"] = json.load(existing_kg)
            st.session_state["loaded_existing"] = True

