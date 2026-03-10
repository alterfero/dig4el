import streamlit as st
import json
from libs import knowledge_graph_utils as kgu
import pandas as pd

if "kgs" not in st.session_state:
    st.session_state["kgs"] = {}
if "cq_transcriptions" not in st.session_state:
    st.session_state["cq_transcriptions"] = {}
if "sentence_comp_dict" not in st.session_state:
    st.session_state["sentence_comp_dict"] = {}
if "concepts" not in st.session_state:
    st.session_state["concepts"] = {}
if "concept_filter" not in st.session_state:
    st.session_state["concept_filter"] = []

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
delimiters_default = [
    " ",
    ".",
    ",",
    ";",
    ":",
    "!",
    "?",
    "\u2026"
  ]

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")
    st.page_link("pages/Grammatical_Description.py", label="Generate Grammars", icon=":material/menu_book:")

    st.write("**Expert features**")
    st.page_link("pages/4_CQ_Editor.py", label="Edit CQs", icon=":material/question_exchange:")
    st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

st.markdown("## Compare CQs across languages")

cqs = st.file_uploader("Load Conversational Questionnaires' transcriptions (all at once for multiple transcriptions)",
                       type="json", accept_multiple_files=True)
delimiters = st.multiselect("Edit word separators if needed", delimiters_bank, default=delimiters_default)

if cqs is not None:
    if st.button("prepare data"):
        st.session_state["cq_transcriptions"] = []
        for cq in cqs:
            new_cq = json.load(cq)
            st.session_state["cq_transcriptions"].append(new_cq)
        st.session_state["loaded_existing"] = True
        st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))

        # organize by language
        transcriptions_by_language = {}
        for transcription in st.session_state["cq_transcriptions"]:
            if transcription["target language"] not in transcriptions_by_language.keys():
                transcriptions_by_language[transcription["target language"]] = [transcription]
            else:
                transcriptions_by_language[transcription["target language"]].append(transcription)
        # consolidate as knowledge graph
        concepts = {}
        for tl, transcriptions in transcriptions_by_language.items():
            kg, unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                transcriptions,
                tl,
                delimiters)
            st.session_state["kgs"][tl] = kg
            # feed concepts
            for entry, data in kg.items():
                for concept, tlw in data["recording_data"]["concept_words"].items():
                    if tlw != "":
                        if concept not in concepts:
                            concepts[concept] = {tl: [{"twl": tlw.partition("_")[0],
                                                       "pivot":kg[entry]["sentence_data"]["text"],
                                                       "kg_entry": entry}]}
                        elif concept in concepts and tl not in concepts[concept].keys():
                            concepts[concept][tl] = [{"twl": tlw.partition("_")[0],
                                                      "pivot":kg[entry]["sentence_data"]["text"],
                                                      "kg_entry": entry}]
                        else:
                            concepts[concept][tl].append({"twl": tlw.partition("_")[0],
                                                          "pivot":kg[entry]["sentence_data"]["text"],
                                                          "kg_entry": entry})
            st.session_state["concepts"] = concepts

        st.write("Languages: {}".format(", ".join(list(st.session_state["kgs"].keys()))))
        #st.write(st.session_state["concepts"])

st.write("Compare based on pivot sentence")
if st.session_state["kgs"] != {}:
    tmp_dict = {}
    for tl, kg in st.session_state["kgs"].items():
        for index, data in kg.items():
            pivot_text = data["sentence_data"]["text"]
            if pivot_text not in tmp_dict.keys():
                tmp_dict[pivot_text] = {tl: {"kg_index":index, "stl": data["recording_data"]["translation"]}}
            else:
                tmp_dict[pivot_text][tl] = {"kg_index":index, "stl": data["recording_data"]["translation"]}
    for sentence, data in tmp_dict.items():
        if len(data)>1:
            st.session_state["sentence_comp_dict"][sentence] = data

    # user selection
    #st.write(st.session_state["sentence_comp_dict"])
    ifilter = st.selectbox("Filter by intent (optional)", ["all intents", "ASSERT", "ORDER", "ASK", "WISH", "EXPRESS CONDITION"])
    cfilter = st.selectbox("Filter by concept (optional)", ["all concepts"] + list(st.session_state["concepts"].keys()))
    ifiltered_sentence_keys = list(st.session_state["sentence_comp_dict"].keys())
    cfiltered_sentence_keys = list(st.session_state["sentence_comp_dict"].keys())
    if ifilter != "all intents":
        ifiltered_sentence_keys = []
        for sentence, data in st.session_state["sentence_comp_dict"].items():
            l0 = list(data.keys())[0]
            if ifilter in st.session_state["kgs"][l0][data[l0]["kg_index"]]["sentence_data"]["intent"]:
                ifiltered_sentence_keys.append(sentence)
    else:
        ifiltered_sentence_keys = list(st.session_state["sentence_comp_dict"].keys())
    if cfilter != "all concepts":
        cfiltered_sentence_keys = []
        for sentence, data in st.session_state["sentence_comp_dict"].items():
            l0 = list(data.keys())[0]
            if cfilter in st.session_state["kgs"][l0][data[l0]["kg_index"]]["sentence_data"]["concept"]:
                cfiltered_sentence_keys.append(sentence)
    filtered_sentence_keys = list(set(ifiltered_sentence_keys).intersection(set(cfiltered_sentence_keys)))

    if len(filtered_sentence_keys) > 0:
        selected_sentence = st.selectbox("select sentence", filtered_sentence_keys)
        st.markdown("**{}**".format(selected_sentence))

        # result display
        for tl in st.session_state["sentence_comp_dict"][selected_sentence]:
            st.markdown("#### {}".format(tl))
            st.write(st.session_state["sentence_comp_dict"][selected_sentence][tl]["stl"])
            gloss = kgu.build_gloss_df(st.session_state["kgs"][tl],
                               st.session_state["sentence_comp_dict"][selected_sentence][tl]["kg_index"],
                               delimiters)
            st.dataframe(gloss)

# with st.expander("Compare based on concept"):
#     if st.session_state["kgs"] != {}:
#         selected_concept = st.selectbox("select concept", st.session_state["concepts"].keys())
#         for concept, tl in st.session_state["concepts"].items():


