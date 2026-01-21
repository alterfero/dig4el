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
import io


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

if "ccq" not in st.session_state:
    with open("./conveqs/canonical_cqs.json", "r") as f:
        st.session_state.ccq = json.load(f)


def normalize_to_list(data_dict):
    # Ensure numeric sorting, even if keys are strings like "1", "24", "03", etc.
    sorted_keys = sorted(data_dict.keys(), key=lambda x: int(x))
    return [data_dict[k] for k in sorted_keys]

def format_translation_for_display(english, translation):
    try:
        if translation[0] == "'":
            translation = "'" + translation[1:].capitalize()
        else:
            translation = translation.capitalize()
            # add the same punctuation
        if english[-1] in ["?", "!", "."]:
            translation += " " + english[-1]
        return translation
    except IndexError:
        return translation


import re
def capitalize_sentences(text: str) -> str:
    # Split on sentence-ending punctuation followed by space
    text = text.replace("  ", " ")
    parts = re.split(r'([.!?]\s+)', text)
    out = []

    for i in range(0, len(parts), 2):
        sentence = parts[i].strip()
        punct = parts[i+1] if i+1 < len(parts) else ""

        if sentence:
            # Capitalize only first character, keep rest unchanged
            sentence = sentence[0].upper() + sentence[1:]

        out.append(sentence + punct)

    return "".join(out).strip()


def display_cq(cqo: dict, delimiters, title, uid, gloss=False):
    indi = cqo.get("target language", "target language unknown")
    pivot = cqo.get("pivot language", "pivot language unknown")
    st.markdown("### {}".format(title))
    st.markdown("In **{}**, pivot: **{}**.".format(indi, pivot))
    st.markdown("**Collected** from {}, by {}".format(cqo["interviewee"], cqo["interviewer"]))
    st.markdown("**Owner(s)**: {}".format("Jacques Vernaudon et Mirose Paia"))
    st.markdown("CQ unique **identification number**: {}".format(cqo["cq_uid"]))
    st.markdown("**Recording unique identification number**: {}".format(cqo["recording_uid"]))
    st.markdown("**Access**: {}".format("accessed read-only by anyone via ConveQs and DIG4EL tools"))
    st.divider()

    cqo_ready = copy.deepcopy(cqo)
    del cqo_ready["data"]
    cqo_ready["data"] = {}
    for index, value in cqo["data"].items():
        if "legacy index" in value and value["legacy index"] != "":
            if "-" in value["legacy index"]:
                legacy_indexes = value["legacy index"].split("-")
                for i in legacy_indexes:
                    cqo_ready["data"][i] = value
            else:
                cqo_ready["data"][value["legacy index"]] = value
        else:
            cqo_ready["data"][index] = value

    canonical_cq = [value
                    for item, value in st.session_state.ccq.items()
                    if st.session_state.ccq[item]["uid"] == uid][0]

    discq = copy.deepcopy(canonical_cq)

    for segment in discq["dialog"]:
        index = segment["index"]
        indi_list = []
        if index + "a" in cqo_ready["data"].keys():
            indi_list.append(cqo_ready["data"][index+"a"]["translation"])
            if index + "b" in cqo_ready["data"].keys():
                indi_list.append(cqo_ready["data"][index + "b"]["translation"])
                if index + "c" in cqo_ready["data"].keys():
                    indi_list.append(cqo_ready["data"][index + "c"]["translation"])
                    if index + "d" in cqo_ready["data"].keys():
                        indi_list.append(cqo_ready["data"][index + "d"]["translation"])

        else:
            if index in cqo_ready["data"]:
                indi_list.append(cqo_ready["data"][index]["translation"])
            else:
                indi_list.append("missing translation")

        tmps = capitalize_sentences(" ".join(indi_list))
        if segment["english"][-1] in ["?", "!", "."]:
            segment[indi] = tmps + segment["english"][-1]
        else:
            segment[indi] = tmps

    st.markdown("**Context**: {}".format(discq["context"]))
    st.divider()
    for segment in discq["dialog"]:

        st.write("{}: {}".format(segment["index"], segment["speaker"]))
        st.markdown("{}: *{}*".format("English", segment["english"]))
        if "alternate_pivot" in segment:
            if segment["alternate_pivot"] != "":
                st.markdown("{}: *{}*".format("Lingua franca", segment["alternate_pivot"]))
        st.markdown("{}: **{}**".format(indi, segment[indi]))
        lebt = segment.get("lebt", "")
        if lebt != "":
            st.markdown("Literal English Back-Translation: {}".format(lebt))
        comment = segment.get("comment", "")
        if comment != "":
            st.markdown("Comments: {}".format(comment))
        st.divider()


