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
import pandas as pd
from libs import utils as u, wals_utils as wu, general_agents, grambank_utils as gu
from libs import grambank_wals_utils as gwu
from libs import knowledge_graph_utils as kgu
from libs import cq_observers as obs
from libs import general_agents
import json
import openai
from pyvis.network import Network
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots

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
    st.session_state["selected_topics"] = []
if "loaded_existing" not in st.session_state:
    st.session_state["loaded_existing"] = ""
if "cq_transcriptions" not in st.session_state:
    st.session_state["cq_transcriptions"] = []
if "consolidated_transcriptions" not in st.session_state:
    st.session_state["consolidated_transcriptions"] = {}
if "tl_knowledge" not in st.session_state:
    st.session_state["tl_knowledge"] = {
        "known_wals":{},
        "known_wals_pk":{},
        "known_grambank":{},
        "known_grambank_pid":{},
        "observed":{},
        "inferred":{}
    }
if "ga" not in st.session_state:
    st.session_state["ga"] = None
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

topics2 = {
"ga_topics": {
    "Canonical word orders": {
  "Order of Subject, Object and Verb": {"code": "81", "observer": (obs.observer_order_of_subject_object_verb, True)},
  "Order of Subject and Verb": {"code": "82", "observer": (obs.observer_order_of_subject_and_verb, True)}}
},
"ca_topics":{}
}

