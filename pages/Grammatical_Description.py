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
import math
import os
import re
import pandas as pd
from libs import utils as u, wals_utils as wu, general_agents, grambank_utils as gu
from libs import grambank_wals_utils as gwu
from libs import knowledge_graph_utils as kgu
from libs import cq_observers as obs
from libs import general_agents
from libs import output_generation_utils as ogu
from libs import ga_param_selection_utils as psu
import json
import openai
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import plotly.graph_objects as go
from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple, List, Set
import tiktoken

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "tl_name" not in st.session_state:
    st.session_state["tl_name"] = ""
if "tl_wals_pk" not in st.session_state:
    st.session_state["tl_wals_pk"] = ""
if "tl_grambank_id" not in st.session_state:
    st.session_state["tl_grambank_id"] = ""
if "delimiters" not in st.session_state:
    st.session_state["delimiters"] = []
if "selected_topics" not in st.session_state:
    st.session_state["selected_topics"] = None
if "loaded_existing" not in st.session_state:
    st.session_state["loaded_existing"] = ""
if "cq_transcriptions" not in st.session_state:
    st.session_state["cq_transcriptions"] = []
if "kg" not in st.session_state:
    st.session_state["kg"] = {}
if "tl_knowledge" not in st.session_state:
    st.session_state["tl_knowledge"] = {
        "known_wals": {},
        "known_wals_pk": {},
        "known_grambank": {},
        "known_grambank_pid": {},
        "observed": {},
        "inferred": {}
    }
if "ga" not in st.session_state:
    st.session_state["ga"] = None
if "parameter_selection_ga" not in st.session_state:
    st.session_state["parameter_selection_ga"] = None
if "known_processed" not in st.session_state:
    st.session_state["known_processed"] = False
if "observations_processed" not in st.session_state:
    st.session_state["observations_processed"] = False
if "redacted" not in st.session_state:
    st.session_state["redacted"] = ""
if "obs" not in st.session_state:
    st.session_state["obs"] = {}
if "belief_history" not in st.session_state:
    st.session_state["belief_history"] = {}
if "consensus_store" not in st.session_state:
    st.session_state["consensus_store"] = {}
if "run_ga" not in st.session_state:
    st.session_state["run_ga"] = False
if "ga_output_available" not in st.session_state:
    st.session_state["ga_output_available"] = False
if "generate_description" not in st.session_state:
    st.session_state["generate_description"] = False
if "results_approved" not in st.session_state:
    st.session_state["results_approved"] = False
if "prompt_content" not in st.session_state:
    st.session_state["prompt_content"] = {}
if "output" not in st.session_state:
    st.session_state["output"] = {}
if "params_by_topic" not in st.session_state:
    with open("./external_data/params_by_topic.json", "r") as f:
        st.session_state["params_by_topic"] = json.load(f)
if "docx_file_ready" not in st.session_state:
    st.session_state["docx_file_ready"] = False
if "audience_language" not in st.session_state:
    st.session_state["audience_language"] = "English"
if "audience" not in st.session_state:
    st.session_state["audience"] = "adult beginners"
if "content_description" not in st.session_state:
    st.session_state["content_description"] = "grammar lesson"
if "final_output" not in st.session_state:
    st.session_state["final_output"] = {}
if "response" not in st.session_state:
    st.session_state["response"] = ""
if "preprocessing_done" not in st.session_state:
    st.session_state["preprocessing_done"] = False
if "computing_done" not in st.session_state:
    st.session_state["computing_done"] = False
if "initial_llm_request_done" not in st.session_state:
    st.session_state["initial_llm_request_done"] = False
if "polishing_done" not in st.session_state:
    st.session_state["polishing_done"] = False
if "polished_docx_file_ready" not in st.session_state:
    st.session_state["polished_docx_file_ready"] = False
if "docx_file" not in st.session_state:
    st.session_state["docx_file"] = None
if "docx_file_plain" not in st.session_state:
    st.session_state["docx_file_plain"] = True
if "preprocess_done" not in st.session_state:
    st.session_state["preprocess_done"] = False
if "selected_parameters_by_topic" not in st.session_state:
    st.session_state["selected_parameters_by_topic"] = {}
if "l_filter" not in st.session_state:
    st.session_state["l_filter"] = {}
if "ga_param_names" not in st.session_state:
    st.session_state["ga_param_names"] = {}
if "strong_seeds" not in st.session_state:
    st.session_state["strong_seeds"] = {}
if "selected_parameters" not in st.session_state:
    st.session_state["selected_parameters"] = {}

# ---------- LLM response helpers ----------
def safe_json(text: str) -> str:
    """
    Escape raw newlines and stray unescaped quotes that appear
    *inside* double-quoted values.
    """
    # 1) replace CR/LF inside quoted strings with \n
    text = re.sub(r'(".*?)(\r?\n)(.*?")',
                  lambda m: m.group(1) + "\\n" + m.group(3),
                  text, flags=re.S)
    # 2) escape naked " inside values → \"
    text = re.sub(r'(".*?[^\\])"(.*?")',
                  lambda m: m.group(1) + '\\"' + m.group(2),
                  text, flags=re.S)
    return text


