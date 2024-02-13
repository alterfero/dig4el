import streamlit as st
import json
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import graphs_utils

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("CQ Recorder")

questionnaires_folder = "./questionnaires"
# cq_list is the list of json files in the questionnaires folder
cq_list = [f for f in listdir(questionnaires_folder) if isfile(join(questionnaires_folder, f)) and f.endswith(".json")]

concepts_kson = json.load(open("./data/concepts.json"))
intents_kson = json.load(open("./data/intents.json"))

if "current_cq" not in st.session_state:
    st.session_state["current_cq"] = cq_list[0]
if "cq_is_chosen" not in st.session_state:
    st.session_state["cq_is_chosen"] = False
if "current_sentence_number" not in st.session_state:
    st.session_state["current_sentence_number"] = 1
if "target_language" not in st.session_state:
    st.session_state["target_language"] = "English"
if "counter" not in st.session_state:
    st.session_state["counter"] = 1
if "recording" not in st.session_state:
    st.session_state["recording"] = {"target language": st.session_state["target_language"],
                                     "pivot language": "English", "cq_uid": "xxx", "data": {}}

questionnaires_folder = "./questionnaires"
# cq_list is the list of json files in the questionnaires folder
cq_list = [f for f in listdir(questionnaires_folder) if isfile(join(questionnaires_folder, f)) and f.endswith(".json")]

recording = {"target language": st.session_state["target_language"], "pivot language": "English", "data": {}}

interviewer = st.text_input("Interviewer", key="interviewer")
st.session_state["recording"]["interviewer"] = interviewer

interviewee = st.text_input("Interviewee", key="interviewee")
st.session_state["recording"]["interviewee"] = interviewee

tl = st.selectbox("Choose a target language", ["english", "french", "german", "tahitian", "mwotlap", "portuguese"])
if st.session_state["target_language"] != tl:
    st.session_state["target_language"] = tl
    st.session_state["cq_is_chosen"] = False

select_cq = st.selectbox("Choose a CQ", cq_list, index=cq_list.index(st.session_state["current_cq"]))
if st.button("select CQ"):
    st.session_state["current_cq"] = select_cq
    st.session_state["cq_is_chosen"] = True

if st.session_state["cq_is_chosen"]:
    # load the json file
    cq = json.load(open(join(questionnaires_folder, st.session_state["current_cq"])))
    number_of_sentences = len(cq["dialog"])
    st.session_state["recording"]["cq_uid"] = cq["uid"]

    recording["cq_uid"] = cq["uid"]
    recording["recording_uid"] = str(int(time.time()))

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
    if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
        translation_default = st.session_state["recording"]["data"][str(st.session_state["counter"])]["translation"]
    else:
        translation_default = ""
    st.write(translation_default)
    translation = st.text_input("Equivalent in {}".format(st.session_state["target_language"]),
                                value=translation_default, key=str(st.session_state["counter"]))

    # for each base concept, display a text box to enter the word in the target language
    concept_words = {}
    for concept in cq["dialog"][str(st.session_state["counter"])]["concept"]:
        if concept in concepts_kson.keys():
            st.write("In this sentence, would you know which word would point to the following concepts?")
            if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
                if concept in st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"].keys():
                    concept_default = st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"][concept]
            else:
                concept_default = ""
            concept_translation = st.text_input("{} : ".format(concept), value=concept_default, key=concept+str(st.session_state["counter"]))
            concept_words[concept] = concept_translation

    if st.button("Validate sentence"):
        st.session_state["recording"]["data"][str(st.session_state["counter"])] = {
            "cq": cq["dialog"][str(st.session_state["counter"])],
            "translation": translation,
            "concept_words": concept_words
        }
        if st.session_state["counter"] < number_of_sentences:
            st.session_state["counter"] = st.session_state["counter"] + 1
        st.rerun()

    if st.button("Save Recording"):
        #if there is no folder with the name of the cq in the recordings folder, create it
        cq_folder_name = st.session_state["current_cq"].replace(".json", "")
        if cq_folder_name not in listdir("./recordings"):
            mkdir("./recordings/" + cq_folder_name)
        #if there is no folder with the name of the target language in the cq folder, create it
        if st.session_state["target_language"] not in listdir("./recordings/" + cq_folder_name):
            mkdir("./recordings/" + cq_folder_name + "/" + st.session_state["target_language"])

        filename = ("./recordings/" + cq_folder_name + "/" + st.session_state["target_language"] + "/" + "recording_"
                    + st.session_state["current_cq"].replace(".json", "") + "_"
                    + st.session_state["target_language"] + "_"
                    + st.session_state["recording"]["interviewer"] + "_"
                    + st.session_state["recording"]["interviewee"] + "_"
                    + str(int(time.time()))
                    + ".json")
        with open(filename, "w") as outfile:
            json.dump(st.session_state["recording"], outfile)
        st.success("Recording saved as {}".format(filename))

    st.subheader("Details on sentence")

    base_concepts = cq["dialog"][str(st.session_state["counter"])]["concept"]
    for node in cq["dialog"][str(st.session_state["counter"])]["graph"].keys():
        node_value = cq["dialog"][str(st.session_state["counter"])]["graph"][node]["value"]
        if node_value != "":
            st.write("Elicits {}, from {}".format(node_value, cq["dialog"][str(st.session_state["counter"])]["graph"][node]["is_required_by"]))
        elif node in concepts_kson.keys() and concepts_kson[node]["ontological parent"] == "TRANSFORMATION":
            st.write("Transformation: {}".format(node))

    #st.write(st.session_state["recording"])