topics = {
"ga_topics": {
    "Existential word?": {
    "Is there an existential verb?": {"code":"GB126", "observer": None}
    },
    "Canonical word orders": {
  "Order of Subject, Object and Verb": {"code": "81", "observer": (obs.observer_order_of_subject_object_verb, True)},
  "Order of Subject and Verb": {"code": "82", "observer": (obs.observer_order_of_subject_and_verb, True)},
  "Order of Object and Verb": {"code": "83", "observer": None},
  "Order of Adjective and Noun": {"code": "87", "observer": (obs.observer_order_of_adjective_and_noun, False)},
  "Order of Demonstrative and Noun": {"code": "88", "observer": (obs.observer_order_of_demonstrative_and_noun, False)},
  "Order of Relative Clause and Noun": {"code": "87", "observer": (obs.observer_order_of_relative_clause_and_noun, False)},
  "Order of Object, Oblique, and Verb": {"code": "84", "observer": None},
  "Order of Adposition and Noun Phrase": {"code": "85", "observer": None},
  "Order of Adverbial Subordinator and Clause": {"code": "94", "observer": None},
  "Order of Genitive and Noun": {"code": "86", "observer": None},
  "Order of Degree Word and Adjective": {"code": "91", "observer": None},
  "Order of Numeral and Noun": {"code": "89", "observer": None},
  "What is the order of numeral and noun in the NP?": {"code": "GB024", "observer": None},
  "What is the order of adnominal demonstrative and noun?": {"code": "GB025", "observer": None},
  "Is the order of core argument (i.e. S/A/P) constituents fixed?": {"code": "GB136", "observer": None},
  "What is the pragmatically unmarked order of S and V in intransitive clauses?": {"code": "GB130", "observer": None},
  "Is a pragmatically unmarked constituent order verb-initial for transitive clauses?": {"code": "GB131", "observer": None},
  "Is a pragmatically unmarked constituent order verb-medial for transitive clauses?": {"code": "GB132", "observer": None},
  "Is a pragmatically unmarked constituent order verb-final for transitive clauses?": {"code": "GB133", "observer": None},
  "Is the order of constituents the same in main and subordinate clauses?": {"code": "GB134", "observer": None},
  "What is the order of adnominal property word and noun?": {"code": "GB193", "observer": None},
  "What is the pragmatically unmarked order of adnominal possessor noun and possessed noun?": {"code": "GB065", "observer": None}
        },
    "Gender and noun class": {
      "Sex-based and Non-sex-based Gender Systems": {"code": "31", "observer": None},
      "Is there a gender/noun class system where sex is a factor in class assignment?": {"code": "GB051", "observer": None},
      "Number of Genders": {"code": "30", "observer": None},
      "Systems of Gender Assignment": {"code": "32", "observer": None},
      "Gender Distinctions in Independent Personal Pronouns": {"code": "44", "observer": None},
      "Is there a gender/noun class system where shape is a factor in class assignment?": {"code": "GB052", "observer": None},
      "Is there a gender/noun class system where animacy is a factor in class assignment?": {"code": "GB053", "observer": None},
      "Is there a gender/noun class system where plant status is a factor in class assignment?": {"code": "GB054", "observer": None},
      "Is there a gender system where a noun's phonological properties are a factor in class assignment?": {"code": "GB192", "observer": None},
      "Is there a large class of nouns whose gender/noun class is not phonologically or semantically predictable?": {"code": "GB321", "observer": None}
  },
    "Number": {
        "Is dual number regularly marked in the noun phrase by a dedicated phonologically free element?": {"code":"GB317", "observer": None},
        "Is singular number regularly marked in the noun phrase by a dedicated phonologically free element?" : {"code":"GB316", "observer": None},
        "Is trial number regularly marked in the noun phrase by a dedicated phonologically free element?": {"code": "GB319", "observer": None},
        "Is paucal number regularly marked in the noun phrase by a dedicated phonologically free element?": {"code": "GB320", "observer": None},
        "Is plural number regularly marked in the noun phrase by a dedicated phonologically free element?": {"code": "GB318", "observer": None},
    },
    "Cases": {
        "Number of Cases": {"code": "49", "observer": None},
        "Case Syncretism": {"code": "28", "observer": None},
        "Position of Case Affixes": {"code": "51", "observer": None},
        "Asymmetrical Case-Marking": {"code": "50", "observer": None},
        "Alignment of Case Marking of Pronouns": {"code": "99", "observer": None},
        "Alignment of Case Marking of Full Noun Phrases": {"code": "98", "observer": None},
        "Are there morphological cases for pronominal core arguments (i.e. S/A/P)?": {"code": "GB071", "observer": None},
        "Are there morphological cases for non-pronominal core arguments (i.e. S/A/P)?": {"code": "GB070", "observer": None},
        "Are there morphological cases for oblique non-pronominal NPs (i.e. not S/A/P)?": {"code": "GB072", "observer": None},
        "Are there morphological cases for independent oblique personal pronominal arguments (i.e. not S/A/P)?": {"code": "GB073", "observer": None},
    },
    "inclusive/exclusive": {
        "Is there a distinction between inclusive and exclusive?": {"code": "GB028", "observer": None},
        "Inclusive/Exclusive Distinction in Verbal Inflection": {"code": "40", "observer": None},
        "Inclusive/Exclusive Distinction in Independent Pronouns": {"code": "39", "observer": None}
    }
    },
    "ca_topics":{}
    }
number_of_belief_propagation_process = 1
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

default_delimiters = [ " ", ".",",",";",":","!","?","\u2026","'"]

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

st.title("Generate grammatical descriptions")
with st.popover("i"):
    st.write("This is an early prototype of inferential outputs, enabled for testing purposes. Outputs are meant to be reviewed by a speaker of the language.")