def decode(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(safe_json(raw))
# -----------------------------------------

# GLOBAL VARIABLES =============================================

observed_params = {
    "Order of Subject, Object and Verb": {"code": "81", "observer": (obs.observer_order_of_subject_object_verb, True)},
    "Order of Subject and Verb": {"code": "82", "observer": (obs.observer_order_of_subject_and_verb, True)},
    "Order of Object and Verb": {"code": "83", "observer": None},
    "Order of Adjective and Noun": {"code": "87", "observer": (obs.observer_order_of_adjective_and_noun, False)},
    "Order of Demonstrative and Noun": {"code": "88",
                                        "observer": (obs.observer_order_of_demonstrative_and_noun, False)},
    "Order of Relative Clause and Noun": {"code": "87",
                                          "observer": (obs.observer_order_of_relative_clause_and_noun, False)},
    "Is there a male/female distinction in 1st person independent pronouns?": {"code": "GB197", "observer": (
    obs.observer_free_pp1_gender, False)},
    "Is there a male/female distinction in 2nd person independent pronouns?": {"code": "GB196", "observer": (
    obs.observer_free_pp2_gender, False)},
    "Is there a gender distinction in independent 3rd person pronouns?": {"code": "GB030", "observer": (
    obs.observer_free_pp3_gender, False)},
    "Are there morphological cases for pronominal core arguments (i.e. S/A/P)?": {"code": "GB071", "observer": (
    obs.observer_free_pp1sg_semantic_role, False)},
    "Inclusive/Exclusive Distinction in Independent Pronouns": {"code": "39", "observer": (
    obs.observer_free_pp_inclusive_exclusive, False)},
}

NUMBER_OF_MESSAGING_CYCLES = 3

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

CP_MIN = 0.8

BELIEF_MIN = 0.8

d = 5

SCORE_MIN = 0.85

K = 50

# ==================================================================

def create_probability_df(cross_consensus_stat):
    data_points = []

    for param, values_dict in cross_consensus_stat.items():
        for value_id, probabilities in values_dict.items():
            for iteration, prob in enumerate(probabilities):
                data_points.append({
                    'Parameter': param,
                    'Value_ID': value_id,
                    'Iteration': iteration + 1,
                    'Probability': prob
                })

    return pd.DataFrame(data_points)


def display_analysis(cross_consensus_stat):
    # Create DataFrame
    df = create_probability_df(cross_consensus_stat)

    # Parameter selector
    params = df['Parameter'].unique()
    selected_param = st.selectbox("Select Parameter", params)

    # Filter data for selected parameter
    param_df = df[df['Parameter'] == selected_param]

    # Create figure
    fig = go.Figure()

    # Color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    # Add traces for each Value_ID
    for i, value_id in enumerate(param_df['Value_ID'].unique()):
        value_data = param_df[param_df['Value_ID'] == value_id]

        # Add line
        fig.add_trace(go.Scatter(
            x=value_data['Iteration'],
            y=value_data['Probability'],
            name=f'Value {value_id}',
            line=dict(color=colors[i % len(colors)]),
            mode='lines+markers',
            marker=dict(size=8),
            hovertemplate="Iteration: %{x}<br>" +
                          "Probability: %{y:.2e}<br>" +
                          f"Value: {value_id}<extra></extra>"
        ))

    # Update layout
    fig.update_layout(
        title=f'Probability Distribution Across Iterations: {selected_param}',
        xaxis_title='Iteration',
        yaxis_title='Probability',
        yaxis_type='log',
        hovermode='closest',
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Get final probabilities
    final_probs = param_df[param_df['Iteration'] == param_df['Iteration'].max()]

    # Create summary statistics
    summary_stats = param_df.groupby('Value_ID').agg({
        'Probability': ['mean', 'std', 'median', 'min', 'max']
    }).round(10)

    summary_stats.columns = ['Mean', 'Std Dev', 'Median', 'Min', 'Max']

    # Format summary stats to scientific notation
    for col in summary_stats.columns:
        summary_stats[col] = summary_stats[col].apply(lambda x: f"{x:.2e}")

    st.subheader("Statistics Across Iterations")
    st.dataframe(summary_stats)

    # Optional: Add a box plot view
    show_boxplot = st.checkbox("Show Distribution Boxplot")
    if show_boxplot:
        fig_box = go.Figure()

        for i, value_id in enumerate(param_df['Value_ID'].unique()):
            value_data = param_df[param_df['Value_ID'] == value_id]

            fig_box.add_trace(go.Box(
                y=value_data['Probability'],
                name=f'Value {value_id}',
                marker_color=colors[i % len(colors)]
            ))

        fig_box.update_layout(
            title='Probability Distribution by Value',
            yaxis_type='log',
            height=400,
            showlegend=False
        )

        st.plotly_chart(fig_box, use_container_width=True)

st.sidebar.subheader("DIG4EL")
st.sidebar.write("Process")
side_info = st.sidebar.empty()

with st.sidebar:
    st.markdown("---")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")
    st.page_link("pages/Transcriptions_explorer.py", label="Explore transcriptions", icon=":material/search:")
    st.page_link("pages/Grammatical_Description.py", label="Generate Grammars", icon=":material/menu_book:")

    st.write("**Expert features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")
    st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

st.title("Generate grammatical descriptions")
colk1, colk2 = st.columns(2)
with colk1.popover("i"):
    st.write(
        "This is an early prototype of inferential outputs, enabled for testing purposes. Outputs are meant to be reviewed by a speaker of the language.")
show_details = colk2.toggle("Show computation details")
# INPUTS ========================================================================
if not st.session_state["loaded_existing"]:
    side_info.write("Waiting for transcription files")
with st.expander("Inputs"):
    if st.button("reset"):
        st.session_state["tl_name"] = ""
        st.session_state["tl_wals_pk"] = ""
        st.session_state["tl_grambank_id"] = ""
        st.session_state["delimiters"] = []
        st.session_state["selected_topics"] = None
        st.session_state["loaded_existing"] = ""
        st.session_state["cq_transcriptions"] = []
        st.session_state["kg"] = {}
        st.session_state["tl_knowledge"] = {
            "known_wals": {},
            "known_wals_pk": {},
            "known_grambank": {},
            "known_grambank_pid": {},
            "observed": {},
            "inferred": {}
        }
        st.session_state["ga"] = None
        st.session_state["run_ga"] = False
        st.session_state["known_processed"] = False
        st.session_state["observations_processed"] = False
        st.session_state["obs"] = {}
        st.session_state["consensus_store"] = {}
        st.session_state["belief_history"] = {}
        st.session_state["ga_output_available"] = False
        st.session_state["generate_description"] = False
        st.session_state["results_approved"] = False
        st.session_state["prompt_content"] = {}
        st.session_state["output"] = {}
        st.session_state["docx_file_ready"] = False
        st.session_state["audience_language"] = "English"
        st.session_state["audience"] = "adult beginners"
        st.session_state["content_description"] = "grammar lesson"
        st.session_state["final_output"] = {}
        st.session_state["response"] = ""
        st.session_state["preprocessing_done"] = False
        st.session_state["computing_done"] = False
        st.session_state["polishing_done"] = False
        st.session_state["polished_docx_file_ready"] = False
        st.session_state["docx_file"] = None
        st.session_state["docx_file_plain"] = True
        st.session_state["selected_parameters_by_topic"] = {}
        st.session_state["selected_parameters"] = []
        st.session_state["strong_seeds"] = []
        st.rerun()

    # MANAGING CQ TRANSCRIPTIONS

    cqs = st.file_uploader(
        "Load Conversational Questionnaires' transcriptions (all at once for multiple transcriptions)", type="json",
        accept_multiple_files=True)
    if cqs is not None:
        st.session_state["cq_transcriptions"] = []
        for cq in cqs:
            new_cq = json.load(cq)
            # update concept labels
            updated_cq, found_some = u.update_concept_names_in_transcription(new_cq)
            if found_some:
                st.write("Some concept labels have been aligned with the latest version.")
            st.session_state["cq_transcriptions"].append(updated_cq)
        st.session_state["loaded_existing"] = True
        st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))

    # load transcriptions, create knowledge graph
    if st.session_state["loaded_existing"]:
        if st.session_state["cq_transcriptions"] != []:
            # Consolidating transcriptions - Knowledge Graph
            st.session_state[
                "kg"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                st.session_state["cq_transcriptions"],
                st.session_state["tl_name"],
                st.session_state["delimiters"])
            with open("./data/knowledge/current_kg.json", "w") as f:
                json.dump(st.session_state["kg"], f, indent=4)
            st.write("{} Conversational Questionnaires: {} sentences, {} words with {} unique words".format(
                len(st.session_state["cq_transcriptions"]), len(st.session_state["kg"]),
                total_target_word_count, len(unique_words)))
            # managing language input
            st.session_state["tl_name"] = st.session_state["cq_transcriptions"][0]["target language"]
            # check data in wals
            st.session_state["tl_wals_pk"] = wu.language_pk_id_by_name.get(st.session_state["tl_name"], {}).get("pk",
                                                                                                                None)
            # check data in grambank
            if st.session_state["tl_name"] in [gu.grambank_language_by_lid[lid]["name"] for lid in
                                               gu.grambank_language_by_lid.keys()]:
                st.session_state["tl_grambank_id"] = next(lid for lid, value in gu.grambank_language_by_lid.items() if
                                                          value["name"] == st.session_state["tl_name"])
            else:
                st.session_state["tl_grambank_id"] = None
            # managing delimiters
            if "delimiters" in st.session_state["cq_transcriptions"][0].keys():
                st.session_state["delimiters"] = st.session_state["cq_transcriptions"][0]["delimiters"]
                print("Word separators have been explicitly entered in the transcription.")
            elif st.session_state["tl_name"] in wu.language_pk_id_by_name.keys():
                with open("./data/delimiters.json", "r") as f:
                    delimiters_dict = json.load(f)
                    st.session_state["delimiters"] = delimiters_dict[st.session_state["tl_name"]]
                    print("Word separators are retrieved from a file.")
            else:
                st.session_state["delimiters"] = st.multiselect("Edit word separators if needed", delimiters_bank,
                                                                default=default_delimiters)
            side_info.write("Input files mapped")

    if cqs == []:
        st.markdown("---")
        st.markdown("#### or use available examples")
        available_transcriptions_folders = os.listdir(os.path.join(".", "available_transcriptions"))
        if ".DS_Store" in available_transcriptions_folders:
            available_transcriptions_folders.remove(".DS_Store")
        existing = st.selectbox("Or load an available set of transcriptions", available_transcriptions_folders)
        if st.button(f"Load {existing}"):
            tpath = os.path.join(".", "available_transcriptions", existing)
            if os.path.isdir(tpath):
                st.session_state["cq_transcriptions"] = []
                for t in os.listdir(tpath):
                    if t.endswith(".json"):
                        with open(os.path.join(tpath, t)) as f:
                            new_cq = json.load(f)
                            st.session_state["cq_transcriptions"].append(new_cq)
            if st.session_state["cq_transcriptions"] != []:
                st.session_state["delimiters"] = st.session_state["cq_transcriptions"][0]["delimiters"]
                st.session_state[
                    "kg"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                    st.session_state["cq_transcriptions"],
                    st.session_state["tl_name"],
                    st.session_state["delimiters"])
                with open("./data/knowledge/current_kg.json", "w") as f:
                    json.dump(st.session_state["kg"], f, indent=4)
                st.write("{} Conversational Questionnaires: {} sentences, {} words with {} unique words".format(
                    len(st.session_state["cq_transcriptions"]), len(st.session_state["kg"]),
                    total_target_word_count, len(unique_words)))
                st.session_state["loaded_existing"] = True
                st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))
                # managing language input
                st.session_state["tl_name"] = st.session_state["cq_transcriptions"][0]["target language"]
                # check data in wals
                st.session_state["tl_wals_pk"] = wu.language_pk_id_by_name.get(st.session_state["tl_name"], {}).get(
                    "pk",
                    None)
                # check data in grambank
                if st.session_state["tl_name"] in [gu.grambank_language_by_lid[lid]["name"] for lid in
                                                   gu.grambank_language_by_lid.keys()]:
                    st.session_state["tl_grambank_id"] = next(
                        lid for lid, value in gu.grambank_language_by_lid.items() if
                        value["name"] == st.session_state["tl_name"])
                else:
                    st.session_state["tl_grambank_id"] = None
                # managing delimiters
                if "delimiters" in st.session_state["cq_transcriptions"][0].keys():
                    st.session_state["delimiters"] = st.session_state["cq_transcriptions"][0]["delimiters"]
                    print("Word separators have been explicitly entered in the transcription.")
                elif st.session_state["tl_name"] in wu.language_pk_id_by_name.keys():
                    with open("./data/delimiters.json", "r") as f:
                        delimiters_dict = json.load(f)
                        st.session_state["delimiters"] = delimiters_dict[st.session_state["tl_name"]]
                        print("Word separators are retrieved from a file.")
                else:
                    st.session_state["delimiters"] = st.multiselect("Edit word separators if needed", delimiters_bank,
                                                                    default=default_delimiters)
                side_info.write("Input files mapped")