def display_same_cq_multiple_languages(cqs: list, title: str, uid: str) -> None:
    indis = []
    canonical_cq = [value
                    for item, value in st.session_state.ccq.items()
                    if st.session_state.ccq[item]["uid"] == uid][0]
    discq = copy.deepcopy(canonical_cq)

    for cqo in cqs:
        indis.append(cqo["target language"])
        cqo_ready = copy.deepcopy(cqo)
        del cqo_ready["data"]
        cqo_ready["data"] = {}
        for index, value in cqo["data"].items():
            if "legacy index" in value and value["legacy index"] != "":
                cqo_ready["data"][value["legacy index"]] = value
            else:
                cqo_ready["data"][index] = value
        indi = cqo_ready["target language"]
        for segment in discq["dialog"]:
            index = segment["index"]
            indi_list = []
            if index + "a" in cqo_ready["data"].keys():

                indi_list.append(cqo_ready["data"][index + "a"]["translation"])
                if index + "b" in cqo_ready["data"].keys():

                    indi_list.append(cqo_ready["data"][index + "b"]["translation"])
                    if index + "c" in cqo_ready["data"].keys():

                        indi_list.append(cqo_ready["data"][index + "c"]["translation"])
                        if index + "d" in cqo_ready["data"].keys():
                            indi_list.append(cqo_ready["data"][index + "d"]["translation"])
            else:
                if index in cqo_ready["data"]:
                    indi_list.append(cqo_ready["data"][index]["translation"])
                else:
                    indi_list.append("missing translation")

            tmps = capitalize_sentences(" ".join(indi_list))
            if segment["english"][-1] in ["?", "!", "."]:
                segment[indi] = tmps + segment["english"][-1]
            else:
                segment[indi] = tmps

    df = pd.DataFrame(discq["dialog"])

    # Optional: order columns as you like
    base_cols = ["index", "speaker", "english"]
    lang_cols = [c for c in df.columns if c not in base_cols]
    df = df[base_cols + lang_cols]

    # ---- Create Excel in memory ----
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        sheet_name = "Transcriptions"

        # Write table starting on row 3 (startrow = 2 because it's 0-based)
        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Write Title
        worksheet["A1"] = title

        # Make title bold / larger
        title_cell = worksheet["A1"]
        title_cell.font = title_cell.font.copy(bold=True, size=14)

        # Write Context
        worksheet["A2"] = discq["context"]
        ctx_cell = worksheet["A2"]
        ctx_cell.font = ctx_cell.font.copy(italic=True)

        # Auto-size columns
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) if cell.value is not None else 0
                         for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2

    # Streamlit download button
    filename = "CQ_" + title + "_"
    filename += ",".join(indis)
    st.download_button(
        label="Download Excel file",
        data=buffer.getvalue(),
        file_name=filename + ".xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.subheader(discq["title"])
    st.subheader("Context: {}".format(discq["context"]))
    for segment in discq["dialog"]:
        st.write("{}: {}".format(segment["index"], segment["speaker"]))
        st.markdown("{}: *{}*".format("english", segment["english"]))
        for indi in indis:
            st.markdown("{}: **{}**".format(indi, segment[indi]))
        st.divider()

def concept_words_to_pseudo_gloss_df(entry, delimiters):
    cwd = entry["concept_words"]
    reverse_cwd = {}
    for item in cwd:
        tws = cwd[item].split("...")
        for w in tws:
            reverse_cwd[w] = item
    words = stats.custom_split(entry["translation"], delimiters=delimiters)
    pseudo_gloss = []
    for word in words:
        if word in reverse_cwd.keys():
            pseudo_gloss.append(
                {
                    "word": word,
                    "concept": reverse_cwd[word]
                }
            )
        else:
            pseudo_gloss.append(
                {
                    "word": word,
                    "concept": ""
                }
            )
    pseudo_gloss_df = pd.DataFrame(pseudo_gloss).T
    # Use first row as column names
    try:
        pseudo_gloss_df.columns = pseudo_gloss_df.iloc[0]
        pseudo_gloss_df = pseudo_gloss_df.iloc[1:].reset_index(drop=True)
    except IndexError:
        print("ERROR with indexes concept_words_to_pseudo_gloss_df")
    return pseudo_gloss_df

def display_and_edit_cq(cqo: dict, filename: str) -> dict:
    if "filename" not in st.session_state:
        st.session_state.filename = filename
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




