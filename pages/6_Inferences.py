import streamlit as st
import json
from exploration.evolutionary101 import Belief
from exploration import simple_inferences as si
from libs import knowledge_graph_utils as kgu
import pandas as pd

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "loaded_kg" not in st.session_state:
    st.session_state["loaded_kg"] = False
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

if not st.session_state["loaded_kg"]:
    with st.expander("Load knowledge graph"):
        existing_kg = st.file_uploader("Load an existing knowledge graph", type="json")
        if existing_kg is not None:
            st.session_state["knowledge_graph"] = json.load(existing_kg)
            st.session_state["loaded_kg"] = True

if st.session_state["loaded_kg"]:

    st.write("loaded Knowledge Graph with {} entries".format(len(st.session_state["knowledge_graph"])))

    # simple inferences: word order
    # based on the knowledge graph, describe word order in the target language.
    with st.expander("Word Order"):
        word_order_stats = si.analyze_word_order(st.session_state["knowledge_graph"])

        st.write("Intransitive events")
        st.write("based on {} intransitive events with known target representations in the knowledge graph, here's the distribution:".format(len(word_order_stats["intransitive"])))
        iwo_df = pd.DataFrame.from_dict(word_order_stats["stats"]["intransitive_word_order"], orient="index", columns=["count"]).sort_values(
            by="count", ascending=False).T
        st.dataframe(iwo_df)

        st.write("Transitive events")
        st.write(
            "based on {} transitive events with known target representations in the knowledge graph, here's the distribution:".format(
                len(word_order_stats["transitive"])))
        two_df = pd.DataFrame.from_dict(word_order_stats["stats"]["transitive_word_order"], orient="index",
                                        columns=["count"]).sort_values(by="count",ascending=False).T
        st.dataframe(two_df)

        if st.checkbox("show sentences"):
            s = st.selectbox("select order", list(word_order_stats["index_lists_by_order"].keys()))
            for index in word_order_stats["index_lists_by_order"][s]:
                df = kgu.build_gloss_df(st.session_state["knowledge_graph"], index)
                st.dataframe(df)


