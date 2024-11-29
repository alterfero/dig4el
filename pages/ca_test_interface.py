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
from libs import knowledge_graph_utils as kgu, construction_agent as ca
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

if "tl_name" not in st.session_state:
    st.session_state["tl_name"] = ""
if "delimiters" not in st.session_state:
    st.session_state["delimiters"] = []
if "loaded_existing" not in st.session_state:
    st.session_state["loaded_existing"] = ""
if "cq_transcriptions" not in st.session_state:
    st.session_state["cq_transcriptions"] = []
if "kg" not in st.session_state:
    st.session_state["kg"] = {}

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
properson_props = {
            "PP1SG": {"number": "singular", "ref": ["speaker"]},
            "PP1INCDU": {"number": "dual", "ref": ["speaker", "listener"]},
            "PP1EXCDU": {"number": "dual", "ref": ["speaker", "other"]},
            "PP1INCTR": {"number": "trial", "ref": ["speaker", "listener", "other"]},
            "PP1EXCTR": {"number": "trial", "ref": ["speaker", "other", "other"]},
            "PP1INCPC": {"number": "paucal", "ref": ["speaker", "listener(s)", "other(s)"]},
            "PP1EXCPC": {"number": "paucal", "ref": ["speaker", "other(s)"]},
            "PP1INCPL": {"number": "plural", "ref": ["speaker", "listener(s)", "other(s)"]},
            "PP1EXCPL": {"number": "plural", "ref": ["speaker", "other(s)"]},

            "PP2SG": {"number": "singular", "ref": ["listener"]},
            "PP2DU": {"number": "dual", "ref": ["listener", "listener"]},
            "PP2TR": {"number": "trial", "ref": ["listener", "listener", "listener"]},
            "PP2PC": {"number": "paucal", "ref": ["listener(s)"]},
            "PP2PL": {"number": "plural", "ref": ["listener(s)"]},

            "PP3SG": {"number": "singular", "ref": ["other"]},
            "PP3DU": {"number": "dual", "ref": ["other", "other"]},
            "PP3TR": {"number": "trial", "ref": ["other", "other", "other"]},
            "PP3PC": {"number": "paucal", "ref": ["other(s)"]},

            "PP3PL": {"number": "plural", "ref": ["other(s)"]},
        }
parameters = {"speaker_gender": ["male", "female"],
               "listener_gender": ["male", "female"],
               "ref_gender": ["male", "female", "other", "multiple"],
               "number": ["singular", "dual", "trial", "paucal", "plural"],
               "intent": ["ASSERT", "ASK", "ORDER"],
               "polarity": ["POSITIVE", "NEGATIVE"],
               "semantic_role": ["agent", "patient", "oblique"]}

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.expander("Data setup"):
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
            # managing language input
            st.session_state["tl_name"] = st.session_state["cq_transcriptions"][0]["target language"]
            # managing delimiters
            if "delimiters" in st.session_state["cq_transcriptions"][0].keys():
                st.session_state["delimiters"] = st.session_state["cq_transcriptions"][0]["delimiters"]
                print("Word separators have been explicitly entered in the transcription.")
            elif st.session_state["tl_name"] in wu.language_pk_id_by_name.keys():
                with open("./data/delimiters.json", "r") as f:
                    delimiters_dict = json.load(f)
                    st.session_state["delimiters"] = delimiters_dict[st.session_state["tl_name"]]
                    print("Word separators are retrieved from the delimiters file, absent from the transcription.")
            else:
                st.session_state["delimiters"] = default_delimiters
            st.multiselect("Edit word separators if needed", delimiters_bank, default=st.session_state["delimiters"])
            if st.button("Generate Knowledge Graph"):
                # Creating kg
                st.session_state[
                    "kg"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                    st.session_state["cq_transcriptions"],
                    st.session_state["tl_name"],
                    st.session_state["delimiters"])
                st.success("{} Conversational Questionnaires: {} sentences, {} words with {} unique words".format(
                    len(st.session_state["cq_transcriptions"]), len(st.session_state["kg"]),
                    total_target_word_count, len(unique_words)))


if st.session_state["kg"] != {}:
    properson = st.selectbox("Select properson",properson_props.keys())
    c = ca.Properson_Construction(properson)
    c.populate_data_list(st.session_state["kg"])
    cdf = c.data_df
    data_list = c.data_list
    if st.toggle("Show raw dataframe"):
        st.dataframe(cdf)

    from itertools import product
    def generate_influence_combinations(parameters):
        """
        Generates all possible influence combinations for the given parameters.

        Parameters:
        - parameters (dict): Dictionary of parameters and their possible values.

        Returns:
        - List of tuples representing influence combinations.
        """
        param_names = list(parameters.keys())
        # Each parameter can be 0 (not influence) or 1 (influence)
        influence_options = [[0, 1] for _ in param_names]
        all_combinations = list(product(*influence_options))
        return param_names, all_combinations

    all_combinations = generate_influence_combinations(parameters)

    def test_combination(params, combination):
        # a combination is invalid if two target words are associated with different values of the parameters tested
        tested_params = [param for flag, param in zip(combination, params) if flag]
        d = {}
        for param in tested_params:
            d[param] = parameters[param]
        combined_values_list = [dict(zip(d.keys(), values)) for values in product(*d.values())]
        # for each value combination, search matching data
        data = []
        for combined_value in combined_values_list:
            tmp = {"parameters": tested_params, "combination":combined_value, "count":0, "target_words":[], "influence": "may influence"}
            for item in data_list:
                match = True
                for p, v in combined_value.items():
                    if item[p] != v:
                        match = False
                if match:
                    tmp["count"] += 1
                    if item["target_words"] != "":
                        tmp["target_words"].append(item["target_words"])
                        #print("item {} match combined value {}, target word {}".format(item, combined_value, item["target_words"] ))
            if tmp["count"] > 1:
                tmp["target_words"] = list(set(tmp["target_words"]))
                if len(tmp["target_words"]) == 0:
                    continue
                elif len(tmp["target_words"]) > 1:
                    tmp["influence"] = "no influence"
                data.append(tmp)
            else:
                tmp["influence"] = "no data"
        return data

    results = []
    for combination in all_combinations[1]:
        influence = test_combination(all_combinations[0], combination)
        for item in influence:
            if item["influence"] == "may influence":
                results.append(item)

    st.write(results)


