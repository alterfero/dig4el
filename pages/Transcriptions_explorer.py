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
import plotly.express as px
import os

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
if "selected_concept" not in st.session_state:
    st.session_state["selected_concept"] = "PP1SG"
if "cdict" not in st.session_state:
    st.session_state["cdict"] = {}
if "pdict" not in st.session_state:
    st.session_state["pdict"] = {}
if "pfilter" not in st.session_state:
    st.session_state["pfilter"] = {"intent": [], "enunciation": [], "predicate": {}, "ip": {}, "rp": []}
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
    "\u2026",
    "..."
]
default_delimiters = [" ", ".", ",", ";", ":", "!", "?", "\u2026", "'"]

with st.sidebar:
    st.subheader("DIG4EL")
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

with st.expander("Input", expanded=True):
    st.markdown("#### Load your transcriptions")
    # load transcriptions
    cqs = st.file_uploader("Load your Conversational Questionnaire transcriptions (all at once for multiple transcriptions)", type="json", accept_multiple_files=True)
    if cqs != []:
        st.session_state["cq_transcriptions"] = []
        for cq in cqs:
            new_cq = json.load(cq)
            st.session_state["cq_transcriptions"].append(new_cq)
        st.session_state["loaded_existing"] = True
        st.session_state["tl_name"] = st.session_state["cq_transcriptions"][0]["target language"]
        st.write("{} files loaded in {}.".format(len(st.session_state["cq_transcriptions"]), st.session_state["tl_name"]))

    if st.session_state["loaded_existing"]:
        if st.session_state["cq_transcriptions"] != []:
            # managing delimiters
            if "delimiters" in st.session_state["cq_transcriptions"][0].keys():
                st.session_state["delimiters"] = st.session_state["cq_transcriptions"][0]["delimiters"]
                st.write("Word separators have been explicitly entered in the transcription.")
            else:
                st.session_state["delimiters"] = default_delimiters
            deli = st.multiselect("Edit word separators if needed: edit the field below and click on 'Update word separators'", delimiters_bank, default=st.session_state["delimiters"])
            if st.button("Update word separators"):
                st.session_state["delimiters"] = deli
            # Consolidating transcriptions - Knowledge Graph
            st.write("Once your transcriptions are loaded and word separators selected, click on 'Build knowledge graph' below")

            if st.button("Build knowledge graph"):
                st.session_state["knowledge_graph"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                    st.session_state["cq_transcriptions"],
                    st.session_state["tl_name"],
                    st.session_state["delimiters"])
                with open("./data/knowledge/current_kg.json", "w") as f:
                    json.dump(st.session_state["knowledge_graph"], f, indent=4)
                st.write("{} Conversational Questionnaires: {} sentences, {} words with {} unique words".format(
                    len(st.session_state["cq_transcriptions"]), len(st.session_state["knowledge_graph"]),
                    total_target_word_count, len(unique_words)))
            if st.session_state["knowledge_graph"] != {}:
                st.success("Your transcriptions are ready for exploration, you can click on 'Explore by concept' or 'Explore by parameter' below")

    st.markdown("---")
    st.markdown("#### or use available examples")
    available_transcriptions_folders = os.listdir(os.path.join(".", "available_transcriptions"))
    if ".DS_Store" in available_transcriptions_folders:
        available_transcriptions_folders.remove(".DS_Store")
    existing = st.selectbox("Or load an available set of transcriptions", available_transcriptions_folders)
    if st.button("Load existing"):
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
                "knowledge_graph"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                st.session_state["cq_transcriptions"],
                st.session_state["tl_name"],
                st.session_state["delimiters"])
            with open("./data/knowledge/current_kg.json", "w") as f:
                json.dump(st.session_state["knowledge_graph"], f, indent=4)
            st.write("{} Conversational Questionnaires: {} sentences, {} words with {} unique words".format(
                len(st.session_state["cq_transcriptions"]), len(st.session_state["knowledge_graph"]),
                total_target_word_count, len(unique_words)))
            st.session_state["loaded_existing"] = True
            st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))
            if st.session_state["knowledge_graph"] != {}:
                st.success("Transcriptions are ready for exploration, you can click on 'Explore by concept' or 'Explore by parameter' below")