# PREPROCESSING: KNOWLEDGE, OBSERVATIONS, PARAMETER DISCOVERY ==============================

if st.session_state["kg"] and not st.session_state["preprocessing_done"]:
    side_info.write("Retrieving specific knowledge")
    col8, col9 = st.columns(2)
    # RETRIEVING KNOWLEDGE ==============================================================
    if st.session_state["tl_name"] != "":
        # WALS
        if st.session_state["tl_wals_pk"] is not None:
            if st.session_state["tl_wals_pk"] in wu.domain_elements_by_language.keys():
                known_values = wu.domain_elements_by_language[st.session_state["tl_wals_pk"]]
                for known_value in known_values:
                    p_name = wu.parameter_name_by_pk[wu.param_pk_by_de_pk[str(known_value)]]
                    de_name = wu.domain_element_by_pk[str(known_value)]["name"]
                    st.session_state["tl_knowledge"]["known_wals"][p_name] = de_name
                    st.session_state["tl_knowledge"]["known_wals_pk"][p_name] = str(known_value)
        if len(st.session_state["tl_knowledge"]["known_wals"]) != 0 and show_details:
            col8.write("**WALS**")
            col8.markdown("{} known parameters in WALS".format(len(st.session_state[
                                                                       "tl_knowledge"][
                                                                       "known_wals"])))

        elif len(st.session_state["tl_knowledge"]["known_wals"]) == 0 and show_details:
            col8.write("No known parameter in WALS")

        # GRAMBANK
        if st.session_state["tl_grambank_id"] is not None:
            ginfo = gu.get_grambank_language_data_by_id_or_name(st.session_state["tl_grambank_id"])
            known_pids = ginfo.keys()
            for known_pid in known_pids:
                p_name = gu.grambank_pname_by_pid[known_pid]
                v_name = gu.grambank_vname_by_vid[ginfo[known_pid]["vid"]]
                st.session_state["tl_knowledge"]["known_grambank"][p_name] = v_name
                st.session_state["tl_knowledge"]["known_grambank_pid"][p_name] = ginfo[known_pid]["vid"]
        if len(st.session_state["tl_knowledge"]["known_grambank"]) != 0 and show_details:
            col9.write("**Grambank**")
            col9.markdown("{} known relevant parameters in Grambank".format(len(st.session_state["tl_knowledge"][
                                                                                    "known_grambank"])))
        elif len(st.session_state["tl_knowledge"]["known_grambank"]) == 0 and show_details:
            col9.write("No known parameter in Grambank")
        st.session_state["known_processed"] = True

    # PROCESSING TRANSCRIPTIONS

    # OBSERVATIONS: RUN ALL AVAILABLE OBSERVERS =================================================================
    side_info.write("Making observations")
    if st.session_state["kg"] != {}:
        # run all available observers
        for param_name, param_info in observed_params.items():
            if param_info["observer"] is not None:
                (func, canonical) = param_info["observer"]
                st.session_state["obs"][param_name] = func(
                    st.session_state["kg"],
                    st.session_state["tl_name"],
                    st.session_state["delimiters"],
                    canonical=canonical
                )
                st.session_state["tl_knowledge"]["observed"][param_name] = st.session_state["obs"][param_name][
                    "agent-ready observation"]

        st.session_state["observations_processed"] = True
        # st.write("st.session_state['tl_knowledge']")
        # st.write(st.session_state["tl_knowledge"])
        # st.write("st.session_state['obs']")
        # st.write(st.session_state["obs"])

    # STATISTICAL PRIORS =====================================================================
    side_info.write("Computing statistical priors")
    if st.session_state["known_processed"] and st.session_state["observations_processed"]:

        prior_family_list = []
        is_family_set = False
        # if no knowledge on this language, ask for alternatives to compute priors
        if st.session_state["tl_knowledge"]["known_wals"] == {} and st.session_state["tl_knowledge"][
            "known_grambank"] == {}:
            base_lname_list = list(set(list(wu.language_pk_id_by_name.keys()) + [linfo["name"] for lid, linfo in
                                                                                 gu.grambank_language_by_lid.items()]))
            similar_lnames = st.multiselect("If you know languages that resemble {}, select one or several of them.".format(
                st.session_state["tl_name"]), base_lname_list)
            prior_family_list = list(set([gwu.get_language_family_by_language_name(lname) for lname in similar_lnames]))
        # otherwise use language family to compute priors
        else:
            prior_family_list = [gwu.get_language_family_by_language_name(st.session_state["tl_name"])]

        if prior_family_list != []:
            st.session_state["l_filter"] = {"family": prior_family_list}
        else:
            st.session_state["l_filter"] = {}

        # SELECT RELEVANT PARAMETERS BY EXPANDING FRONTIER BASED ON OBSERVED AND KNOWN ============

        # Populate ga_param_codes and st.session_state["ga_param_names"],
        # Initialize st.session_state["prompt_content"] by topic (topic removed from this version)

        # build general graph with all wals and grambank values  ----------------------------
        BASE_DIR = Path("./external_data")
        st.session_state["G"] = psu.load_all_cpts(BASE_DIR)
        print(f'Graph: |V|={st.session_state["G"].number_of_nodes()}, |E|={st.session_state["G"].number_of_edges()}')

        # naive uniform priors (replace with family priors if it makes sense) ---
        priors = {v: 1 / st.session_state["G"].number_of_nodes() for v in st.session_state["G"].nodes}
        parameter_selection_belief = psu.BeliefState(priors)

        # feed observations: use a General Agent to get beliefs from observations -----------------------------------
        st.session_state["parameter_selection_ga"] = general_agents.GeneralAgent("parameter_selection_ga",
                                                                                 parameter_names=[str(name) for name in
                                                                                                  st.session_state[
                                                                                                      'obs'].keys()],
                                                                                 language_stat_filter={})

        for observed_param_name in st.session_state["tl_knowledge"]["observed"]:
            st.session_state["parameter_selection_ga"].add_observations(observed_param_name,
                                                                        st.session_state["tl_knowledge"]["observed"][
                                                                            observed_param_name])

        st.session_state["parameter_selection_ga"].run_belief_update_from_observations()

        for p in st.session_state["parameter_selection_ga"].language_parameters.keys():
            for v_code in st.session_state["parameter_selection_ga"].language_parameters[p].beliefs.keys():
                proba = st.session_state["parameter_selection_ga"].language_parameters[p].beliefs[v_code]
                parameter_selection_belief.update_observation(v_code, proba)  # soft evidence

        # feed knowledge
        for p, v in st.session_state["tl_knowledge"]["known_wals_pk"].items():
            parameter_selection_belief.set_known(v)  # hard evidence
        for p, v in st.session_state["tl_knowledge"]["known_grambank_pid"].items():
            parameter_selection_belief.set_known(v)  # hard evidence

        # select parameters ----------------------------------------------
        side_info.write("Discovering parameters")
        st.subheader("Parameter discovery")
        st.markdown("{} parameters observed, {} known from WALS, {} known from Grambank.  parameters".format(
            len(st.session_state["tl_knowledge"]["observed"]),
            len(st.session_state["tl_knowledge"]["known_wals_pk"]),
            len(st.session_state["tl_knowledge"]["known_grambank_pid"]
                )))

        # --------------------------------------------------------
        # 1.  Run suggest_parameters *once* and cache the ranking
        # --------------------------------------------------------



        # seeds = all values whose belief ≥ BELIEF_MIN
        st.session_state["strong_seeds"] = set(parameter_selection_belief.strong_values(0.9))

        st.session_state["selected_parameters"] = psu.suggest_parameters(
            st.session_state["G"],
            parameter_selection_belief,
            θ_CP=CP_MIN,  # floor on edge weights kept during frontier expansion.
            θ_belief=BELIEF_MIN,  # threshold above which a value is considered *strong*
            d=d,  # BFS depth limit
            θ_score=SCORE_MIN,  # minimum score for a candidate to be proposed
            K=K,  # top‑k suggestions to return
        )
        st.write("{} Strong parameters, enabling a reach of {} other parameters.".format(len(st.session_state["strong_seeds"]),
                                                                                         len(st.session_state["selected_parameters"])))

        ranked = list(psu.suggest_parameters(
            st.session_state["G"],
            parameter_selection_belief,
            θ_CP=CP_MIN,  # floor on edge weights kept during frontier expansion.
            θ_belief=BELIEF_MIN,  # threshold above which a value is considered *strong*
            d=d,  # BFS depth limit
            θ_score=SCORE_MIN,  # minimum score for a candidate to be proposed
            K=K,  # top‑k suggestions to return
        ))
        st.session_state["top_nodes"] = {vid for vid, _ in ranked}

        # let user choose topics of interest, knowing the parameters available in each
        available_parameter_names = [gwu.get_pname_from_value_code(code[0]) for code in st.session_state["selected_parameters"]] + [
            gwu.get_pname_from_value_code(code) for code in st.session_state["strong_seeds"]]

        p_per_topic = []
        tc = 0
        for topic in st.session_state["params_by_topic"]:
            c = 0
            found_p = False
            for p in available_parameter_names:
                if p in st.session_state["params_by_topic"][topic]:
                    c += 1
                    found_p = True
            if not found_p:
                print(f"parameter {p} not found in params_by_topic")
            p_per_topic.append({"topic": topic, "count": c})
            tc += c
        st.dataframe(pd.DataFrame(p_per_topic))
        st.write("Total count: {}".format(tc))

        st.session_state["selected_topics"] = st.multiselect("Choose topics (leaving blank will select all topics)", ["All"] +
                                                             list(st.session_state["params_by_topic"].keys()))

        if "All" in st.session_state["selected_topics"] or st.session_state["selected_topics"] == []:
            st.session_state["selected_topics"] = [topic for topic in list(st.session_state["params_by_topic"].keys())]

        for selected_topic in st.session_state["selected_topics"]:
            st.session_state["selected_parameters_by_topic"][selected_topic] = \
                [p for p in st.session_state["params_by_topic"][selected_topic] if p in available_parameter_names]

        st.session_state["preprocessing_done"] = True
        side_info.write("Preprocessing done")