with st.expander("Inputs"):
    if st.button("reset"):
            st.session_state["tl_name"] = ""
            st.session_state["tl_wals_pk"] = ""
            st.session_state["tl_grambank_id"] = ""
            st.session_state["delimiters"] = []
            st.session_state["selected_topics"] = []
            st.session_state["loaded_existing"] = ""
            st.session_state["cq_transcriptions"] = []
            st.session_state["consolidated_transcriptions"] = {}
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
            st.rerun()

    # TOPICS AND LANGUAGE
    st.session_state["selected_topics"] = st.multiselect("Choose topics", list(topics["ga_topics"].keys()))
    for topic in st.session_state["selected_topics"]:
        st.session_state["prompt_content"][topic] = {pname: {"main value":None, "examples by value":{}} for pname in topics["ga_topics"][topic].keys()}
    ga_param_codes = [item["code"] for topic, topic_params in topics["ga_topics"].items() for item in topic_params.values() if
                                 item["code"] is not None and topic in st.session_state["selected_topics"]]
    ga_param_names = [gwu.get_pname_from_pcode(code) for code in ga_param_codes]
    ca_param_codes = [item["code"] for topic, topic_params in topics["ca_topics"].items() for item in topic_params.values() if
                                 item["code"] is not None and topic in st.session_state["selected_topics"]]
    ca_param_names = [gwu.get_pname_from_pcode(code) for code in ca_param_codes]

    # MANAGING CQ TRANSCRIPTIONS
    cqs = st.file_uploader("Load Conversational Questionnaires' transcriptions (all at once for multiple transcriptions)", type="json",
                           accept_multiple_files=True)
    if cqs is not None:
        st.session_state["cq_transcriptions"] = []
        for cq in cqs:
            new_cq = json.load(cq)
            st.session_state["cq_transcriptions"].append(new_cq)
        st.session_state["loaded_existing"] = True
        st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))

    # load transcriptions, create knowledge graph
    if st.session_state["loaded_existing"]:
        if st.session_state["cq_transcriptions"] != []:
            # Consolidating transcriptions
            st.session_state[
                "consolidated_transcriptions"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                st.session_state["cq_transcriptions"],
                st.session_state["tl_name"],
                st.session_state["delimiters"])
            st.write("{} Conversational Questionnaires: {} sentences, {} words with {} unique words".format(
                len(st.session_state["cq_transcriptions"]), len(st.session_state["consolidated_transcriptions"]),
                total_target_word_count, len(unique_words)))
            # managing language input
            st.session_state["tl_name"] = st.session_state["cq_transcriptions"][0]["target language"]
            # check data in wals
            st.session_state["tl_wals_pk"] = wu.language_pk_id_by_name.get(st.session_state["tl_name"], {}).get("pk", None)
            # check data in grambank
            if st.session_state["tl_name"] in [gu.grambank_language_by_lid[lid]["name"] for lid in gu.grambank_language_by_lid.keys()]:
                st.session_state["tl_grambank_id"] = next(lid for lid, value in gu.grambank_language_by_lid.items() if value["name"] == st.session_state["tl_name"])
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
                    print("Word separators are retrieved from the .")
            else:
                st.session_state["delimiters"] = default_delimiters
            st.multiselect("Edit word separators if needed", delimiters_bank, default=st.session_state["delimiters"])

    show_details = st.toggle("Show details")

# RETRIEVING KNOWLEDGE ==============================================================
if show_details:
    st.write("#### Known parameters in {}".format(st.session_state["tl_name"]))
    col8, col9 = st.columns(2)