if st.session_state["knowledge_graph"] != {}:
    st.session_state["cdict"] = kgu.build_concept_dict(st.session_state["knowledge_graph"])
    def index_parameters(cdict):
        param_index = {}
        for concept, details_list in cdict.items():
            for oc in details_list:
                for param_cat in oc["particularization"].keys():
                    if param_cat not in param_index.keys():
                        param_index[param_cat] = {}
                    for param in oc["particularization"][param_cat].keys():
                        if param not in param_index[param_cat]:
                            param_index[param_cat][param] = []
                        if oc["particularization"][param_cat][param] not in param_index[param_cat][param]:
                            param_index[param_cat][param].append(oc["particularization"][param_cat][param])
        return param_index
    st.session_state["pdict"] = index_parameters(st.session_state["cdict"])

# EXPLORE BY CONCEPT -------------------
    with st.expander("Explore by concept"):
        user_concept = st.selectbox("Select a concept", list(st.session_state["cdict"].keys()), index=list(st.session_state["cdict"].keys()).index(st.session_state["selected_concept"]))
        if st.button("Explore concept {}".format(user_concept)):
            st.session_state["selected_concept"] = user_concept

        st.write("{} occurrences of **{}**. Click on the left of any row to get more details on an entry.".format(len(st.session_state["cdict"][st.session_state["selected_concept"]]), st.session_state["selected_concept"]))

        #flatten cdict[selected] to display in a df
        flat_cdict_oc = []
        #st.write(st.session_state["cdict"][selected_concept])
        for oc in st.session_state["cdict"][st.session_state["selected_concept"]]:
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
            selected_cdict_entry = st.session_state["cdict"][st.session_state["selected_concept"]][(selected["selection"]["rows"][0])]
            kg_entry = selected_cdict_entry["kg_entry"]

            # Supergloss
            supergloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], kg_entry, st.session_state["delimiters"])
            gloss_selection = st.dataframe(supergloss, use_container_width=True, selection_mode="single-column", on_select="rerun", key="supergloss_df")
            # show sentences with the selected word if any
            if gloss_selection["selection"]["columns"] != []:
                tw = gloss_selection["selection"]["columns"][0].split("_")[0]
                kg_entries_with_word = kgu.get_sentences_with_word(st.session_state["knowledge_graph"],
                                                                   tw,
                                                                   st.session_state["delimiters"])
                # stats
                wstats = {}
                for e in kg_entries_with_word:
                    c = [c for c in st.session_state["knowledge_graph"][e]["recording_data"]["concept_words"].keys() if tw in st.session_state["knowledge_graph"][e]["recording_data"]["concept_words"][c].split("...")]
                    if c == []:
                        c = "undefined"
                    else:
                        c = c[0]
                    if c in wstats.keys():
                        wstats[c] += 1
                    else:
                        wstats[c] = 1
                wstats_df = pd.DataFrame(list(wstats.items()), columns=["Concept", "Number of occurrences"])
                wstats_df = wstats_df.sort_values("Number of occurrences", ascending=False)

                st.subheader("'**{}**' is, or is part of, the expression of the following concepts:".format(tw))
                # Create the clickable bar chart
                fig = px.bar(
                    wstats_df,
                    x='Concept',
                    y='Number of occurrences',
                )
                # Enable clicking
                fig.update_layout(
                    xaxis_title="Concepts",
                    yaxis_title="Count",
                    # Rotate x-axis labels if there are many words
                    xaxis=dict(tickangle=45)
                )
                # Display the chart and store click data in session state
                sc = st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key='bar_chart',
                    theme="streamlit",
                    on_select="rerun"
                )
                if sc["selection"]["points"]:
                    s_concept = sc["selection"]["points"][0]["label"]
                else:
                    s_concept = ""
                if s_concept != "" \
                        and s_concept != "undefined" \
                        and s_concept != st.session_state["selected_concept"] \
                        and s_concept in list(st.session_state["cdict"].keys()):
                    if st.button("Jump to concept {}".format(s_concept)):
                        st.session_state["selected_concept"] = s_concept
                        st.rerun()

                if s_concept != "" and s_concept != "undefined":
                    st.write("#### Sentences with *{}* contributing to the expression of **{}**".format(gloss_selection["selection"]["columns"][0], s_concept))
                else:
                    st.write("#### Sentences with *{}*".format(
                        gloss_selection["selection"]["columns"][0], s_concept))
                gloss_counter = 0
                for kge in kg_entries_with_word:
                    kgc = st.session_state["knowledge_graph"][kge]
                    if s_concept != "" and s_concept != "undefined":
                        if s_concept in kgc["recording_data"]["concept_words"].keys() and tw in kgc["recording_data"]["concept_words"][s_concept].split("..."):
                            gloss_counter += 1
                            gloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], kge,
                                                       st.session_state["delimiters"])
                            st.write(st.session_state["knowledge_graph"][kge]["sentence_data"]["text"])
                            st.dataframe(gloss, key="subgloss"+str(gloss_counter), use_container_width=True)
                    else:
                        gloss_counter += 1
                        gloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], kge,
                                                   st.session_state["delimiters"])
                        st.write(st.session_state["knowledge_graph"][kge]["sentence_data"]["text"])
                        st.dataframe(gloss, key="subgloss" + str(gloss_counter), use_container_width=True)

            # Showing sentences using the same target word(s)
            st.write("---")
            if selected_cdict_entry["target_words"] != "":
                entries_with_target_word = kgu.get_sentences_with_word(st.session_state["knowledge_graph"],
                                                                   selected_cdict_entry["target_words"],
                                                                   st.session_state["delimiters"])
                current_entries = []
                for item in st.session_state["cdict"][st.session_state["selected_concept"]]:
                    current_entries.append(item["kg_entry"])
                current_entries = list(set(current_entries))
                st.subheader("Other occurrences of '**{}**' not connected to the selected concept:".format(
                    selected_cdict_entry["target_words"],
                    st.session_state["selected_concept"]))
                xcount = 0
                for e in entries_with_target_word:
                    if e not in current_entries:
                        xcount += 1
                        gloss = kgu.build_gloss_df(st.session_state["knowledge_graph"], e,
                                                   st.session_state["delimiters"])
                        st.write(st.session_state["knowledge_graph"][e]["sentence_data"]["text"])
                        st.dataframe(gloss)
                if xcount == 0:
                    st.write("None")