# END PREPROCESSING

# SHOW DETAILS
if st.session_state["preprocessing_done"] and show_details:
    st.write("#### Known parameters in {}".format(st.session_state["tl_name"]))
    show_params = st.toggle("Show known WALS parameters")
    if show_params:
        st.write(st.session_state["tl_knowledge"]["known_wals"])
    show_params = st.toggle("Show known Grambank parameters")
    if show_params:
        st.write(st.session_state["tl_knowledge"]["known_grambank"])
    if show_details:
        st.markdown("#### Retrieving **observed** information in Conversational Questionnaires")
        show_observed_details = st.toggle("Show details about observations")
        # st.write(st.session_state["obs"])
        if show_observed_details:
            for pobs in st.session_state["obs"]:
                if len(st.session_state["obs"][pobs]["observations"]) != 0:
                    st.markdown("#### {}".format(pobs))
                    for de_name, details in st.session_state["obs"][pobs]["observations"].items():
                        if details["count"] != 0:
                            st.write("---------------------------------------------")
                            st.write("**{}** in ".format(de_name))
                            for occurrence_index, context in details["details"].items():
                                st.markdown("- ***{}***".format(
                                    st.session_state["kg"][occurrence_index]["recording_data"]["translation"]))
                                st.write(st.session_state["kg"][occurrence_index]["sentence_data"]["text"])
                                gdf = kgu.build_gloss_df(st.session_state["kg"], occurrence_index,
                                                         st.session_state["delimiters"])
                                st.dataframe(gdf)
                                st.write("context: {}".format(context))
                    st.markdown("-------------------------------------")
        # STRONG SEEDS AND PARAMS
        if st.toggle("See strong parameters and reach"):
            colx1, colx2 = st.columns(2)
            colx1.markdown("**Strong parameters**")
            for p in st.session_state["strong_seeds"]:
                colx1.write("*{}*".format(gwu.get_pname_from_value_code(p)))
                colx1.write(gwu.get_pvalue_name_from_value_code(p))
                colx1.write("---")
            colx2.markdown("**Probabilistic Reach above score threshold**")
            for p in st.session_state["selected_parameters"]:
                colx2.write("*{}*".format(gwu.get_pname_from_value_code(p[0])))
                colx2.write(gwu.get_pvalue_name_from_value_code(p[0]))
                colx2.write("Score: {}".format(round(p[1], 2)))
                colx2.write("---")
        # NETWORK
        if st.toggle("Display network"):
            # --------------------------------------------------------
            # 2.  Build the visual sub-graph = seeds ∪ st.session_state["top_nodes"]
            # --------------------------------------------------------
            visible_nodes = st.session_state["strong_seeds"].union(st.session_state["top_nodes"])
            net = Network(height="600px", width="100%", directed=True, bgcolor="#ffffff")
            net.force_atlas_2based()

            # -- nodes ------------------------------------------------

            for node in st.session_state["strong_seeds"]:
                p_value_name = gwu.get_pvalue_name_from_value_code(node)
                p_name = gwu.get_pname_from_value_code(node)
                net.add_node(node,
                             label=p_name,
                             color="#8cd790",
                             title=f"{p_name}: {p_value_name}")

            for node in st.session_state["top_nodes"]:
                p_value_name = gwu.get_pvalue_name_from_value_code(node)
                p_name = gwu.get_pname_from_value_code(node)
                net.add_node(node,
                             label=p_name,
                             title=f"{p_name}: {p_value_name}",
                             color="#ffa552")

            # -- edges: only if both ends are in visible_nodes -------
            for u in visible_nodes:
                for v, attrs in st.session_state["G"][u].items():
                    if v in visible_nodes and attrs["weight"] >= CP_MIN:
                        net.add_edge(
                            u, v,
                            title=f"P={attrs['weight']:.2f}",
                            physics=True,
                            width=1,  # fixed line thickness (px)
                            color={"color": "#dddddd",  # dict form lets you customise
                                   "highlight": "#333333",  #   normal / on‑select / on‑hover
                                   "hover": "#555555"}

                        )

            # --------------------------------------------------------
            # 3.  Render
            # --------------------------------------------------------
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            net.write_html(tmp.name)
            components.html(open(tmp.name, "r", encoding="utf-8").read(),
                            height=650, scrolling=True)