if st.session_state["tl_name"] != "":
    # WALS
    if st.session_state["tl_wals_pk"] is not None:
        if st.session_state["tl_wals_pk"] in wu.domain_elements_by_language.keys():
            known_values =  wu.domain_elements_by_language[st.session_state["tl_wals_pk"]]
            for known_value in known_values:
                if wu.param_pk_by_de_pk[str(known_value)] in ga_param_codes + ca_param_codes:
                    p_name = wu.parameter_name_by_pk[wu.param_pk_by_de_pk[str(known_value)]]
                    de_name = wu.domain_element_by_pk[str(known_value)]["name"]
                    st.session_state["tl_knowledge"]["known_wals"][p_name] = de_name
                    st.session_state["tl_knowledge"]["known_wals_pk"][p_name] = str(known_value)
    if len(st.session_state["tl_knowledge"]["known_wals"]) != 0 and show_details:
        col8.write("**WALS**")
        col8.markdown("{} known relevant parameters in WALS".format(len(st.session_state[
                                                                        "tl_knowledge"][
                                                                        "known_wals"])))
        show_params = col8.toggle("Show known WALS parameters")
        if show_params:
            col8.write(st.session_state["tl_knowledge"]["known_wals"])
    elif len(st.session_state["tl_knowledge"]["known_wals"]) == 0 and show_details:
        col8.write("No known parameter in WALS")

    # GRAMBANK
    if st.session_state["tl_grambank_id"] is not None:
        ginfo = gu.get_grambank_language_data_by_id_or_name(st.session_state["tl_grambank_id"])
        known_pids =  ginfo.keys()
        for known_pid in known_pids:
            if known_pid in ga_param_codes + ca_param_codes:
                p_name = gu.grambank_pname_by_pid[known_pid]
                v_name = gu.grambank_vname_by_vid[ginfo[known_pid]["vid"]]
                st.session_state["tl_knowledge"]["known_grambank"][p_name] = v_name
                st.session_state["tl_knowledge"]["known_grambank_pid"][p_name] = ginfo[known_pid]["vid"]
    if len(st.session_state["tl_knowledge"]["known_grambank"]) != 0 and show_details:
        col9.write("**Grambank**")
        col9.markdown("{} known relevant parameters in Grambank".format(len(st.session_state[ "tl_knowledge"][
                                                                                            "known_grambank"])))
        show_params = col9.toggle("Show known Grambank parameters")
        if show_params:
            col9.write(st.session_state["tl_knowledge"]["known_grambank"])
    elif len(st.session_state["tl_knowledge"]["known_grambank"]) == 0 and show_details:
        col9.write("No known parameter in Grambank")
    st.session_state["known_processed"] = True
    #st.write(st.session_state["tl_knowledge"])

# PROCESSING TRANSCRIPTIONS

# OBSERVATIONS =================================================================

