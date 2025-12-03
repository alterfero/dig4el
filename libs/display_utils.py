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
from copy import deepcopy

def _concat_str(old: str, new: str, sep: str = " ") -> str:
    """Concatenate two strings with a separator, skipping empties and avoiding duplicates."""
    old = old or ""
    new = new or ""
    if not old:
        return new
    if not new:
        return old
    if new in old:
        return old
    return f"{old}{sep}{new}"

def _merge_concept_words(base: dict, incoming: dict) -> dict:
    """
    Merge two 'concept words' dicts:
    - Ignore empty strings.
    - If both sides have non-empty and different values, join with ' | ' (deduped).
    """
    base = dict(base or {})
    incoming = dict(incoming or {})
    for k, v in incoming.items():
        v = v or ""
        if not v:
            continue
        if k not in base or not base[k]:
            base[k] = v
        else:
            if v != base[k]:
                parts = {p.strip() for p in (str(base[k]) + "|" + str(v)).split("|") if p.strip()}
                base[k] = " | ".join(sorted(parts))
    return base

def merge_legacy_entries(entries):
    """
    entries: list of dicts with keys:
      - 'legacy index': str
      - 'cq': str
      - 'alternate pivot': str
      - 'translation': str
      - 'concept words': dict
      - 'comments': str

    Returns a new list where '2a', '2b', etc. are merged into '2'.
    """
    grouped = {}
    order = []

    for i, entry in enumerate(entries):
        # 1. Get legacy index or fallback to list position
        raw_idx = entry.get("legacy index")
        if raw_idx is None or raw_idx == "":
            raw_idx = str(i + 1)

        # 2. Normalize to numeric prefix
        m = re.match(r"(\d+)", raw_idx)
        base_idx = m.group(1) if m else raw_idx

        if base_idx not in grouped:
            # Start with a copy of the first entry for this base index
            merged = deepcopy(entry)
            merged["legacy index"] = base_idx  # normalize
            grouped[base_idx] = merged
            order.append(base_idx)
        else:
            merged = grouped[base_idx]

            # Concatenate string fields
            for field in ["cq", "alternate pivot", "translation", "comments"]:
                merged[field] = _concat_str(
                    merged.get(field, ""),
                    entry.get(field, "")
                )

            # Merge concept words dict
            merged["concept words"] = _merge_concept_words(
                merged.get("concept words", {}),
                entry.get("concept words", {}),
            )

    # Return in order of first appearance of each base index
    return [grouped[i] for i in order]



def display_cq(cqo: dict, delimiters, title, gloss=False):
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

    original_entry_list = normalize_to_list(cqo["data"])

    entry_list = merge_legacy_entries(original_entry_list)


    for entry in entry_list:
        li = entry["legacy index"]
        if li == "":
            li = str(entry_list.index(entry) + 1)
        english = entry["cq"]
        translation = entry["translation"]
        translation = format_translation_for_display(english, translation)

        st.markdown("{}: *{}*".format(li, english))
        st.markdown("**{}**".format(translation))

        if gloss:
            cwd = entry["concept_words"]
            reverse_cwd = {}
            for item in cwd:
                tws = cwd[item].split("...")
                for w in tws:
                    reverse_cwd[w] = item
            words = stats.custom_split(entry["translation"], delimiters=cqo["delimiters"])
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
            try:
                pseudo_gloss_df = pd.DataFrame(pseudo_gloss).T
                # Use first row as column names
                pseudo_gloss_df.columns = pseudo_gloss_df.iloc[0]
                pseudo_gloss_df = pseudo_gloss_df.iloc[1:].reset_index(drop=True)
                st.dataframe(pseudo_gloss_df, hide_index=True)
            except IndexError:
                try:
                    print("IndexError when creating pseudo-gloss in display_cq. {}, {}, {}".format(indi, title, entry["cq"]))
                    pseudo_gloss_df = pd.DataFrame(pseudo_gloss).T
                    st.dataframe(pseudo_gloss_df, hide_index=True)
                except:
                    print("Double failure when creating pseudo-gloss in display_cq")
                    st.markdown("*Pseudo-gloss cannot be generated for this sentence*")

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

