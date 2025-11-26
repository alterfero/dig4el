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
import copy

import streamlit as st
import pandas as pd
import json
import os
from libs import stats

DELIMITER_BANK = [
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

def preview_dig4el_cq(cqo: dict, filename: str) -> dict:
    if "filename" not in st.session_state:
        st.session_state.filename = filename
    def normalize_to_list(data_dict):
        # Ensure numeric sorting, even if keys are strings like "1", "24", "03", etc.
        sorted_keys = sorted(data_dict.keys(), key=lambda x: int(x))
        return [data_dict[k] for k in sorted_keys]
    def list_to_numbered_dict(items_list):
        """
        Convert a list of items back into a dict whose keys are
        stringified integers starting from "1".
        """
        return {str(i + 1): item for i, item in enumerate(items_list)}
    cq = copy.deepcopy(cqo)
    indi = cq["target language"]
    pivot = cq["pivot language"]
    if "data" not in st.session_state or filename != st.session_state.filename:
        st.session_state.data = normalize_to_list(cq["data"])
        st.session_state.filename = filename
    st.divider()
    if st.button("Save modified CQ", key=f"save_{filename}_top"):
        edited_dialog = list_to_numbered_dict(st.session_state.data)
        cq["data"] = edited_dialog
        return cq
    st.write(f"Conversational Questionnaire file: {filename}")
    st.markdown(f"**{pivot}** to **{indi}**")
    delimiters = st.multiselect("Word delimiters", DELIMITER_BANK, default=cq["delimiters"])
    st.markdown("**Content**")
    for idx, entry in enumerate(st.session_state.data):
        with st.expander(f"{entry['legacy index']} — {entry['translation']} ({entry['cq']}) ", expanded=False):
            # ---- Display sentences ----
            st.markdown(f"### Legacy index: `{entry['legacy index']}`")

            st.text_input(
                "Pivot sentence",
                value=entry["cq"],
                key=f"pivot_{idx}",
                disabled=False,  # change to False if you want it editable
            )

            target = st.text_input(
                "Target sentence",
                value=entry["translation"],
                key=f"target_{idx}",
            )
            st.session_state.data[idx]["translation"] = target  # keep updated

            # ---- Dataframe of concepts (editable words column) ----
            df = pd.DataFrame(
                [{"concept": k, "words": v} for k, v in entry["concept_words"].items()]
            )

            st.markdown("### Concept Map")
            selected = st.dataframe(
                df, selection_mode="single-cell", on_select="rerun"
            )

            if selected["selection"]["cells"] != []:
                selected_row = selected["selection"]["cells"][0][0]
                if selected_row != st.session_state.selected_row:
                    st.session_state.selected_row = selected_row
                    st.session_state.data = normalize_to_list(cq["data"])

                selected_item = df.iloc[selected_row]
                selected_concept = selected_item["concept"]

                # Tokenize target sentence
                tokens = stats.custom_split(target, delimiters)

                selected_tokens = st.multiselect(
                    f"Select tokens for **{selected_concept}**:",
                    tokens,
                    key=f"tokens_{idx}",
                )

                if st.button("Apply selection", key=f"apply_{idx}"):
                    # Save tokens (you can choose how to join them)
                    combined = "...".join(selected_tokens)
                    st.session_state.data[idx]["concept_words"][selected_concept] = combined
                    st.success(f"Assigned words to concept: {selected_concept}")
                    st.rerun()
    if st.button("Save modified CQ", key=f"save_{filename}"):
        edited_dialog = list_to_numbered_dict(st.session_state.data)
        cq["data"] = edited_dialog
        return cq


