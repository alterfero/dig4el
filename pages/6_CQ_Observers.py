import streamlit as st
import json
from exploration.evolutionary101 import Belief
from exploration import simple_inferences as si
from libs import knowledge_graph_utils as kgu, wals_utils as wu
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

delimiters = json.load(open("./data/delimiters.json"))
available_target_languages = list(delimiters.keys())
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

# ====================================================================

with st.expander("Load or compute a knowledge graph"):
    if not st.session_state["loaded_kg"]:
        existing_kg = st.file_uploader("Load an existing knowledge graph", type="json")
        if existing_kg is not None:
            st.session_state["knowledge_graph"] = json.load(existing_kg)
            st.session_state["loaded_kg"] = True

    language = st.selectbox("Select a language", available_target_languages, index=0)
    if st.button("Compute new knowledge graph"):
        st.session_state["knowledge_graph"], unique_words, unique_words_frequency, total_target_word_count = (
            kgu.build_knowledge_graph(language))
        st.write("total_target_word_count: {}".format(total_target_word_count))
        if st.session_state["knowledge_graph"] != {}:
            st.session_state["loaded_kg"] = True

if st.session_state["loaded_kg"]:

    st.write("loaded Knowledge Graph with {} entries".format(len(st.session_state["knowledge_graph"])))

    # simple inferences: word order
    # based on the knowledge graph, describe word order in the target language.
    with st.expander("Word Order"):
        st.subheader("Word Order")
        word_order_stats = si.analyze_word_order(st.session_state["knowledge_graph"])
        colc, colv = st.columns(2)
        colc.write("Intransitive events")
        colc.write("Distribution of {} intransitive events with known target representations in the knowledge graph:".format(len(word_order_stats["intransitive"])))
        iwo_df = pd.DataFrame.from_dict(word_order_stats["stats"]["intransitive_word_order"], orient="index", columns=["count"]).sort_values(
            by="count", ascending=False).T
        colc.dataframe(iwo_df)

        colv.write("Transitive events")
        colv.write(
            "Distribution of {} transitive events with known target representations in the knowledge graph:".format(
                len(word_order_stats["transitive"])))
        two_df = pd.DataFrame.from_dict(word_order_stats["stats"]["transitive_word_order"], orient="index",
                                        columns=["count"]).sort_values(by="count",ascending=False).T
        colv.dataframe(two_df)

        if st.checkbox("show sentences"):
            s = st.selectbox("select order", list(word_order_stats["index_lists_by_order"].keys()))
            for index in word_order_stats["index_lists_by_order"][s]:
                df = kgu.build_gloss_df(st.session_state["knowledge_graph"], index)
                st.dataframe(df)

        if st.checkbox("Show description"):
            if language == "french":
                st.write("This language strongly favors agent-initial word orders, with AEP dominating transitive constructions and AE prevailing in intransitive ones across various sentence types and both wildcard and non-wildcard contexts. Alternative orders serve specific functions: APE, often wildcard-marked, appears flexible and is used mainly for assertions and questions with processive predicates; PAE, mostly non-wildcard, occurs in diverse sentence types; PEA, exclusively non-wildcard, is rare and specific to certain question types and epistemic expressions. The single instances of EAP and EA orders suggest highly specialized uses. This pattern indicates a language with a default agent-first structure but with the flexibility to employ marked word orders for particular semantic or pragmatic purposes, with wildcard markings generally associated with more variable constructions.")
            elif language == "marquesan (Nuku Hiva)":
                st.write("**For linguists**: This language shows a strong preference for event-initial word orders, with EAP (Event-Agent-Patient) dominating transitive constructions and EA (Event-Agent) slightly favoring intransitive ones. For transitive sentences, EAP is the most common order (8 instances), followed by AEP (4 instances), with a single occurrence of EPA. Intransitive sentences show a close split between EA (8 instances) and AE (5 instances). The language demonstrates flexibility in word order, with EAP used across various sentence types including questions, assertions, and orders, in both wildcard and non-wildcard contexts. AEP appears in specific constructions like questions, assertions, and deontic expressions. Notably, patient-initial orders (PAE, PEA) and APE are absent. This pattern suggests a language with a default event-initial structure, but with the capacity to use agent-initial orders for particular semantic or pragmatic purposes. The distribution of wildcard markings doesn't show a clear pattern, indicating that word order flexibility might not be strongly tied to specific construction types.")
                st.write("**For an english-speaking 8 years old**: In this language, people like to start their sentences with what's happening (the action). It's like saying 'Running is the dog' instead of 'The dog is running.' They do this a lot, especially when they're talking about someone doing something to something else. Sometimes they start with who's doing the action, but not as often. They can mix up the order of words to mean different things, like asking questions or giving orders. It's kind of like a puzzle where you can move the pieces around, but some ways of putting the pieces together are used more than others. The cool thing is, they never start a sentence with the thing that's being acted on - it's always the action or the person doing it first.")
        filename = ("word_order_stats.json")
        st.download_button(label="download word order statistics", data=json.dumps(word_order_stats, indent=4),
                           file_name=filename)