# PREPARING AND RUNNING GENERAL AGENT ==================================================================
if st.session_state["preprocessing_done"] and st.button("Guess grammar rules"):
    st.session_state["run_ga"] = True
if (st.session_state["preprocessing_done"]
        and st.session_state["run_ga"]
        and not st.session_state["ga_output_available"]):
    side_info.write("Creating agent")
    st.session_state["belief_history"] = {}
    st.session_state["consensus_store"] = {}
    st.session_state["ga_output_available"] = False
    st.session_state["generate_description"] = False
    st.session_state["results_approved"] = False
    st.session_state["ga_param_names"] = [
        p
        for topic in st.session_state["selected_parameters_by_topic"].keys()
        for p in st.session_state["selected_parameters_by_topic"][topic]
    ]
    st.write("Running General Agent with {} parameters.".format(len(st.session_state["ga_param_names"])))

    st.session_state["prompt_content"] = {}

    for topic in st.session_state["selected_topics"]:
        st.session_state["prompt_content"][topic] = {pname: {"main value": None, "examples by value": {}}
                                                     for pname in st.session_state["selected_parameters_by_topic"][topic]}

    st.session_state["run_ga"] = True

    if st.session_state["run_ga"]:
        side_info.write("Running inferences")
        st.session_state["ga"] = general_agents.GeneralAgent("ga",
                                                             parameter_names=st.session_state["ga_param_names"],
                                                             language_stat_filter=st.session_state["l_filter"])

        st.session_state["belief_history"] = {param: [st.session_state["ga"].language_parameters[param].beliefs] for
                                              param in st.session_state["ga"].language_parameters.keys()}

        # OBSERVATIONS
        for observed_param_name in st.session_state["tl_knowledge"]["observed"]:
            st.session_state["ga"].add_observations(observed_param_name,
                                                    st.session_state["tl_knowledge"]["observed"][observed_param_name])
        st.session_state["ga"].run_belief_update_from_observations()
        # adjust the weight of observed parameters according to their certainty
        for observed_param_name in st.session_state["tl_knowledge"]["observed"]:
            try:
                st.session_state["ga"].language_parameters[observed_param_name].update_entropy()
                st.session_state["ga"].language_parameters[observed_param_name].update_weight_from_observations()
            except KeyError:
                print("updating weight: {} not in {}".format(observed_param_name,
                                                             st.session_state["ga"].language_parameters.keys()))

        for param in st.session_state["belief_history"].keys():
            st.session_state["belief_history"][param].append(st.session_state["ga"].language_parameters[param].beliefs)

        # TRUTH INJECTION
        # Injecting beliefs of known parameters from wals/grambank
        for known_p_name in st.session_state["tl_knowledge"]["known_wals_pk"].keys():
            depk = st.session_state["tl_knowledge"]["known_wals_pk"][known_p_name]
            if known_p_name in st.session_state["ga"].language_parameters.keys():
                st.session_state["ga"].language_parameters[known_p_name].inject_peak_belief(depk, 1, locked=True)
        for known_p_name in st.session_state["tl_knowledge"]["known_grambank_pid"].keys():
            vid = st.session_state["tl_knowledge"]["known_grambank_pid"][known_p_name]
            if known_p_name in st.session_state["ga"].language_parameters.keys():
                st.session_state["ga"].language_parameters[known_p_name].inject_peak_belief(vid, 1, locked=True)

        # BELIEF PROPAGATION
        side_info.write("Belief propagation")
        beliefs_snapshot = st.session_state["ga"].get_beliefs()
        for k in range(NUMBER_OF_MESSAGING_CYCLES):
            st.session_state["belief_history"] = {param_name: [] for param_name in
                                                  st.session_state["ga"].language_parameters.keys()}
            st.session_state["ga"].reset_beliefs_history()
            st.session_state["ga"].put_beliefs(beliefs_snapshot)
            #st.write(st.session_state["ga"].get_displayable_beliefs())
            for i in range(3):
                st.session_state["ga"].run_belief_update_cycle()
                for param in st.session_state["ga"].language_parameters.keys():
                    st.session_state["belief_history"][param].append(
                        st.session_state["ga"].language_parameters[param].beliefs)
                # st.write("----------------**Messaging Iteration {}**---------------------".format(i))
                # st.write(st.session_state["ga"].get_displayable_beliefs())
            st.session_state["consensus_store"][k] = st.session_state["ga"].get_beliefs()

        cross_consensus_stat = {param: {gwu.get_pvalue_name_from_value_code(pvalue): [] for pvalue in
                                        st.session_state["consensus_store"][0][param].keys()}
                                for param in st.session_state["consensus_store"][0].keys()}

        for i, result in st.session_state["consensus_store"].items():
            for param, pvalues in result.items():
                for pvalue, proba in pvalues.items():
                    cross_consensus_stat[param][gwu.get_pvalue_name_from_value_code(pvalue)].append(proba)

        st.session_state["run_ga"] = False
        st.session_state["ga_output_available"] = True
        side_info.write("Inferences computed")

# Details
if show_details and st.session_state["ga_output_available"]:

    st.write("Agent created with {} parameters, {} known, {} observed.".format(
        len(st.session_state["ga"].language_parameters),
        len(st.session_state["tl_knowledge"]["known_wals"]) + len(
            st.session_state["tl_knowledge"]["known_grambank"]),
        len(st.session_state["tl_knowledge"]["observed"])))

    st.write("**beliefs evolution**")
    for param in st.session_state["belief_history"].keys():
        if param in st.session_state["tl_knowledge"]["known_wals"]:
            origin = "Known"
        elif param in st.session_state["tl_knowledge"]["known_grambank"]:
            origin = "Known"
        elif param in st.session_state["tl_knowledge"]["observed"]:
            origin = "Observed"
        else:
            origin = "Inferred"
        if st.session_state["ga"].language_parameters[param].locked:
            l = " is locked"
        else:
            l = ""
        rounded_weight = round(st.session_state["ga"].language_parameters[param].weight, 2)
        st.write(param + "(" + origin + ")" + l)
        st.write("{} ({}, {}). Normalized entropy = {}%. Weight = {}".format(param, origin, l,
                                                                             round(100 * st.session_state[
                                                                                 "ga"].language_parameters[
                                                                                 param].entropy, 2),
                                                                             rounded_weight))
        pdf = pd.DataFrame(st.session_state["belief_history"][param]).T
        renaming_dict = {}
        for v in st.session_state["belief_history"][param][0].keys():
            renaming_dict[v] = gwu.get_pvalue_name_from_value_code(v)
        pdf = pdf.rename(index=renaming_dict)
        st.dataframe(pdf)

    show_ga = st.toggle("Show General Agent graph")
    if show_ga:
        # GRAPH with pyvis
        def plot_ga_pyvis(ga):
            net = Network(height='800px', width='100%', directed=True)
            net.barnes_hut()
            # Add nodes with belief values
            for param_name in ga.graph.keys():
                if param_name in st.session_state["tl_knowledge"]["known_wals"]:
                    col = "blue"
                    s = 30
                    prefix = "KNOWN (WALS)"
                elif param_name in st.session_state["tl_knowledge"]["known_grambank"]:
                    col = "pink"
                    s = 30
                    prefix = "KNOWN (Grambank)"
                elif param_name in st.session_state["tl_knowledge"]["observed"]:
                    col = "yellow"
                    s = 20
                    prefix = "OBSERVED"
                else:
                    col = "grey"
                    s = 10
                    prefix = "Inferred"

                node_title = prefix + "\n" + param_name

                net.add_node(
                    n_id=param_name,
                    label=prefix,
                    title=node_title,
                    size=s,
                    color=col
                )
            # Add edges with probabilities
            for from_node in ga.graph.keys():
                for to_node in ga.graph[from_node].keys():
                    max_cp = ga.graph[from_node][to_node].max().max()
                    max_row, max_col = ga.graph[from_node][to_node].stack().idxmax()
                    max_row_name = gwu.get_pvalue_name_from_value_code(max_row)
                    max_col_name = gwu.get_pvalue_name_from_value_code(max_col)
                    try:
                        net.add_edge(
                            source=from_node,
                            to=to_node,
                            value=ga.graph[from_node][to_node].max().max(),
                            title=from_node + "-->" + to_node + "\nCP table:\n" + str(ga.graph[from_node][to_node]),
                            label=ga.graph[from_node][to_node].max().max(),
                            color="#eeeeee",
                            arrows="",
                            physics=True
                        )
                    except:
                        print("no node")

            # Customize physics options for better layout
            net.set_options("""
                            var options = {
                              "nodes": {
                                "font": {
                                  "size": 16
                                }
                              },
                              "edges": {
                                "color": {
                                  "inherit": true
                                },
                                "smooth": true
                              },
                              "physics": {
                                "enabled": true,
                                "stabilization": {
                                "enabled": true,
                                "iterations": 100,
                                "updateInterval": 25
                                },
                                "barnesHut": {
                                  "gravitationalConstant": -8000,
                                  "centralGravity": 0.9,
                                  "springLength": 500,
                                  "springConstant": 0.05,
                                  "damping": 0.5,
                                  "avoidOverlap": 1
                                },
                                "minVelocity": 0.75
                              }
                            }
                            """)
            # Generate HTML representation of the graph
            return net.generate_html()


        # Generate the PyVis graph HTML
        html_str = plot_ga_pyvis(st.session_state["ga"])

        # Display the PyVis graph in Streamlit
        st.components.v1.html(html_str, height=800, width=1000)
        # st.write(st.session_state["ga"].graph)

