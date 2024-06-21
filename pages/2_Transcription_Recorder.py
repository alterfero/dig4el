import streamlit as st
import json
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import graphs_utils
from libs import utils, stats

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

delimiters = {
    "french": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "english": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "marquesan (Nuku Hiva)": [" ", ".", ",", ";", ":", "!", "?", "…"]
}

questionnaires_folder = "./questionnaires"
# cq_list is the list of json files in the questionnaires folder
cq_list = [f for f in listdir(questionnaires_folder) if isfile(join(questionnaires_folder, f)) and f.endswith(".json")]

concepts_kson = json.load(open("./data/concepts.json"))
available_target_languages = ["french", "marquesan (Nuku Hiva)"]
available_pivot_languages = ["english", "french"]
questionnaires_folder = "./questionnaires"

if "current_cq" not in st.session_state:
    st.session_state["current_cq"] = cq_list[0]
if "cq_is_chosen" not in st.session_state:
    st.session_state["cq_is_chosen"] = False
if "current_sentence_number" not in st.session_state:
    st.session_state["current_sentence_number"] = 1
if "target_language" not in st.session_state:
    st.session_state["target_language"] = "marquesan (Nuku Hiva)"
if "pivot_language" not in st.session_state:
    st.session_state["pivot_language"] = "english"
if "counter" not in st.session_state:
    st.session_state["counter"] = 1
if "recording" not in st.session_state:
    st.session_state["recording"] = {"target language": st.session_state["target_language"],
                                     "pivot language": "english", "cq_uid": "xxx", "data": {},
                                     "interviewer": "", "interviewee": ""}
if "loaded_existing" not in st.session_state:
    st.session_state["loaded_existing"] = False
if "existing_filename" not in st.session_state:
    st.session_state["existing_filename"] = ""
if "cq_id_dict" not in st.session_state:
    cq_id_dict = {}
    for cq in cq_list:
        cq_json = json.load(open(join(questionnaires_folder, cq)))
        cq_id_dict[cq_json["uid"]] = {"filename": cq, "content": cq_json}
    st.session_state["cq_id_dict"] = cq_id_dict


st.title("CQ Recorder")

st.write("You can start a new recording right away, or load an existing one to edit it")
if not st.session_state["loaded_existing"]:
    with st.expander("Load recording"):
        existing_recording = st.file_uploader("Load an existing recording", type="json")
        if existing_recording is not None:
            st.session_state["recording"] = json.load(existing_recording)
            print("Existing recording loaded: ", existing_recording.name)
            st.session_state["existing_filename"] = existing_recording.name
            st.session_state["loaded_existing"] = True

if st.session_state["loaded_existing"]:
    default_interviewer = st.session_state["recording"]["interviewer"]
    default_interviewee = st.session_state["recording"]["interviewee"]
    default_target_language = st.session_state["recording"]["target language"]
    default_pivot_language = st.session_state["recording"]["pivot language"]
    default_cq_uid = st.session_state["recording"]["cq_uid"]
    default_data = st.session_state["recording"]["data"]
else:
    if st.session_state["recording"]["interviewer"] == "":
        default_interviewer = ""
    else:
        default_interviewer = st.session_state["recording"]["interviewer"]
    if st.session_state["recording"]["interviewee"] == "":
        default_interviewee = ""
    else:
        default_interviewee = st.session_state["recording"]["interviewee"]
    if st.session_state["recording"]["target language"] == "english":
        default_target_language = "english"
    else:
        default_target_language = st.session_state["recording"]["target language"]
    if st.session_state["recording"]["pivot language"] == "english":
        default_pivot_language = "english"
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

with st.expander("Parameters"):
    interviewer = st.text_input("Interviewer", value=default_interviewer, key="interviewer")
    st.session_state["recording"]["interviewer"] = interviewer

    interviewee = st.text_input("Interviewee", value=default_interviewee, key="interviewee")
    st.session_state["recording"]["interviewee"] = interviewee

    tl = st.selectbox("Choose a target language", available_target_languages, index=available_target_languages.index(default_target_language))
    if st.session_state["target_language"] != tl:
        st.session_state["target_language"] = tl
        st.session_state["cq_is_chosen"] = False

    pl = st.selectbox("Choose a pivot language", available_pivot_languages,
                      index=available_pivot_languages.index(default_pivot_language))
    if st.session_state["pivot_language"] != pl:
        st.session_state["pivot_language"] = pl
        #print("pivot language switched to {}".format(pl))
        st.session_state["recording"]["pivot language"] = pl
        st.session_state["cq_is_chosen"] = False

    if not st.session_state["loaded_existing"]:
        select_cq = st.selectbox("Choose a CQ", cq_list, index=cq_list.index(st.session_state["current_cq"]))
        if st.button("select CQ"):
            st.session_state["current_cq"] = select_cq
            st.session_state["cq_is_chosen"] = True
    else:
        st.session_state["current_cq"] = st.session_state["cq_id_dict"][default_cq_uid]["filename"]
        st.session_state["cq_is_chosen"] = True

