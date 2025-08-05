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
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import graphs_utils
from libs import utils, stats, wals_utils as wu
from random import randint
from libs import output_generation_utils as ogu
from io import BytesIO

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

delimiters = json.load(open("./data/delimiters.json"))
delimiters_bank = [
    " ",
    ".",
    "?",
    "!",
    ",",
    "·",
    "‧",
    "․",
    "-",
    "_",
    "‿",
    "、",
    "。",
    "።",
    ":",
    ";",
    "؟",
    "٬",
    "؛",
    "۔",
    "।",
    "॥",
    "𐩖",
    "𐑀",
    "་",
    "᭞",
    "᠂",
    "᠃",
    " ",
    "꓿",
    "፡",
    "'",
    "…",
    "–",
    "—"
]
key_counter = 0

questionnaires_folder = "./questionnaires"
# cq_list is the list of json files in the questionnaires folder
cq_list = [f for f in listdir(questionnaires_folder) if isfile(join(questionnaires_folder, f)) and f.endswith(".json")]

concepts_kson = json.load(open("./data/concepts.json"))
available_pivot_languages = list(wu.language_pk_id_by_name.keys())
questionnaires_folder = "./questionnaires"

if "concepts" not in st.session_state:
    with open("./data/concepts.json", "r") as f:
        st.session_state["concepts"] = json.load(f)
if "predicates_list" not in st.session_state:
    st.session_state["predicates_list"] = graphs_utils.get_leaves_from_node(st.session_state["concepts"], "PREDICATE")
if "current_cq" not in st.session_state:
    st.session_state["current_cq"] = cq_list[0]
if "cq_is_chosen" not in st.session_state:
    st.session_state["cq_is_chosen"] = False
if "current_sentence_number" not in st.session_state:
    st.session_state["current_sentence_number"] = 1
if "available_target_languages" not in st.session_state:
    st.session_state["available_target_languages"] = list(wu.language_pk_id_by_name.keys())
if "target_language" not in st.session_state:
    st.session_state["target_language"] = st.session_state["available_target_languages"][0]
if "delimiters" not in st.session_state:
    st.session_state["delimiters"] = delimiters["English"]
if "pivot_language" not in st.session_state:
    st.session_state["pivot_language"] = "English"
if "counter" not in st.session_state:
    st.session_state["counter"] = 1
if "recording" not in st.session_state:
    st.session_state["recording"] = {"target language": st.session_state["target_language"],
                                     "delimiters": st.session_state["delimiters"],
                                     "pivot language": "English", "cq_uid": "xxx", "data": {},
                                     "interviewer": "", "interviewee": ""}
if "loaded_existing_transcription" not in st.session_state:
    st.session_state["loaded_existing_transcription"] = False
if "existing_filename" not in st.session_state:
    st.session_state["existing_filename"] = ""
if "cq_id_dict" not in st.session_state:
    cq_id_dict = {}
    for cq in cq_list:
        cq_json = json.load(open(join(questionnaires_folder, cq)))
        cq_id_dict[cq_json["uid"]] = {"filename": cq, "content": cq_json}
    st.session_state["cq_id_dict"] = cq_id_dict

st.title("Enter CQ Translations")

with st.popover("information and tutorial"):
    st.markdown("""This page allows to record the transcription of Conversational Questionnaires. 
                You can either start a new transcription or continue working on a DIG4EL transcription you have on your computer. 
                ***Your inputs will not be saved on the server!*** Make sure you use the 'save' button at the bottom of the page to save the file on your computer (one per Conversational Questionnaire).
                
                The interface allows entering each segment in the target language in the 'Equivalent in ...' field.
                Once entered the equivalent of the segment in the target language, press the return key to enable the concept(s)-word(s) association. 
                This series of fields allow to match concepts expressed in the segment with word(s) in the target language, a word being a sequence
                of characters between two spaces/punctuation marks. All the words contributing to a concept can be entered in each field. 
                - Fields can be left empty.
                - Multiple words from the drop-down list can be associated with a single concept.
                - The same word can be associated with several concepts.
      
                Watch the tutorial:
                """)
    st.video("https://youtu.be/QTmukcvL3fU")

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.page_link("pages/dashboard.py", label="Back to Dashboard", icon=":material/home:")

if not st.session_state["loaded_existing_transcription"]:
    with st.expander("Load an existing DIG4EL transcription"):
        existing_recording = st.file_uploader("Load an existing recording", type="json")
        if existing_recording is not None:
            st.session_state["recording"] = json.load(existing_recording)
            print("Existing recording loaded: ", existing_recording.name)
            st.session_state["existing_filename"] = existing_recording.name
            # update concept labels
            st.session_state["recording"], found_old_labels = utils.update_concept_names_in_transcription(
                st.session_state["recording"])
            if found_old_labels:
                st.write("Some concept labels have been updated to the latest version.")
            st.session_state["loaded_existing_transcription"] = True