if st.session_state["consolidated_transcriptions"] != {}:
    # run observers
    for topic_name in st.session_state["selected_topics"]:
        if topic_name in topics["ga_topics"].keys():
            for param_name, param_info in topics["ga_topics"][topic_name].items():
                if param_info["observer"] is not None:
                    (func, canonical) = param_info["observer"]
                    st.session_state["obs"][param_name] = func(
                        st.session_state["consolidated_transcriptions"],
                        st.session_state["tl_name"],
                        st.session_state["delimiters"],
                        canonical=canonical
                    )
                    st.session_state["tl_knowledge"]["observed"][param_name] = st.session_state["obs"][param_name][
                        "agent-ready observation"]
        elif topic_name in topics["ca_topics"].keys():
            for param_name, param_info in topics["ga_topics"][topic_name].items():
                if param_info["observer"] is not None:
                    (func, canonical) = param_info["observer"]
                    st.session_state["obs"][param_name] = func(
                        st.session_state["consolidated_transcriptions"],
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

    if show_details:
        st.markdown("#### Retrieving **observed** information in Conversational Questionnaires")
        show_observed_details = st.toggle("Show details about observations")
        #st.write(st.session_state["obs"])
        if show_details and show_observed_details:
            for pobs in st.session_state["obs"]:
                if len(st.session_state["obs"][pobs]["observations"]) != 0:
                    st.markdown("#### {}".format(pobs))
                    for de_name, details in st.session_state["obs"][pobs]["observations"].items():
                        if details["count"] != 0:
                            st.write("---------------------------------------------")
                            st.write("**{}** in ".format(de_name))
                            for occurrence_index, context in details["details"].items():
                                st.markdown("- ***{}***".format(st.session_state["consolidated_transcriptions"][occurrence_index]["recording_data"]["translation"]))
                                st.write(st.session_state["consolidated_transcriptions"][occurrence_index]["sentence_data"]["text"])
                                gdf = kgu.build_gloss_df(st.session_state["consolidated_transcriptions"], occurrence_index, st.session_state["delimiters"])
                                st.dataframe(gdf)
                                st.write("context: {}".format(context))
                    st.markdown("-------------------------------------")

# STATISTICAL PRIORS =====================================================================

if st.session_state["known_processed"] and st.session_state["observations_processed"]:

    prior_family_list = []
    is_family_set = False
    # if no knowledge on this language, ask for alternatives to compute priors
    if st.session_state["tl_knowledge"]["known_wals"]=={} and st.session_state["tl_knowledge"]["known_grambank"]=={}:
        base_lname_list = list(set(list(wu.language_pk_id_by_name.keys()) + [linfo["name"] for lid, linfo in gu.grambank_language_by_lid.items()]))
        similar_lnames = st.multiselect("If you know languages that resemble {}, select one or several of them.".format(st.session_state["tl_name"]), base_lname_list)
        prior_family_list = list(set([gwu.get_language_family_by_language_name(lname) for lname in similar_lnames]))
    # otherwise use language family to compute priors
    else:
        prior_family_list = [gwu.get_language_family_by_language_name(st.session_state["tl_name"])]

    if show_details:
        if prior_family_list == []:
            display_family_list = "all"
        else:
            display_family_list = "the " + ", ".join(prior_family_list)
        st.write("Prior knowledge is based on statistics over **{}** language family(ies).".format(display_family_list))

    if prior_family_list != []:
        l_filter = {"family":prior_family_list}
    else:
        l_filter = {}

    # PREPARING AND RUNNING GENERAL AGENT
    st.markdown("#### Generating Grammar")
    if st.button("Launch inferential process"):
        st.session_state["run_ga"] = True
        st.session_state["belief_history"] = {}
        st.session_state["consensus_store"] = {}
        st.session_state["ga_output_available"] = False
        st.session_state["generate_description"] = False
        st.session_state["results_approved"] = False
    infospot = st.empty()
    if st.session_state["run_ga"]:
        st.session_state["ga"] = general_agents.GeneralAgent("ga",
                                                             parameter_names=ga_param_names,
                                                             language_stat_filter=l_filter)


        st.session_state["belief_history"] = {param: [st.session_state["ga"].language_parameters[param].beliefs] for param in st.session_state["ga"].language_parameters.keys()}

        if show_details:
            st.write("Agent created with {} parameters, {} known, {} observed.".format(len(st.session_state["ga"].language_parameters),
                                                                                           len(st.session_state["tl_knowledge"]["known_wals"])+len(st.session_state["tl_knowledge"]["known_grambank"]),
                                                                                           len(st.session_state["tl_knowledge"]["observed"])))
            st.write("Initial beliefs")
            st.write(st.session_state["ga"].get_displayable_beliefs())


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
                print("updating weight: {} not in {}".format(observed_param_name, st.session_state["ga"].language_parameters.keys()))

        for param in st.session_state["belief_history"].keys():
            st.session_state["belief_history"][param].append(st.session_state["ga"].language_parameters[param].beliefs)
        if show_details:
            infospot.write("Injecting observations")
            st.write("Beliefs after observations")
            st.write(st.session_state["ga"].get_displayable_beliefs())

        # TRUTH INJECTION
        # Injecting beliefs of known parameters from wqls/grambank
        for known_p_name in st.session_state["tl_knowledge"]["known_wals_pk"].keys():
            depk = st.session_state["tl_knowledge"]["known_wals_pk"][known_p_name]
            st.session_state["ga"].language_parameters[known_p_name].inject_peak_belief(depk, 1, locked=True)
        for known_p_name in st.session_state["tl_knowledge"]["known_grambank_pid"].keys():
            vid = st.session_state["tl_knowledge"]["known_grambank_pid"][known_p_name]
            st.session_state["ga"].language_parameters[known_p_name].inject_peak_belief(vid, 1, locked=True)

        if show_details:
            infospot.write("Injecting known information")
            st.write("Beliefs after injecting known information")
            st.write(st.session_state["ga"].get_displayable_beliefs())

        # BELIEF PROPAGATION
        if show_details:
            infospot.write("Running inferences...")
        beliefs_snapshot = st.session_state["ga"].get_beliefs()
        for k in range(number_of_belief_propagation_process):
            if show_details:
                infospot.write("Running General Agent #{}/{}".format(k+1, number_of_belief_propagation_process))
            st.session_state["belief_history"] = {param_name:[] for param_name in st.session_state["ga"].language_parameters.keys()}
            st.session_state["ga"].reset_beliefs_history()
            st.session_state["ga"].put_beliefs(beliefs_snapshot)
            #st.write(st.session_state["ga"].get_displayable_beliefs())
            for i in range(3):
                st.session_state["ga"].run_belief_update_cycle()
                for param in st.session_state["ga"].language_parameters.keys():
                    st.session_state["belief_history"][param].append(st.session_state["ga"].language_parameters[param].beliefs)
                # st.write("----------------**Messaging Iteration {}**---------------------".format(i))
                # st.write(st.session_state["ga"].get_displayable_beliefs())
            st.session_state["consensus_store"][k] = st.session_state["ga"].get_beliefs()


        cross_consensus_stat = {param: {gwu.get_pvalue_name_from_value_code(pvalue): [] for pvalue in st.session_state["consensus_store"][0][param].keys()}
                                for param in st.session_state["consensus_store"][0].keys()}

        for i, result in st.session_state["consensus_store"].items():
            for param, pvalues in result.items():
                for pvalue, proba in pvalues.items():
                    cross_consensus_stat[param][gwu.get_pvalue_name_from_value_code(pvalue)].append(proba)

        if show_details:
            infospot.write("All inferences computed")

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
                                                                         round(100*st.session_state["ga"].language_parameters[param].entropy, 2),
                                                                         rounded_weight))
                pdf = pd.DataFrame(st.session_state["belief_history"][param]).T
                renaming_dict = {}
                for v in st.session_state["belief_history"][param][0].keys():
                    renaming_dict[v] = gwu.get_pvalue_name_from_value_code(v)
                pdf = pdf.rename(index=renaming_dict)
                st.dataframe(pdf)
        st.session_state["run_ga"] = False
        st.session_state["ga_output_available"] = True
    # Details
    if show_details and st.session_state["ga_output_available"]:
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
                                title=from_node + "-->" + to_node + "\nMax CP value: " + str(ga.graph[from_node][
                                                                                                 to_node].max().max()) + " for " + max_row_name + " given " + max_col_name,
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
        # show_cross_consensus_stats = st.toggle("Show results across agents")
        # if show_cross_consensus_stats:
        #     st.markdown("#### Beliefs across {} seperate consensus search".format(number_of_belief_propagation_process))
        #     display_analysis(cross_consensus_stat)