# EXPLORE BY PARAMETER
    with st.expander("Explore by parameter"):
        with st.popover("info"):
            st.markdown("""
            You can filter using **Intent**, **Internal Particularization** and **Relational Particularization**.
            - Multiple choices within a selection field are unions (**OR**): If you select both "ASK" and "ORDER" in Intent, any entry with an "ASK" **OR** "ORDER" intent will be selected. 
            - Selections across selection fields are intersections (**AND**): If you select "ASK" in Intent and "NEGATIVE" polarity in Internal Particularization, only entries with both "ASK" Intent **AND** "NEGATIVE" polarity will be selected.
            
            This behavior allows selecting entries with any given range of grammatical parameters across those proposed. 
            
            **If you don't see any output**, it probably means that there are no entries satisfying the filter you entered.
            """)
        kcount = 0
        # FILTER INPUT
        colq, cola, colw, cole = st.columns(4)
        # intent
        s_intent = colq.multiselect("Filter by Intent", ["All"] + st.session_state["pdict"]["intent"]["intent"])
        if s_intent == ["All"] or s_intent == []:
            is_intent_filter = False
            s_intent = []
        else:
            is_intent_filter = True
        st.session_state["pfilter"]["intent"] = s_intent
        # type of predicate
        s_pred = cola.multiselect("Filter by type of Predicate", ["All"] + st.session_state["pdict"]["predicate"]["predicate"])
        if s_pred == ["All"] or s_pred == []:
            is_pred_filter = False
            s_pred = []
        else:
            is_pred_filter = True
        st.session_state["pfilter"]["predicate"] = s_pred
        # ip
        s_internal = colw.multiselect("Filter by Internal Particularization", ["All"] + list(st.session_state["pdict"]["internal_particularization"].keys()))
        if s_internal == ["All"] or s_internal == []:
            is_ip_filter = False
            s_internal = []
        else:
            is_ip_filter = True
        if is_ip_filter:
            for p in s_internal:
                kcount += 1
                pp = colw.multiselect(f"Values of {p}",
                                      ["All"] + st.session_state["pdict"]["internal_particularization"][p],
                                      key="pp" + str(kcount))
                if pp == ["All"]:
                    pp = []
                st.session_state["pfilter"]["ip"][p] = pp
        # rp
        s_relational = cole.multiselect("Filter by Relational Particularization", ["All"] + list(st.session_state["pdict"]["relational_particularization"].keys()))
        if s_relational == ["All"] or s_relational == []:
            s_relational = []
            is_rp_filter = False
        else:
            is_rp_filter = True
        st.session_state["pfilter"]["rp"] = s_relational

        # FILTER USAGE
        selected_oc = []
        si_count = 0
        sp_count = 0
        sip_count = 0
        srp_count = 0
        oc_count = 0
        for concept in st.session_state["cdict"].keys():
            for oc in st.session_state["cdict"][concept]:
                oc_count += 1
                si = False
                sp = False
                sip = False
                srp = False
                # intent
                if is_intent_filter:
                    if oc["particularization"]["intent"]["intent"] in st.session_state["pfilter"]["intent"]:
                        si = True
                        si_count += 1
                else:
                    si = True
                    si_count += 1
                # predicate
                if is_pred_filter:
                    if oc["particularization"]["predicate"]["predicate"] in st.session_state["pfilter"]["predicate"]:
                        sp = True
                        sp_count += 1
                else:
                    sp = True
                    sp_count += 1
                # internal particularization
                if is_ip_filter:
                    oc_ip_params = list(oc["particularization"]["internal_particularization"].keys())
                    subsip = True
                    if oc_ip_params == []:
                        subsip = False
                    for pfilter_ip_param in st.session_state["pfilter"]["ip"].keys():
                        #print("pfilter_ip_param: {}".format(pfilter_ip_param))
                        #print("oc_ip_params: {}".format(oc_ip_params))
                        if pfilter_ip_param in oc_ip_params:
                            #print("MATCH: pfilter_ip_param in oc_ip_params")
                            #print(oc["particularization"]["internal_particularization"][pfilter_ip_param])
                            #print("in?")
                            #print(st.session_state["pfilter"]["ip"][pfilter_ip_param])
                            if oc["particularization"]["internal_particularization"][pfilter_ip_param] in st.session_state["pfilter"]["ip"][pfilter_ip_param]:
                                continue
                            else:
                                subsip = False
                        else:
                            subsip = False
                    sip = subsip
                    if sip:
                        sip_count += 1
                else:
                    sip = True
                    sip_count += 1
                # relational particularization
                if is_rp_filter:
                    oc_rp_params = oc["particularization"]["relational_particularization"].keys()
                    for oc_rp_param in oc_rp_params:
                        if oc_rp_param in st.session_state["pfilter"]["rp"]:
                            srp = True
                            srp_count += 1
                else:
                    srp = True
                    srp_count += 1
                if si and sp and sip and srp:
                    selected_oc.append(oc)

        # Display results
        # keep unique pivot sentences
        displayed_oc = []
        psl = []
        for oc in selected_oc:
            if oc["pivot_sentence"] not in psl:
                psl.append(oc["pivot_sentence"])
                displayed_oc.append(oc)
        st.write("{} entries selected".format(len(displayed_oc)))

        ocp_df = pd.DataFrame(displayed_oc, columns=["pivot_sentence", "target_sentence"])
        ocp_selected = st.dataframe(ocp_df, selection_mode="single-row", on_select=display_result, key="ocp_df", use_container_width=True)
        if ocp_selected["selection"]["rows"] != []:
            selected_cdictp_entry = displayed_oc[(ocp_selected["selection"]["rows"][0])]
            kgp_entry = selected_cdictp_entry["kg_entry"]

            # Gloss of selected sentence
            st.write("---")
            st.write("Concepts and target words of the selected sentence: ")
            pgloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], kgp_entry, st.session_state["delimiters"])
            pgloss_selection =st.dataframe(pgloss, selection_mode="single-column", on_select="rerun", key="pgloss_df")
            # show sentences with the selected word if any
            if pgloss_selection["selection"]["columns"] != []:
                ptw = pgloss_selection["selection"]["columns"][0].split("_")[0]
                pkg_entries_with_word = kgu.get_sentences_with_word(st.session_state["knowledge_graph"],
                                                                   ptw,
                                                                   st.session_state["delimiters"])
                st.subheader("Sentences with '*{}*':".format(ptw))
                for pkge in pkg_entries_with_word:
                    ppgloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], pkge, st.session_state["delimiters"])
                    st.dataframe(ppgloss)















