# Copyright (C) 2024 Sebastien CHRISTIAN, University of French Polynesia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import streamlit as st
import json
from libs import knowledge_graph_utils as kgu
import pandas as pd

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "tl_name" not in st.session_state:
    st.session_state["tl_name"] = ""
if "delimiters" not in st.session_state:
    st.session_state["delimiters"] = []
if "loaded_existing" not in st.session_state:
    st.session_state["loaded_existing"] = ""
if "cq_transcriptions" not in st.session_state:
    st.session_state["cq_transcriptions"] = []
if "knowledge_graph" not in st.session_state:
    st.session_state["knowledge_graph"] = {}
if "cdict" not in st.session_state:
    st.session_state["cdict"] = {}

delimiters_bank = [
    " ",  # Space
    ".",  # Period or dot
    "?",  # Interrogation mark
    "!",  # Exclamation mark
    ",",  # Comma
    "·",  # Middle dot (interpunct)
    "‧",  # Small interpunct (used in some East Asian scripts)
    "․",  # Armenian full stop
    "-",  # Hyphen or dash (used in compound words or some languages)
    "_",  # Underscore (used in some digital texts and programming)
    "‿",  # Tironian sign (used in Old Irish)
    "、",  # Japanese comma
    "。",  # Japanese/Chinese full stop
    "።",  # Ge'ez (Ethiopian script) word separator
    ":",  # Colon
    ";",  # Semicolon
    "؟",  # Arabic question mark
    "٬",  # Arabic comma
    "؛",  # Arabic semicolon
    "۔",  # Urdu full stop
    "।",  # Devanagari danda (used in Hindi and other Indic languages)
    "॥",  # Double danda (used in Sanskrit and other Indic texts)
    "𐩖",  # South Arabian word divider
    "𐑀",  # Old Hungarian word separator
    "་",  # Tibetan Tsheg (used in Tibetan script)
    "᭞",  # Sundanese word separator
    "᠂",  # Mongolian comma
    "᠃",  # Mongolian full stop
    " ",  # Ogham space mark (used in ancient Irish writing)
    "꓿",  # Lisu word separator
    "፡",  # Ge'ez word separator
    "'",  # Apostrophe (used for contractions and possessives)
    "…",  # Ellipsis
    "–",  # En dash
    "—",  # Em dash
]
default_delimiters = [" ", ".", ",", ";", ":", "!", "?", "\u2026", "'"]

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")
    st.page_link("pages/Grammatical_Description.py", label="Generate Grammars", icon=":material/menu_book:")

    st.write("**Expert features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")
    st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

with st.expander("Input"):
    # load transcriptions or last kg
    if st.button("load last knowledge graph"):
        with open("./data/knowledge/current_kg.json", "r") as f:
            st.session_state.knowledge_graph = json.load((f))
        st.session_state["delimiters"] = default_delimiters


    cqs = st.file_uploader("Load Conversational Questionnaire transcriptions (all at once for multiple transcriptions)", type="json", accept_multiple_files=True)
    if cqs is not None:
        st.session_state["cq_transcriptions"] = []
        for cq in cqs:
            new_cq = json.load(cq)
            st.session_state["cq_transcriptions"].append(new_cq)
        st.session_state["loaded_existing"] = True
        st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))
    if st.session_state["loaded_existing"]:
        if st.session_state["cq_transcriptions"] != []:
            # managing delimiters
            if "delimiters" in st.session_state["cq_transcriptions"][0].keys():
                st.session_state["delimiters"] = st.session_state["cq_transcriptions"][0]["delimiters"]
                st.write("Word separators have been explicitly entered in the transcription.")
            else:
                st.session_state["delimiters"] = st.multiselect("Edit word separators if needed", delimiters_bank,
                                                                default=default_delimiters)
            # Consolidating transcriptions - Knowledge Graph
            if st.button("Build knowledge graph"):
                st.session_state[
                    "knowledge_graph"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                    st.session_state["cq_transcriptions"],
                    st.session_state["tl_name"],
                    st.session_state["delimiters"])
                with open("./data/knowledge/current_kg.json", "w") as f:
                    json.dump(st.session_state["knowledge_graph"], f, indent=4)
                st.write("{} Conversational Questionnaires: {} sentences, {} words with {} unique words".format(
                    len(st.session_state["cq_transcriptions"]), len(st.session_state["knowledge_graph"]),
                    total_target_word_count, len(unique_words)))

if st.session_state["knowledge_graph"] != {}:
    st.session_state["cdict"] = kgu.build_concept_dict(st.session_state["knowledge_graph"])

    with st.expander("Explore by concept", expanded=True):
        selected_concept = st.selectbox("Select a concept", list(st.session_state["cdict"].keys()), index=0)
        st.write("{} occurrences. Click on the left of any row to get more details on an entry.".format(len(st.session_state["cdict"][selected_concept])))

        #flatten cdict[selected] to display in a df
        flat_cdict_oc = []
        #st.write(st.session_state["cdict"][selected_concept])
        for oc in st.session_state["cdict"][selected_concept]:
            tmp = {}
            tmp["pivot_sentence"] = oc["pivot_sentence"]
            tmp["target_sentence"] = oc["target_sentence"]
            tmp["target_words"] = oc["target_words"]
            for param_cat, params in oc["particularization"].items():
                    for p, v in params.items():
                        tmp[f"{param_cat}_{p}"] = v
            flat_cdict_oc.append(tmp)

        oc_df = pd.DataFrame(flat_cdict_oc)
        def display_result():
            return None

        selected = st.dataframe(oc_df, selection_mode="single-row", on_select=display_result, key="oc_df")
        if selected["selection"]["rows"] != []:
            selected_cdict_entry = st.session_state["cdict"][selected_concept][(selected["selection"]["rows"][0])]
            kg_entry = selected_cdict_entry["kg_entry"]

            # Gloss of selected sentence
            st.write("---")
            st.write("Concepts and target words of the selected sentence: ")
            gloss = kgu.build_gloss_df(st.session_state["knowledge_graph"], kg_entry, st.session_state["delimiters"])
            st.dataframe(gloss)

            # Showing sentences using the same target word(s)
            st.write("---")
            if selected_cdict_entry["target_words"] != "":
                entries_with_target_word = kgu.get_sentences_with_word(st.session_state["knowledge_graph"],
                                                                   selected_cdict_entry["target_words"],
                                                                   st.session_state["delimiters"])
                current_entries = []
                for item in st.session_state["cdict"][selected_concept]:
                    current_entries.append(item["kg_entry"])
                current_entries = list(set(current_entries))
                st.write("Other occurrences of **{}** not connected to the concept {}:".format(
                    selected_cdict_entry["target_words"],
                    selected_concept))
                xcount = 0
                for e in entries_with_target_word:
                    if e not in current_entries:
                        xcount += 1
                        gloss = kgu.build_gloss_df(st.session_state["knowledge_graph"], e,
                                                   st.session_state["delimiters"])
                        st.write(st.session_state["knowledge_graph"][e]["sentence_data"]["text"])
                        st.write(st.session_state["knowledge_graph"][e]["recording_data"]["translation"])
                        st.dataframe(gloss)
                        st.write("---")
                if xcount == 0:
                    st.write("None")