# EDITABLE RESULTS ================================================================
if st.session_state["ga_output_available"]:
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
                result_list.append({"Parameter": pname,
                                    "Origin": origin,
                                    "Winner": P.get_winning_belief_name(),
                                    "Confidence": round(100*(1-P.entropy))})
            result_df = pd.DataFrame(result_list)
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

                vcode_by_vname = {gwu.get_pvalue_name_from_value_code(vcode):vcode for vcode in P.beliefs.keys()}
                vname_by_vcode = {vcode: gwu.get_pvalue_name_from_value_code(vcode) for vcode in P.beliefs.keys()}
                wining_belief_vcode = P.get_winning_belief_code()
                wining_belief_vname = P.get_winning_belief_name()

                selected_winning_vname = st.selectbox("{} ({})".format(pname, origin),
                                                      vcode_by_vname.keys(),
                                                      index=list(vcode_by_vname.keys()).index(wining_belief_vname),
                                                      key=pname)
                if selected_winning_vname != wining_belief_vname:
                    st.session_state["ga"].language_parameters[pname].inject_peak_belief(vcode_by_vname[selected_winning_vname], 1, locked=True)
                    st.warning("Belief manually edited: {}:{}".format(pname, selected_winning_vname))

            if st.button("Approve beliefs"):
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
                            if  vname not in st.session_state["prompt_content"][topic][pname]["examples by value"].keys():
                                st.session_state["prompt_content"][topic][pname]["examples by value"][vname] = []
                            for occurrence_index, context in details["details"].items():
                                gdf = kgu.build_gloss_df(st.session_state["consolidated_transcriptions"],
                                                         occurrence_index,
                                                         st.session_state["delimiters"])
                                st.session_state["prompt_content"][topic][pname]["examples by value"][vname].append({
                                    "english sentence":
                                        st.session_state["consolidated_transcriptions"][occurrence_index][
                                            "sentence_data"]["text"],
                                    "translation": st.session_state["consolidated_transcriptions"][occurrence_index][
                                        "recording_data"][
                                        "translation"],
                                    "gloss": gdf.to_dict(),
                                    "context": context
                                })
    st.markdown("#### Download raw grammatical description with examples as a json file.")
    st.download_button("Download raw description as a json file.", json.dumps(st.session_state["prompt_content"], indent=4), file_name="grammatical_description_of_{}.json".format(st.session_state["tl_name"]))
    st.session_state["generate_description"] = True