if st.session_state["loaded_existing_transcription"]:
    default_interviewer = st.session_state["recording"]["interviewer"]
    default_interviewee = st.session_state["recording"]["interviewee"]
    default_target_language = st.session_state["recording"]["target language"]
    st.session_state["target_language"] = st.session_state["recording"]["target language"]
    if st.session_state["target_language"] not in st.session_state["available_target_languages"]:
        st.session_state["available_target_languages"].append(st.session_state["target_language"])
    try:
        default_delimiters = st.session_state["recording"]["delimiters"]
    except KeyError:
        st.session_state["recording"]["delimiters"] = delimiters["English"]
        default_delimiters = delimiters["English"]
    default_pivot_language = st.session_state["recording"]["pivot language"]
    if default_pivot_language == "english":
        default_pivot_language = "English"
        st.session_state["recording"]["pivot language"] = "English"

    default_cq_uid = st.session_state["recording"]["cq_uid"]
    default_data = st.session_state["recording"]["data"]

else:  ## if not loaded_existing_transcription
    default_target_language = "English"
    default_delimiters = delimiters["English"]
    if st.session_state["recording"]["interviewer"] == "":
        default_interviewer = ""
    else:
        default_interviewer = st.session_state["recording"]["interviewer"]
    if st.session_state["recording"]["interviewee"] == "":
        default_interviewee = ""
    else:
        default_interviewee = st.session_state["recording"]["interviewee"]
    if st.session_state["recording"]["pivot language"] == "English":
        default_pivot_language = "English"
    else:
        default_pivot_language = st.session_state["recording"]["pivot language"]
    if st.session_state["recording"]["cq_uid"] == "xxx":
        default_cq_uid = ""
    else:
        default_cq_uid = st.session_state["recording"]["cq_uid"]
    if st.session_state["recording"]["data"] == {}:
        default_data = {}
    else:
        default_data = st.session_state["recording"]["data"]

with st.expander("Start a new transcription or edit the header of an existing one"):
    st.markdown(
        """***Don't forget to save your transcription using the 'Save' button at the bottom of the page. 
    Nothing is saved on the server.***""")
    interviewer = st.text_input("Interviewer", value=default_interviewer, key="interviewer" + str(key_counter))
    key_counter += 1
    st.session_state["recording"]["interviewer"] = interviewer

    interviewee = st.text_input("Interviewee", value=default_interviewee, key="interviewee" + str(key_counter))
    key_counter += 1
    st.session_state["recording"]["interviewee"] = interviewee

    tl = st.selectbox("Choose a target language", ["not in the list"] + st.session_state["available_target_languages"],
                      index=st.session_state["available_target_languages"].index(
                          st.session_state["target_language"]) + 1)
    if tl != st.session_state["target_language"]:
        if tl == "not in the list":
            new_tl = st.text_input("Enter the name of the target language")
            if new_tl != "":
                st.session_state["target_language"] = new_tl
                st.session_state["recording"]["target language"] = new_tl
                st.session_state["available_target_languages"].append(new_tl)
                print("Target language changed to {}".format(st.session_state["target_language"]))
        else:
            st.session_state["target_language"] = tl
            st.session_state["recording"]["target language"] = tl
        st.session_state["cq_is_chosen"] = False

    st.session_state["recording"]["delimiters"] = st.multiselect("verify and edit word separators if needed",
                                                                 delimiters_bank, default=default_delimiters)
    st.session_state["delimiters"] = st.session_state["recording"]["delimiters"]
    st.write("Active delimiters: {}".format(st.session_state["recording"]["delimiters"]))

    pl = st.selectbox("Choose a pivot language", available_pivot_languages,
                      index=available_pivot_languages.index(default_pivot_language))
    if st.session_state["pivot_language"] != pl:
        st.session_state["pivot_language"] = pl
        #print("pivot language switched to {}".format(pl))
        st.session_state["recording"]["pivot language"] = pl
        st.session_state["cq_is_chosen"] = False

    if not st.session_state["loaded_existing_transcription"]:  # if starting fresh, choose a cq
        select_cq = st.selectbox("Choose a CQ", cq_list, index=cq_list.index(st.session_state["current_cq"]))
        if st.button("select CQ"):
            st.session_state["current_cq"] = select_cq
            st.session_state["cq_is_chosen"] = True
    else:  # if loaded_existing_transcription
        st.session_state["current_cq"] = st.session_state["cq_id_dict"][default_cq_uid]["filename"]
        st.session_state["cq_is_chosen"] = True

