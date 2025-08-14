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
from libs import ga_param_selection_utils as psu
import json
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
from pathlib import Path
from libs import file_manager_utils as fmu

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
    with open("./external_data/params_by_topic.json", "r", encoding='utf-8') as f:
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
if "cqs" not in st.session_state:
    st.session_state.cqs = []

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

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"),
    "storage"
)

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

st.sidebar.subheader("DIG4EL")
st.sidebar.write("Process")
side_info = st.sidebar.empty()

with st.sidebar:
    st.markdown("---")
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.page_link("pages/dashboard.py", label="Back to dashboard", icon=":material/contract_edit:")

st.title("Generate knowledge from CQs")
with st.popover("How to use this page"):
    st.markdown("""
    ### Generating knowledge from CQ
    This page allows using CQ translations in DIG4EL format to 'guess' how the grammar of the language works.\\
    You just have to upload CQ translations using the **Input** section and press on the **Launch CQ processing** button. 
    Once DIG4EL has guessed as many grammatical parameters are possible, you will see a table with these parameters 
    """)

show_details = st.toggle("Show computation details")
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
    st.write("Current target language: {}".format(st.session_state.indi_language))
    if st.session_state.indi_language in ["English", "Abkhaz-Adyge"]:
        st.warning("Select the target language name in the dashboard first!")
    cq_source = st.radio("Use CQ translations...", ["available online", "from your computer"])
    if cq_source == "available online":
        if st.session_state.indi_language not in os.listdir(BASE_LD_PATH):
            st.write("No CQ translation files available online yet for {}".format(st.session_state.indi_language))
            st.write("You can upload files from your computer below and select 'add them to the public repository' "
                     "if you want to make them available online.")
        else:
            available_transcription_files = [fn
                                             for fn in os.listdir(os.path.join(BASE_LD_PATH,
                                                                               st.session_state.indi_language,
                                                                               "cq",
                                                                               "cq_translations"
                                                                               ))
                                             if fn.endswith(".json")]
            selected_online_files = st.multiselect("Select available online files to process",
                                                   ["ALL"] + available_transcription_files)
            if selected_online_files:
                if "ALL" in selected_online_files:
                    selected_online_files = available_transcription_files
                st.session_state.cqs = selected_online_files

                if st.session_state.cqs is not None:
                    st.session_state["cq_transcriptions"] = []
                    for cq in st.session_state.cqs:
                        with open(os.path.join(BASE_LD_PATH,
                                               st.session_state.indi_language,
                                               "cq",
                                               "cq_translations",
                                               cq), "r", encoding='utf-8') as f:
                            new_cq = json.load(f)
                        # update concept labels
                        updated_cq, found_some = u.update_concept_names_in_transcription(new_cq)
                        if found_some:
                            st.write("Some concept labels have been aligned with the latest version.")
                        st.session_state["cq_transcriptions"].append(updated_cq)
                st.session_state["loaded_existing"] = True
                st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))


    elif cq_source == "from your computer":
        add_to_repo = st.checkbox("Add these files to the read-only online repository")
        if add_to_repo:
            st.markdown("""Documents uploaded to the repository can be **accessed** through DIG4EL **by anyone**. 
            It is a public **read-only** access : The documents cannot be modified or downloaded.
            If you have any rights to these documents, you can ask us to provide you with a copy,
            and/or to  remove them from the repository using the email address on the home page.""")
            owner = st.text_input("Owner's full name")
            orcid = st.text_input("Owner's ORCID number (optional for now)")
            authorization = st.selectbox("This content can be...",
                                         ["accessed read-only by anyone via DIG4EL tools"])
            st.divider()

        st.session_state.cqs = st.file_uploader(
            "Load Conversational Questionnaires' transcriptions (all at once for multiple transcriptions)", type="json",
            accept_multiple_files=True)

        if st.session_state.cqs is not None:
            st.session_state["cq_transcriptions"] = []
            for cq in st.session_state.cqs:
                new_cq = json.load(cq)
                if "cq_uid" not in new_cq.keys():
                    st.warning("Discarding file: Not a DIG4EL CQ translation.")
                else:
                    # update concept labels
                    updated_cq, found_some = u.update_concept_names_in_transcription(new_cq)
                    if found_some:
                        st.write("Some concept labels have been aligned with the latest version.")
                    if add_to_repo:
                        updated_cq["owner name"] = owner
                        updated_cq["owner orcid"] = orcid
                        updated_cq["authorization"] = authorization
                        if st.session_state.indi_language not in os.listdir(BASE_LD_PATH):
                            fmu.create_ld(BASE_LD_PATH, st.session_state.indi_language)
                        with open(os.path.join(BASE_LD_PATH,
                                               st.session_state.indi_language,
                                               "cq",
                                               "cq_translations",
                                               cq.name), "w", encoding='utf-8') as f:
                            u.save_json_normalized(updated_cq, f)
                        st.success("{} added to the online repository".format(cq.name))
                    st.session_state["cq_transcriptions"].append(updated_cq)
            st.session_state["loaded_existing"] = True
            st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))

    # load transcriptions, create knowledge graph
    if st.session_state["loaded_existing"] and st.button("Launch CQ processing"):
        if st.session_state["cq_transcriptions"] != []:
            # Consolidating transcriptions - Knowledge Graph
            st.session_state[
                "kg"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                st.session_state["cq_transcriptions"],
                st.session_state["tl_name"],
                st.session_state["delimiters"])
            with open("./data/knowledge/current_kg.json", "w", encoding='utf-8') as f:
                u.save_json_normalized(st.session_state["kg"], f, indent=4)
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
                with open("./data/delimiters.json", "r", encoding='utf-8') as f:
                    delimiters_dict = json.load(f)
                    st.session_state["delimiters"] = delimiters_dict[st.session_state["tl_name"]]
                    print("Word separators are retrieved from a file.")
            else:
                st.session_state["delimiters"] = st.multiselect("Edit word separators if needed", delimiters_bank,
                                                                default=default_delimiters)
            side_info.write("Input files mapped")