# REDACTED GRAMMATICAL DESCRIPTION
if st.session_state["ga_output_available"] and st.session_state["results_approved"] and st.session_state["generate_description"]:
    st.markdown("#### Generate redacted grammatical descriptions by topic.")
    lesson_topic = st.selectbox("Choose a topic", st.session_state["selected_topics"])
    lesson_audience = st.selectbox("Choose an audience", ["Adult L2 beginners", "L2 Teachers", "Primary school student", "Middle school student", "High school student", "Linguists"])
    lesson_format = st.selectbox("Choose a format", ["Display here", "Markdown"])

    doc_format_prompt = {
        "Display here": {"prompt": "Your lesson should be formatted with the github-flavored markdown as a string to display with Streamlit. the output should be correctly displayed when using the streamlit.markdown() function. Don't put the '''markdown''' in the output.", "extension": "txt"},
        "Markdown":  {"prompt": "Your lesson should be formatted with the github-flavored markdown as a string to display with Streamlit. the output should be correctly displayed when using the streamlit.markdown() function. Don't put the '''markdown''' in the output.", "extension": "txt"}
    }

    prompt = "Based on the following information, create a short well-organized grammar chapter about " + lesson_topic +  "  in the " + st.session_state["tl_name"] + " language "
    prompt += "for " + lesson_audience + "."
    prompt += "Don't use jargon or complicated words. Use simple, non-technical words. Don't use acronyms."
    prompt += "Compare the {} language to English to help readers understand the differences."
    prompt += "Use only on the material and examples provided. Do not use or infer any additional information, examples, or rules beyond what I give. If something is unclear or missing from the input, don't fill the gaps. Focus on explaining the rules and providing examples from the material I supply."
    prompt += "If there is no knowledge and no example on a topic, ignore it."
    prompt += "Use all and only the examples provided. Use the gloss information to explain which word in target language means what using horizontal tables showing the correspondance between English words and {} words.".format(st.session_state["tl_name"])
    prompt += "Here are the information (use only this information): "
    prompt += str(st.session_state["prompt_content"][lesson_topic]) + "."
    prompt += "Don't add encouragement or personal comment."
    prompt += doc_format_prompt[lesson_format]["prompt"]

    use_openai = st.toggle("Use OpenAI to write a short chapter about {} in {}".format(lesson_topic, st.session_state["tl_name"]))
    if use_openai:
        # Check if 'OPENAI_API_KEY' is available in st.secrets (i.e., running on Streamlit Cloud)
        if "OPEN_AI_KEY" in st.secrets:
            openai.api_key = st.secrets["OPEN_AI_KEY"]
        else:
            # Fallback to environment variable for local development
            openai.api_key = os.getenv("OPEN_AI_KEY")

        #print(openai.models.list())
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",
            messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are an assistant that writes short and engaging grammar book chapters for {}. Use only the information provided by the user. Use all the examples provided by the user. Do not introduce any additional material, even if it seems relevant. If the user-provided material is incomplete or ambiguous, ommit content. ".format(lesson_audience)
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ])
        st.session_state["redacted"] = response.choices[0].message.content
        st.markdown(response.choices[0].message.content)
        print(response.choices[0].message.content)

        st.download_button("Download lesson", st.session_state["redacted"], file_name="generated_grammar_lesson_{}_in{}".format(st.session_state["tl_name"], lesson_topic)+doc_format_prompt[lesson_format]["extension"])