if st.session_state["cq_is_chosen"]:
    # load the json file
    cq = json.load(open(join(questionnaires_folder, st.session_state["current_cq"])))
    number_of_sentences = len(cq["dialog"])
    st.session_state["recording"]["cq_uid"] = cq["uid"]

    st.session_state["recording"]["recording_uid"] = str(int(time.time()))

    st.title("Title: {}".format(cq["title"]))
    st.write("Context: ", cq["context"])

    colq, colw, cole = st.columns(3)
    if colq.button("Previous"):
        if st.session_state["counter"] > 1:
            st.session_state["counter"] = st.session_state["counter"] - 1
            st.rerun()
    colw.subheader("Sentence #" + str(st.session_state.counter))
    if cole.button("Next"):
        if st.session_state["counter"] < number_of_sentences:
            st.session_state["counter"] = st.session_state["counter"] + 1
            st.rerun()

    st.subheader(cq["dialog"][str(st.session_state["counter"])]["speaker"] + " : " + cq["dialog"][str(st.session_state["counter"])]["text"])

    #a recording exists at this index
    if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
        translation_default = st.session_state["recording"]["data"][str(st.session_state["counter"])]["translation"]
        if "alternate_pivot" in st.session_state["recording"]["data"][str(st.session_state["counter"])].keys():
            alternate_pivot_default = st.session_state["recording"]["data"][str(st.session_state["counter"])][
                "alternate_pivot"]
        else:
            st.session_state["recording"]["data"][str(st.session_state["counter"])]["alternate_pivot"] = ""
            alternate_pivot_default = ""
    else:
        translation_default = ""
        alternate_pivot_default = ""

    # if pivot language is not english, store the pivot form
    if st.session_state["pivot_language"] != "english":
        alternate_pivot = st.text_input(
            "Enter here the expression you used in {}".format(st.session_state["pivot_language"]),
            value=alternate_pivot_default)
    else:
        alternate_pivot = ""

    translation_raw = st.text_input("Equivalent in {}".format(st.session_state["target_language"]),
                                value=translation_default, key=str(st.session_state["counter"]))
    translation = utils.normalize_sentence(translation_raw)
    segmented_target_sentence = stats.custom_split(translation, delimiters[st.session_state["target_language"]])

    # for each base concept, display a multiselect tool to select the word(s) that express (part of) this concept in the target language
    # the word(s) are stored as strings in the json, separated by "...", but must be a list for the multiselect tool to work.
    concept_words = {}
    for concept in cq["dialog"][str(st.session_state["counter"])]["concept"]:
        concept_default = []
        if concept in concepts_kson.keys():
            st.write("In this sentence, would you know which word(s) would contribute to the expression the following concepts?")
            if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
                if concept in st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"].keys():
                    target_word_list = utils.listify(st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"][concept])
                    if all(element in segmented_target_sentence for element in target_word_list):
                        concept_default = target_word_list
                else:
                    st.write("concept {} is in the CQ but not in this recording, it will be ignored".format(concept))
            else:
                concept_default = []
            concept_translation_list = st.multiselect("{} : ".format(concept), segmented_target_sentence, default=concept_default, key=concept+str(st.session_state["counter"]))
            concept_words[concept] = "...".join(concept_translation_list)
        else:
            st.write("Concept {} not found in the concept graph".format(concept))

    if st.button("Validate sentence"):
        st.session_state["recording"]["data"][str(st.session_state["counter"])] = {
            "cq": cq["dialog"][str(st.session_state["counter"])]["text"],
            "alternate_pivot": alternate_pivot,
            "translation": translation,
            "concept_words": concept_words
        }
        if st.session_state["counter"] < number_of_sentences:
            st.session_state["counter"] = st.session_state["counter"] + 1
        st.rerun()

    st.write(st.session_state["recording"])
    filename = ("recording_"
                + st.session_state["current_cq"].replace(".json", "") + "_"
                + st.session_state["target_language"] + "_"
                + st.session_state["recording"]["interviewer"] + "_"
                + st.session_state["recording"]["interviewee"] + "_"
                + str(int(time.time())) + ".json")
    st.download_button(label="download your recording", data=json.dumps(st.session_state["recording"], indent=4), file_name=filename)

            # LOCAL SAVING
            # if there is no folder with the name of the cq in the recordings folder, create it
            # cq_folder_name = st.session_state["current_cq"].replace(".json", "")
            # if cq_folder_name not in listdir("./recordings"):
            #     mkdir("./recordings/" + cq_folder_name)
            # #if there is no folder with the name of the target language in the cq folder, create it
            # if st.session_state["target_language"] not in listdir("./recordings/" + cq_folder_name):
            #     mkdir("./recordings/" + cq_folder_name + "/" + st.session_state["target_language"])
            #
            # if st.session_state["loaded_existing"]:
            #     filename = ("./recordings/" + cq_folder_name + "/" + st.session_state["target_language"] + "/" +
            #                 st.session_state["existing_filename"])
            # else:
            #     filename = ("./recordings/" + cq_folder_name + "/" + st.session_state["target_language"] + "/" + "recording_"
            #                 + st.session_state["current_cq"].replace(".json", "") + "_"
            #                 + st.session_state["target_language"] + "_"
            #                 + st.session_state["recording"]["interviewer"] + "_"
            #                 + st.session_state["recording"]["interviewee"] + "_"
            #                 + str(int(time.time()))
            #                 + ".json")
            # json.dump(st.session_state["recording"], open(filename, "w"))
            # st.success("Recording saved as {}".format(filename))