# PREPROCESSING: KNOWLEDGE, OBSERVATIONS, PARAMETER DISCOVERY ==============================

if st.session_state["kg"] and not st.session_state["preprocessing_done"]:
    with st.spinner("Retrieving existing knowledge"):
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
        with st.spinner("Making observations..."):
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
        with st.spinner("Computing statistical priors"):
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
        with st.spinner("Discovering grammatical parameters that can be inferred from knowledge and observations"):
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
            st.markdown("{} parameters observed, {} known from WALS, {} known from Grambank.".format(
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
st.session_state["run_ga"] = True
if (st.session_state["preprocessing_done"]
        and st.session_state["run_ga"]
        and not st.session_state["ga_output_available"]):
    with st.spinner("Running Bayesian Agent..."):
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
            st.markdown("""Based on statistical information, existing knowledge, 
            observations and inferences across parameters, the following beliefs formed a consensus.
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
                if round(100 * (1 - P.entropy)) > 80:  # Only add beliefs if confidence > 80%
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

# PACKAGING RESULTS

if st.session_state["ga_output_available"] and st.session_state["results_approved"]:

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
        if (1 - P.entropy) > 0.8:
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
    with open(os.path.join(BASE_LD_PATH,
                           st.session_state.indi_language,
                           "cq",
                           "cq_knowledge",
                           "cq_knowledge.json"), "w", encoding='utf-8') as f:
        u.save_json_normalized(json_blob, f)
    st.success("CQ knowledge completed and added to the knowledge bank!")
    st.session_state.has_bayesian = True
    st.session_state.bayesian_data = json_blob
    st.page_link("pages/dashboard.py", label="Back to dashboard", icon=":material/contract_edit:")

    # st.download_button(label=" 📥You can download CQ Knowledge results for future use.📥",
    #                    data=u.save_json_normalizeds(json_blob),
    #                    file_name="dig4el_cq_knowledge.json"
    #                    )