if st.session_state["cq_is_chosen"]:
    # load the json file
    cq = json.load(open(join(questionnaires_folder, st.session_state["current_cq"])))
    number_of_sentences = len(cq["dialog"])
    st.session_state["recording"]["cq_uid"] = cq["uid"]

    st.session_state["recording"]["recording_uid"] = str(int(time.time()))

    docx_file = ogu.generate_transcription_doc(cq, st.session_state["target_language"],
                                               st.session_state["pivot_language"])
    with st.sidebar:
        st.download_button(
            label="📥 Download an EMPTY transcription sheet for this CQ as .docx",
            data=docx_file,
            file_name=f'{cq["title"]}_transcription_sheet.docx',
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    colt1, colt2 = st.columns([3, 1])
    colt1.title("{}".format(cq["title"]))
    colt1.write("Context: {}".format(cq["context"]))
    with colt1.popover("See the full dialog"):
        for i in range(1, len(cq["dialog"]) + 1):
            st.write(cq["dialog"][str(i)]["speaker"] + " : " + cq["dialog"][str(i)]["text"])
    st.divider()

    counter_string = "Segment {}".format(str(st.session_state.counter))
    if "legacy index" in cq["dialog"][str(st.session_state["counter"])]:
        if cq["dialog"][str(st.session_state["counter"])]["legacy index"] != "":
            counter_string += ", legacy index {}".format(cq["dialog"][str(st.session_state["counter"])]["legacy index"])
    #st.write(st.write(f'Current position: {counter_string}.'))
    colq, colw, cole = st.columns([1, 3, 1])
    if colq.button("Previous"):
        if st.session_state["counter"] > 1:
            st.session_state["counter"] = st.session_state["counter"] - 1
            st.rerun()
    if colw.button("Current position {}".format(counter_string)):
        pass
    if cole.button("Next"):
        if st.session_state["counter"] < number_of_sentences:
            st.session_state["counter"] = st.session_state["counter"] + 1
            st.rerun()
    jump_to = colw.slider(f"Jump to segment", 1, number_of_sentences, value=st.session_state["counter"])
    if jump_to != st.session_state["counter"]:
        st.session_state["counter"] = jump_to
        st.rerun()

    colz, colx = st.columns(2, gap="large")
    colz.subheader(cq["dialog"][str(st.session_state["counter"])]["speaker"] + ' says: "' +
                   cq["dialog"][str(st.session_state["counter"])]["text"] + '"')
    # create the dialog context view on the right column
    colx.markdown("#### Local dialog context")
    start_index = max(1, st.session_state["counter"] - 2)
    stop_index = min(len(cq["dialog"]) + 1, start_index + 10)
    for i in range(start_index, stop_index):
        if i == st.session_state["counter"]:
            colx.markdown(f'**{cq["dialog"][str(i)]["speaker"] + ": " + cq["dialog"][str(i)]["text"]}**')
        else:
            colx.markdown(f'{cq["dialog"][str(i)]["speaker"] + ": " + cq["dialog"][str(i)]["text"]}')

    # a recording exists at this index
    if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
        translation_default = st.session_state["recording"]["data"][str(st.session_state["counter"])]["translation"]
        # alernate pivot
        if "alternate_pivot" in st.session_state["recording"]["data"][str(st.session_state["counter"])].keys():
            alternate_pivot_default = st.session_state["recording"]["data"][str(st.session_state["counter"])][
                "alternate_pivot"]
        else:
            st.session_state["recording"]["data"][str(st.session_state["counter"])]["alternate_pivot"] = ""
            alternate_pivot_default = ""
        # comment
        if "comment" in st.session_state["recording"]["data"][str(st.session_state["counter"])].keys():
            default_comment = st.session_state["recording"]["data"][str(st.session_state["counter"])]["comment"]
        else:
            st.session_state["recording"]["data"][str(st.session_state["counter"])]["comment"] = ""
            default_comment = ""
    # no recording at this index
    else:
        translation_default = ""
        alternate_pivot_default = ""
        default_comment = ""

    # if pivot language is not english, store the pivot form
    if st.session_state["pivot_language"] != "English":
        alternate_pivot = colz.text_input(
            "Enter here the expression you used in {}".format(st.session_state["pivot_language"],
                                                              value=alternate_pivot_default),
            value=alternate_pivot_default)
    else:
        alternate_pivot = ""

    translation_raw = colz.text_input("Equivalent in {}".format(st.session_state["target_language"]),
                                      value=translation_default,
                                      key=str(st.session_state["counter"]) + str(key_counter))
    key_counter += 1
    translation = utils.normalize_sentence(translation_raw)
    segmented_target_sentence = stats.custom_split(translation, st.session_state["recording"]["delimiters"])

    # Early sentence validation
    if colz.button("Validate sentence", key="early_validation"+str(key_counter)):
        st.session_state["recording"]["data"][str(st.session_state["counter"])] = {
            "legacy index": cq["dialog"][str(st.session_state["counter"])]["legacy index"],
            "cq": cq["dialog"][str(st.session_state["counter"])]["text"],
            "alternate_pivot": alternate_pivot,
            "translation": translation,
            "concept_words": {},
            "comment": ""
        }
        key_counter += 1

    # for each base concept, display a multiselect tool to select the word(s) that express (part of) this concept in the target language
    # the word(s) are stored as strings in the json, separated by "...", but must be a list for the multiselect tool to work.
    concept_words = {}
    colz.write(
        "In this sentence, would you know which word(s) would contribute to the expression the following concepts?")
    concept_list = cq["dialog"][str(st.session_state["counter"])]["intent"]

    # Concepts
    is_negative_polarity = False
    for concept, properties in cq["dialog"][str(st.session_state["counter"])]["graph"].items():
        if concept[-8:] == "POLARITY":
            if properties["value"] == "NEGATIVE":
                concept_list.append("Negative Polarity")
    concept_list += cq["dialog"][str(st.session_state["counter"])]["concept"]
    for concept in concept_list:
        concept_default = []
        if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
            if concept in st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"].keys():
                target_word_list = utils.listify(
                    st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"][concept])
                if all(element in segmented_target_sentence for element in target_word_list):
                    concept_default = target_word_list
        else:
            concept_default = []
        # Multiselect input. The displayed concept string is the description of the concept from concept.json
        concept_translation_list = colz.multiselect("{} : ".format(concepts_kson[concept]["description"]),
                                                    segmented_target_sentence, default=concept_default,
                                                    key=concept + str(st.session_state["counter"]) + str(key_counter))
        key_counter += 1
        concept_words[concept] = "...".join(concept_translation_list)

    # Predicate
    predicate_default = ""
    predicate_index_default = st.session_state["predicates_list"].index("PROCESSIVE PREDICATE")
    predicate_words_default = []
    if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
        # identify the predicate key in the concept_words dict
        for k in st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"]:
            if k in st.session_state["predicates_list"]:
                predicate_default = k
                predicate_index_default = st.session_state["predicates_list"].index(predicate_default)
                predicate_words_list = \
                    utils.listify(
                        st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"][k])
                if all(element in segmented_target_sentence for element in predicate_words_default):
                    predicate_words_default = predicate_words_list
                    if "" in predicate_words_list:
                        predicate_words_list.remove("")

    type_of_predicate = colz.selectbox(
        "If it makes sense, select the type of predicate used in the sentence in {}".format(
            st.session_state["target_language"]),
        st.session_state["predicates_list"],
        index=predicate_index_default)

    predicate_words = colz.multiselect("Which word(s) indicate(s) the type of predicate?",
                                       segmented_target_sentence, default=predicate_words_default,
                                       key="predicate_" + str(st.session_state["counter"]) + str(key_counter))
    concept_words[type_of_predicate] = "...".join(predicate_words)
    if type_of_predicate != predicate_default and predicate_default in concept_words.keys():
        del concept_words[predicate_default]

    # Comments
    comment = colz.text_input("Comments/Notes", value=default_comment, key="comment" + str(st.session_state["counter"]))

    # Validate Sentence
    if colz.button("Validate expression and connections"):
        st.session_state["recording"]["data"][str(st.session_state["counter"])] = {
            "legacy index": cq["dialog"][str(st.session_state["counter"])]["legacy index"],
            "cq": cq["dialog"][str(st.session_state["counter"])]["text"],
            "alternate_pivot": alternate_pivot,
            "translation": translation,
            "concept_words": concept_words,
            "comment": comment
        }
        if st.session_state["counter"] < number_of_sentences - 1:
            st.session_state["counter"] = st.session_state["counter"] + 1
            st.rerun()
        else:
            st.subheader("End of the CQ, congratulations! Click on 'Download your recording' below!")
            st.balloons()

    st.divider()
    #st.write(st.session_state["recording"])
    filename = ("recording_"
                + st.session_state["current_cq"].replace(".json", "") + "_"
                + st.session_state["target_language"] + "_"
                + st.session_state["recording"]["interviewer"] + "_"
                + st.session_state["recording"]["interviewee"] + "_"
                + str(int(time.time())) + ".json")
    colf, colg = st.columns(2)
    colf.download_button(label="**download your transcription**",
                         data=json.dumps(st.session_state["recording"], indent=4), file_name=filename)
    colf.markdown("""Downloading the transcription saves your transcription on your computer.""")
    colg.markdown("""
                Nothing is stored on the server -> **Save your work!**
                DIG4EL creates one file per questionnaire, that you can then re-load to continue working on it, or share with anyone you want.  
                  """)
