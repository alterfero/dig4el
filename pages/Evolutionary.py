import streamlit as st
import json
from exploration.evolutionary101 import Belief

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

# Typological data ================================================

syntactic_elements = {
    "single specific invariable word" : {
        "paramaters": {
            "concept": "",
            "word": ""
        },
        "test": "test_single_specific_invariable_word"
    }
}

typological_knowledge = {
    "personal pronouns": {
        "can be searched individually": True,
        "can vary with": ["SEMANTIC ROLE", "NUMBER", "GENDER"]
    }
}


if not st.session_state["loaded_existing"]:
    with st.expander("Load knowledge graph"):
        existing_kg = st.file_uploader("Load an existing knowledge graph", type="json")
        if existing_kg is not None:
            st.session_state["knowledge_graph"] = json.load(existing_kg)
            st.session_state["loaded_existing"] = True