# EDITABLE RESULTS ================================================================

if st.session_state["ga_output_available"]:
    side_info.write("Results edition")
    st.markdown("#### Beliefs")
    edit_beliefs = st.toggle("Let me edit beliefs")
    if not edit_beliefs:
        if st.session_state["ga_output_available"]:
            st.markdown("""Based on statistical information, existing knowledge, observations and inferences across parameters, the following beliefs formed a consensus.
            """)
            result_list = []
            for pname, P in st.session_state["ga"].language_parameters.items():
                if pname in st.session_state["tl_knowledge"]["known_wals"]:
                    origin = "Known"
                elif pname in st.session_state["tl_knowledge"]["known_grambank"]:
                    origin = "Known"
                elif pname in st.session_state["tl_knowledge"]["observed"]:
                    origin = "Observed"
                else:
                    origin = "Inferred"
                if round(100 * (1 - P.entropy)) > 50:  # Only add beliefs if confidence > 50%
                    result_list.append({"Parameter": pname,
                                        "Origin": origin,
                                        "Winner": P.get_winning_belief_name(),
                                        "Confidence": round(100 * (1 - P.entropy))})
            result_df = pd.DataFrame(result_list)
            result_df = result_df.sort_values(by="Confidence", ascending=False)
            st.dataframe(result_df, use_container_width=True)

            #st.markdown("{} ({}): **{}** with {}% confidence.".format(pname, origin, P.get_winning_belief_name(), round(100*(1-P.entropy))))
        if st.button("Approve beliefs"):
            st.session_state["results_approved"] = True
    else:
        if st.session_state["ga_output_available"]:
            st.markdown("#### Editable Beliefs")
            st.markdown("""Based on statistical information, existing knowledge, observations and inferences across parameters, the following beliefs formed a consensus.
                   You can correct those you disagree with by selecting your preferred value.""")

            for pname, P in st.session_state["ga"].language_parameters.items():
                if pname in st.session_state["tl_knowledge"]["known_wals"]:
                    origin = "Known"
                elif pname in st.session_state["tl_knowledge"]["known_grambank"]:
                    origin = "Known"
                elif pname in st.session_state["tl_knowledge"]["observed"]:
                    origin = "Observed"
                else:
                    origin = "Inferred"

                vcode_by_vname = {gwu.get_pvalue_name_from_value_code(vcode): vcode for vcode in P.beliefs.keys()}
                vname_by_vcode = {vcode: gwu.get_pvalue_name_from_value_code(vcode) for vcode in P.beliefs.keys()}
                wining_belief_vcode = P.get_winning_belief_code()
                wining_belief_vname = P.get_winning_belief_name()

                selected_winning_vname = st.selectbox("{} ({})".format(pname, origin),
                                                      vcode_by_vname.keys(),
                                                      index=list(vcode_by_vname.keys()).index(wining_belief_vname),
                                                      key=pname)
                if selected_winning_vname != wining_belief_vname:
                    st.session_state["ga"].language_parameters[pname].inject_peak_belief(
                        vcode_by_vname[selected_winning_vname], 1, locked=True)
                    st.warning("Belief manually edited: {}:{}".format(pname, selected_winning_vname))

            if st.button("Approve beliefs"):
                # flag result approved
                st.session_state["results_approved"] = True