def reformat_cq_index(cq):
    cqo = copy.deepcopy(cq)
    del cqo["data"]
    cqo["data"] = {}
    tmp_data_a = {}
    tmp_data_b = {}
    tmp_data_c = {}
    tmp_data_d = {}
    base_index = 0
    last_base_index = 0
    before_last_base_index = 0
    for index, data in cq["data"].items():
        # print("key: {}".format(index))
        if "legacy index" in data:
            # print("There is a legacy index field")
            legacy_index = data["legacy index"] if data["legacy index"] != "" else index
        else:
            # print("No legacy index field")
            legacy_index = index
        # print("legacy_index: {}".format(legacy_index))
        # print("content: {}".format(data["cq"]))
        if legacy_index[-1] == "a":
            base_index = legacy_index[:-1]
            # print("base index: {}".format(base_index))
            tmp_data_a = data
            # print("part A: {}".format(data["cq"]))
            before_last_base_index = last_base_index
            last_base_index = base_index
            continue

        if legacy_index[-1] == "b":
            combined = {
            "legacy index": base_index,
            "cq": tmp_data_a["cq"] + " " + data["cq"],
            "alternate_pivot": tmp_data_a["alternate_pivot"] + data["alternate_pivot"],
            "translation": format_translation_for_display(tmp_data_a["cq"], tmp_data_a["translation"])
                           + format_translation_for_display(data["cq"], data["translation"]),
            "concept_words": tmp_data_a["concept_words"] | data["concept_words"]
            }
            # print("Combined with A at base index {}".format(base_index))
            # print(combined)
            tmp_data_b = combined
            cqo["data"][base_index] = combined
            before_last_base_index = last_base_index
            last_base_index = base_index
            continue

        if legacy_index[-1] == "c":
            # print("There's a C, combining with previous")
            combined = {
                "legacy index": last_base_index,
                "cq": tmp_data_b["cq"] + " " + data["cq"],
                "alternate_pivot": tmp_data_b["alternate_pivot"] + data["alternate_pivot"],
                "translation": format_translation_for_display(tmp_data_b["cq"], tmp_data_b["translation"]) +
                               format_translation_for_display(data["cq"], data["translation"]),
                "concept_words": tmp_data_b["concept_words"] | data["concept_words"]
            }
            tmp_data_c = combined
            # print("Combined with AB at base index {}".format(last_base_index))
            # print(combined)
            cqo["data"][last_base_index] = combined
            before_last_base_index = last_base_index
            last_base_index = base_index
            continue
        if legacy_index[-1] == "d":
            # print("C'mon, there's a D, combining with previous")
            combined = {
                "legacy index": before_last_base_index,
                "cq": tmp_data_c["cq"] + " " + data["cq"],
                "alternate_pivot": tmp_data_c["alternate_pivot"] + data["alternate_pivot"],
                "translation": format_translation_for_display(tmp_data_c["cq"], tmp_data_c["translation"]) +
                               format_translation_for_display(data["cq"], data["translation"]),
                "concept_words": tmp_data_c["concept_words"] | data["concept_words"]
            }
            tmp_data_d = combined
            # print("Combined with ABC at base index {}".format(before_last_base_index))
            # print(combined)
            cqo["data"][before_last_base_index] = combined
            before_last_base_index = last_base_index
            last_base_index = base_index
            continue
        else:
            # print("Direct through: at index {}".format(legacy_index))
            cqo["data"][legacy_index] = cq["data"][index]
            cqo["data"][legacy_index]["translation"] = format_translation_for_display(
                cqo["data"][legacy_index]["cq"],
                cqo["data"][legacy_index]["translation"]
            )

            # print(cqo["data"][legacy_index])
    return cqo

def display_same_cq_multiple_languages(cqs_content, title, show_pseudo_glosses=False):
    verify = True
    t1 = cqs_content[0]["data"]["1"]["cq"]
    l1 = len(cqs_content[0])
    for item in cqs_content:
        if item["data"]["1"]["cq"] != t1:
            return st.error("These CQs are not comparable")
        if len(item) != l1:
            print("CQs don't have all the same length")

    reformated_cqs_content = []
    for cq in cqs_content:
        reformated_cqs_content.append(reformat_cq_index(cq))
    c1 = reformated_cqs_content[0]

    st.subheader(title)
    for index, data in c1["data"].items():
        if "legacy index" in data:
            displayed_index = str(index) if data["legacy index"] == "" else data["legacy index"]
        else:
            displayed_index = str(index)
        st.markdown("#### {} - {}".format(displayed_index, data["cq"]))
        local_table = []
        for cqi in range(len(reformated_cqs_content)):
            if index in reformated_cqs_content[cqi]["data"]:
                c = reformated_cqs_content[cqi]["data"][index]
                local_table.append(
                    {
                        "language": reformated_cqs_content[cqi]["target language"],
                        "translation": c["translation"],
                        "pivot": c["alternate_pivot"] if "alternate pivot" in c.keys() else ""
                    }
                )
            else:
                local_table.append(
                    {
                        "language": reformated_cqs_content[cqi]["target language"] + ": No content for this index",
                        "translation": "",
                        "pivot": ""
                    })
        is_pivot = False
        for language_entry in local_table:
            if language_entry["pivot"] != "":
                is_pivot = True

        # local_df = pd.DataFrame(local_table).T
        # if not is_pivot:
        #     local_df = local_df.drop(labels=["pivot"], axis=0)
        # local_df.columns = local_df.iloc[0]
        # local_df = local_df.iloc[1:].reset_index(drop=True)
        # st.dataframe(local_df, hide_index=True)

        local_df = pd.DataFrame(local_table)
        if not is_pivot:
            local_df = local_df.drop(labels=["pivot"], axis=1)
        st.dataframe(local_df, hide_index=True)

        if show_pseudo_glosses:
            for cqi in range(len(reformated_cqs_content)):
                pseudo_gloss = concept_words_to_pseudo_gloss_df(reformated_cqs_content[cqi]["data"][index],
                                                                delimiters=reformated_cqs_content[cqi]["delimiters"])
                st.write(reformated_cqs_content[cqi]["target language"])
                st.dataframe(pseudo_gloss, hide_index=True)