# GRAMMATICAL DESCRIPTION CONTENT
if st.session_state["ga_output_available"] and st.session_state["results_approved"]:

    beliefs = st.session_state["ga"].get_beliefs()
    for topic in st.session_state["prompt_content"]:
        for pname in st.session_state["prompt_content"][topic].keys():
            if pname in beliefs.keys():
                # main value
                max_vcode = max(beliefs[pname], key=beliefs[pname].get)
                max_vname = gwu.get_pvalue_name_from_value_code(max_vcode)
                st.session_state["prompt_content"][topic][pname]["main value"] = max_vname
                #obs
                if pname in st.session_state["obs"].keys():
                    examples = {}
                    for vname, details in st.session_state["obs"][pname]["observations"].items():
                        if details["count"] != 0:
                            if vname not in st.session_state["prompt_content"][topic][pname][
                                "examples by value"].keys():
                                st.session_state["prompt_content"][topic][pname]["examples by value"][vname] = []
                            for occurrence_index, context in details["details"].items():
                                gdf = kgu.build_super_gloss_df(st.session_state["kg"],
                                                               occurrence_index,
                                                               st.session_state["delimiters"])
                                st.session_state["prompt_content"][topic][pname]["examples by value"][vname].append({
                                    "english sentence":
                                        st.session_state["kg"][occurrence_index][
                                            "sentence_data"]["text"],
                                    "translation": st.session_state["kg"][occurrence_index][
                                        "recording_data"][
                                        "translation"],
                                    "gloss": gdf.to_dict(),
                                    "context": context
                                })
    st.markdown("#### Download raw grammatical description with examples.")
    colqw, colqe = st.columns(2)
    colqw.download_button("📥 As JSON",
                       json.dumps(st.session_state["prompt_content"], indent=4),
                       file_name="grammatical_description_of_{}.json".format(st.session_state["tl_name"]))
    with open("./data/current_gram.json", "w") as f:
        json.dump(st.session_state["prompt_content"], f, indent=4)
    st.session_state["generate_description"] = True
    #st.write(st.session_state["prompt_content"])
    docx_file = ogu.generate_docx_from_grammar_json(st.session_state["prompt_content"], st.session_state["tl_name"])
    if docx_file:
        colqe.download_button(
            label="📥 As DOCX",
            data=docx_file,
            file_name=f'{st.session_state["tl_name"]}_grammar_elements.docx',
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.write("Generation of docx file failed.")

# HYBRID LLM GRAMMATICAL DESCRIPTION ====================================================================

if st.session_state["ga_output_available"] and st.session_state["results_approved"] and st.session_state[
    "generate_description"]:

    st.markdown("#### Use a LLM to customize grammatical descriptions.")

    # USER INPUT
    prompt_override = st.text_input(
        "Ask a specific question about the language or leave blank for default topics.")
    content_type = st.selectbox("What kind of document do you want?", ["grammar lesson", "grammatical description"])
    audience_language = st.selectbox("What is L1?", ["English", "French", "Japanese", "Mandarin Chinese", "German"])
    if audience_language != st.session_state["audience_language"]:
        st.session_state["audience_language"] = audience_language
    audience = st.selectbox("For which audience?", ["high-school beginners", "adult beginners", "linguists"])
    if audience != st.session_state["audience"]:
        st.session_state["audience"] = audience

    # build prompt data
    # create final result_list
    result_list = []
    for pname, P in st.session_state["ga"].language_parameters.items():
        if pname in st.session_state["tl_knowledge"]["known_wals"]:
            origin = "Known"
        elif pname in st.session_state["tl_knowledge"]["known_grambank"]:
            origin = "Known"
        elif pname in st.session_state["tl_knowledge"]["observed"]:
            origin = "Observed"
        else:
            origin = "Inferred"
        examples_by_value = {}
        for domain in st.session_state["prompt_content"]:
            for param in st.session_state["prompt_content"][domain].keys():
                if param == pname:
                    examples_by_value = st.session_state["prompt_content"][domain][param]["examples by value"]
        if (1 - P.entropy) > 0.7:
            result_list.append({"Parameter": pname,
                                "Origin": origin,
                                "Winner": P.get_winning_belief_name(),
                                "Confidence": round(100 * (1 - P.entropy)),
                                "Examples by value": examples_by_value})
    # build sentence_data_list
    sentence_data_list = kgu.build_alterlingua_list_from_kg(st.session_state["kg"],
                                                            st.session_state["delimiters"])
    json_blob = {
        "sentences": sentence_data_list,  # lower-case, no spaces
        "grammar_priors": result_list
    }

    # st.write("Data packaged for LLM")
    # st.write(json_blob)



    DEFAULT_PROMPT = """
    SYSTEM
    You are "DIG4EL", a generator of {{content_description}} for the {{language_name}} language for {{audience}}.
    {{audience}} speak {{audience_language}}. 
    • Explanations compare {{audience_language}} and {{language_name}} to help {{audience}} learn the grammar. 
    • Explanations are optimized to the read and understood by {{audience}}.
    • Treat the JSON object you receive as ground truth; never invent extra facts.
    • Use ONLY information present in the JSON; never hallucinate extra facts.
    • Do not invent examples, fact or gloss about the target language: Use examples from the JSON.
    • Combine grammar_priors and sentences to infer grammatical rules.
    • Use also the alterlingua in the provided JSON to understand the grammar of the language, but remember it is not the target language. The target language is the value of the 'target_raw' key. 
    • Also use comments to infer grammatical rules and to illustrate examples.
    • Output must match the EXACT JSON schema shown below – no comments, no extra keys, no trailing commas.
    • Preserve target language orthography and punctuation.
    • Gloss must be the alterlingua version as presented in the data, unchanged.

    FOCUS AREAS (fixed order)
      1. Assertion, Question, Injunction: How to determine if a sentence is an assertion, a question or an order?
      2. Existence, Categorization, Qualification: How do you say that something is, that this something belongs to a category, and that this something displays some qualities?
      3. Agent and Patient in a simple sentence: How to determine what is the agent and what is the patient in a simple sentence?
      4. References to people and things: How to recognize and use references to people and things?
      5. Negation: How to say that something is not or that an action does not occur?

    The content of explanations you provide must answer the questions associated with each focus area. 

    STRICT-JSON-SCHEMA  (copy exactly):
    {
      "chapters": [
        {
          "title": "Assertion, Question, Injunction",
          "subtitle": "How to determine if a sentence is an assertion, a question or an order?",
          "explanation": "",
          "examples": [
            { "english": "", 
            "target": "", 
            "gloss": "" 
            }
          ]
        },
        {
          "title": "Existence, Categorization, Qualification",
          "subtitle": "How do you say that something is, that this something belongs to a category, and that this something displays some qualities?",
          "explanation": "",
          "examples": [
            { "english": "", 
            "target": "", 
            "gloss": "" }
          ]
        },
        {
          "title": "Agent and Patient in a simple sentence",
          "subtitle": "How to determine what is the agent and what is the patient in a simple sentence?",
          "explanation": "",
          "examples": [
            { "english": "", 
            "target": "", 
            "gloss": "" 
            }
          ]
        },
        {
          "title": "References to people and things",
          "subtitles": "How to recognize and use references to people and things?",
          "explanation": "",
          "examples": [
            { "english": "", 
            "target": "", 
            "gloss": "" }
          ]
        },
        {
          "title": "Negation",
          "subtitle": "How to say that something is not or that an action does not occur?",
          "explanation": "",
          "examples": [
            { "english": "", 
            "target": "", 
            "gloss": "" }
          ]
        }
      ]
    }

    ALLOWED TOOL (optional)
    Use ⟨define morpheme="-y": "1SG.POSS"⟩ inline inside an *explanation* if needed.

    TASKS
    1. Parse all `sentences[*]` and `grammar_priors`.
    2. For each focus area, pick up to three sentences that illustrate it best.
    3. Fill the JSON template:
       – `explanation` for each chapter. Explanation must answer the question in the subtitle. (≤250 words).  
       - Explanations should compare {{audience_language}} and {{language_name}}, insisting on contrasts. 
       - Explanations should be adapted to {{audience}}. 
       – Populate `examples` with the chosen sentences (preserve order).
       - Gloss should be exactly the alterlingua gloss from the data.
    4. If no example fits a chapter, leave its `examples` array empty and set `explanation` to "No examples available yet".
    5. Output **only** the JSON object that conforms to STRICT-JSON-SCHEMA. Do not wrap it in Markdown fences or add any prose.

    END OF PROMPT

    """

    DEFAULT_SPECIFIC_QUESTION_PROMPT = """
    SYSTEM
     You are "DIG4EL", a generator of {{content_description}} of the {{language_name}} language for {{audience}}.
    {{audience}} speak {{audience_language}}. 
    - Your objective is to answer the user's question about the language. 
    - Your answers compare {{audience_language}} and {{language_name}} to help {{audience}} learn the grammar. 
    - Your answers are optimized to be read and understood by {{audience}}.
    
    To do so, the user gives you data: a JSON with all the information you need:
    - grammar_priors: A List of grammatical parameters and their value in the language at hand.
    - sentences: for each sentence, a dictionary shows:
      - english sentence ('source_english'),
      - the target language sentence ('target_raw'),
      - an explanatory gloss ('alterlingua'),
      - optional comments ('comment').
    
    IMPORTANT CLARIFICATIONS:
    • The target language grammar is only represented by 'target_raw': 'alterlingua' is an explanatory/teaching gloss; it may contain hints or expansions not actually present in the target language. 
    • Treat the JSON object you receive as ground truth; do not invent extra facts.
    • Do not invent examples, facts, or gloss about the target language. Use only examples from the JSON data.
    • Combine grammar_priors and 'target_raw' from the sentences to infer grammatical rules. The 'alterlingua' is only for the final gloss in your output.
    • Output must match the EXACT JSON schema shown below – no comments, no extra keys, no trailing commas.
    • Preserve target language orthography and punctuation exactly as given in 'target_raw'.
    • The gloss must be the 'alterlingua' version exactly as presented in the data, with no changes.
    
    FOCUS: {{user_question}}
    
    STRICT-JSON-SCHEMA  (copy exactly):
    {
      "chapters": [
        {
          "title": {{user_question}},
          "subtitle": "",
          "explanation": "",
          "examples": [
            { "english": "", 
              "target": "", 
              "gloss": "" 
            }
          ]
        }
      ]
    }
    
    TASKS
    1. Parse all `sentences[*]` and `grammar_priors`.
    2. Pick up all sentences that illustrate the answer to the user's question.
    3. Infer grammatical rules from the 'target_raw' field (plus grammar_priors), ignoring morphological or syntactic markers in 'alterlingua'.
    4. Fill the JSON template:
       – `explanation` must answer the user's question (thoroughly). Explanation should compare {{audience_language}} 
       and {{language_name}}, insisting on contrasts. Explanations should be adapted to {{audience}}. 
       – `examples` should contain the relevant sentences that illustrate your explanation.
           * “english” must be the value from 'source_english'.
           * “target” must be the value from 'target_raw'.
           * “gloss” must be the value from 'alterlingua'.
       – If no examples fit, leave the `examples` array empty and set `explanation` to "No examples available".
    5. Output **only** the JSON object conforming to STRICT-JSON-SCHEMA. Do not add any extra text or formatting beyond that JSON.
    
    END OF PROMPT
    
    """

    if prompt_override == "":
        system_prompt = DEFAULT_PROMPT
        system_prompt = system_prompt.replace("{{content_description}}", st.session_state["content_description"])
        system_prompt = system_prompt.replace("{{language_name}}", st.session_state["tl_name"])
        system_prompt = system_prompt.replace("{{audience_language}}", st.session_state["audience_language"])
        system_prompt = system_prompt.replace("{{audience}}", st.session_state["audience"])
        print("Prompt before inserting data ==============")
        print("SYSTEM")
        print(system_prompt)
        print("USER")
        user_payload = f"""Answer the questions about the grammar of the {st.session_state['tl_name']} language, 
        to {audience} speaking {st.session_state['audience_language']}. 
        Here's the {st.session_state['tl_name']} data: 
        
        """
        print("User payload")
        print(user_payload)
    else:
        system_prompt = DEFAULT_SPECIFIC_QUESTION_PROMPT
        system_prompt = system_prompt.replace("{{content_description}}", st.session_state["content_description"])
        system_prompt = system_prompt.replace("{{language_name}}", st.session_state["tl_name"])
        system_prompt = system_prompt.replace("{{audience_language}}", st.session_state["audience_language"])
        system_prompt = system_prompt.replace("{{audience}}", st.session_state["audience"])
        system_prompt = system_prompt.replace("{{user_question}}", prompt_override)
        print("Prompt before inserting data ================================================")
        print("SYSTEM")
        print(system_prompt)
        print("USER")
        user_payload = f"""Answer the question '{prompt_override}' about the grammar of the {st.session_state['tl_name']} language, 
                to {audience} speaking {st.session_state['audience_language']}. 
                Here's the {st.session_state['tl_name']} data: 

                """
        print("User payload")
        print(user_payload)

    user_payload += json.dumps(json_blob, ensure_ascii=False)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_payload}
    ]

    print("TOKENS ================================================")
    # Choose your model's encoding; for GPT-4, GPT-3.5-turbo, etc.
    encoding = tiktoken.encoding_for_model("gpt-4")  # or "gpt-3.5-turbo", etc.

    input_text = system_prompt + user_payload
    num_tokens = len(encoding.encode(input_text))

    print(f"Number of tokens: {num_tokens}")

    st.markdown("#### Make sure everything below is correct and press 'Generate'")
    st.markdown("⚠️ Be aware: The data will be sent to a remote LLM for processing ⚠️")
    table = {"Focus": "",
             "Content": "",
             "L1": "",
             "Audience": ""
             }
    if prompt_override:
        table["Focus"] = prompt_override
    else:
        table["Focus"] = "Default"
    table["Content"] = st.session_state['content_description']
    table["L1"] = st.session_state['audience_language']
    table["Audience"] = st.session_state['audience']
    st.table(table)
    use_openai = st.button(f"Generate")
    request_info = st.empty()
    if use_openai:
        request_info.write("Sending generation request... {} tokens".format(num_tokens))
        api_key = os.getenv("OPEN_AI_KEY")
        if not api_key:
            st.error("No OpenAI key found – set OPEN_AI_KEY as an env var or add it to .streamlit/secrets.toml")

        if api_key:
            openai.api_key = api_key
            side_info.write("Waiting for LLM output...")

            st.session_state["response"] = openai.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                temperature=0.3,
                max_tokens=5000
            ).choices[0].message.content

            request_info.write("Response received")
            print("Response received")
            print("Loading as json")
            jsload_success = False

            # if the json returned is not well-formed, we send it back to GPT3.5 for cleaning.
            try:
                st.session_state["output"] = decode(st.session_state["response"])
                jsload_success = True
                request_info.success("Valid response received")
            except json.decoder.JSONDecodeError:
                st.write("Issue decoding json, sending back for a fix")
                print("Raw Response")
                print(st.session_state["response"])
                fixed_response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "SYSTEM: The previous response was not valid JSON. "
                                                            "Return exactly the same content but formatted as valid JSON. "
                                                            "Do not add any extra keys, comments, or prose."},
                              {"role": "user", "content": st.session_state["response"]}],
                    temperature=0.0,
                    max_tokens=5000
                ).choices[0].message.content
                try:
                    fixed_output = decode(fixed_response)
                    jsload_success = True
                    st.session_state["output"] = fixed_output
                    # st.write(fixed_output)
                except json.decoder.JSONDecodeError:
                    print(fixed_response)
                    request_info.write("Failed to generate a well-formed response, see terminal for raw response.")

            else:
                request_info.write("Unable to use the OpenAI API key, please contact support.")

    col41, col42, col43 = st.columns(3)
    if st.session_state["output"] != {}:
        st.session_state["initial_llm_request_done"] = True
        side_info.write("Formatted content received")
        request_info.write("Intermediate output available")

        col41.download_button("Download JSON with gloss tables",
                           json.dumps(st.session_state["output"], indent=4),
                           file_name="hybrid_grammatical_description_of_{}.json".format(
                               st.session_state["tl_name"]), key="inter_json")
        if col42.button("Generate docx with gloss tables", key="generate_inter_docx"):
            st.session_state["docx_file"] = ogu.generate_docx_from_hybrid_output(st.session_state["output"],
                                                             st.session_state["tl_name"],
                                                             gloss_format="table")
            st.session_state["docx_file_ready"] = True

    if st.session_state["docx_file_ready"]:
        col43.download_button(
            label="📥 Download intermediate DOCX",
            data=st.session_state["docx_file"],
            file_name=f'export_hybrid_grammar_of_{st.session_state["tl_name"]}_detailed_tables.docx',
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="inter_docx"
        )

    # POLISHING
    if st.session_state["output"] != {} and not st.session_state["polishing_done"]:
        request_info.write("Polishing output...")
        side_info.write("Waiting for content polishing...")
        print("POLISHING ========================================================================")
        final_system_prompt = f'''
                SYSTEM
                    You are a language-learning assistant adapting a grammar lesson provided by the user in a JSON format by turning the gloss provided in examples 
                    into a plain language presentation of the sentence, focusing on the title and the explanation. 
                    - The title is in 'title', the explanation in 'explanation', and the examples in 'examples'.
                    - Each example shows the English sentence, the target sentence in the target language, and the gloss. 
                    - The gloss is made of each target language word, followed by information about the word, delimited with <>. 
                        This information always start with the meaning of the word, then between parenthesis information about its
                        Internal Particularization (IP) as tense or number, then Relational Particularization (RP) 
                        as the semantic role. 
                NOTE: Do no invent anything about the target language. Use only the information provided in the user JSON.
                OBJECTIVE:
                    - Return the same JSON with updated gloss for each example. 
                    - The updated gloss should be a plain-language string, easy to read by the {st.session_state['audience_language']}-speaking 
                        {st.session_state['audience']}, helping to understand the explanation given. 
                FORMAT: 
                    - Your output should be a valid JSON with the exact same format as the input. 

                '''
        # TOKEN COUNT
        encoding = tiktoken.encoding_for_model("gpt-4")  # or "gpt-3.5-turbo", etc.

        final_input_text = final_system_prompt + st.session_state["response"]
        num_tokens = len(encoding.encode(final_input_text))
        print("Polishing request: {} tokens".format(num_tokens))


        final_response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "system", "content": final_system_prompt},
                      {"role": "user", "content": st.session_state["response"]}],
            temperature=0.3,
            max_tokens=5000
        ).choices[0].message.content

        try:
            st.session_state["final_output"] = decode(final_response)
            print("POLISHING RESPONSE: ")
            print(final_response)
            print("POLISHING OUTPUT: ")
            print(st.session_state["final_output"])
        except json.decoder.JSONDecodeError:
            print("Error decoding final JSON")
            print(final_response)

        st.session_state["polishing_done"] = True

    if st.session_state["final_output"] != {}:
        side_info.write("Final content received")
        col51, col52, col53 = st.columns(3)
        request_info.success("Done.")
        col51.download_button("Download final JSON",
                              json.dumps(st.session_state["final_output"], indent=4),
                              file_name="{}_grammar_plain.json".format(
                                  st.session_state["tl_name"]), key="final_json")

        if col52.button("Generate final docx"):
            st.session_state["docx_file_plain"] = ogu.generate_plain_language_docx_from_hybrid_output(st.session_state["final_output"],
                                                                   st.session_state["tl_name"])
            st.session_state["polished_docx_file_ready"] = True

        if st.session_state["polished_docx_file_ready"]:
            col53.download_button(
                label="📥 Download final DOCX",
                data=st.session_state["docx_file_plain"],
                file_name=f'{st.session_state["tl_name"]}_grammar_plain.docx',
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="final_docx"
            )


