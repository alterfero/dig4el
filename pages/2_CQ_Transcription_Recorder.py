import streamlit as st
import json
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import graphs_utils
from libs import utils, stats, wals_utils as wu

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

delimiters = json.load(open("./data/delimiters.json"))
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

questionnaires_folder = "./questionnaires"
# cq_list is the list of json files in the questionnaires folder
cq_list = [f for f in listdir(questionnaires_folder) if isfile(join(questionnaires_folder, f)) and f.endswith(".json")]

concepts_kson = json.load(open("./data/concepts.json"))
available_pivot_languages = list(wu.language_pk_id_by_name.keys())
questionnaires_folder = "./questionnaires"

if "current_cq" not in st.session_state:
    st.session_state["current_cq"] = cq_list[0]
if "cq_is_chosen" not in st.session_state:
    st.session_state["cq_is_chosen"] = False
if "current_sentence_number" not in st.session_state:
    st.session_state["current_sentence_number"] = 1
if "available_target_languages" not in st.session_state:
    st.session_state["available_target_languages"] = list(wu.language_pk_id_by_name.keys())
if "target_language" not in st.session_state:
    st.session_state["target_language"] = "English"
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


st.title("Transcription Recorder")

with st.popover("i"):
    st.markdown("""This page allows to record the transcription of Conversational Questionnaires. 
                You can either start a new transcription or continue working on a DIG4EL transcription you have on your computer. 
                ***Your inputs will not be saved on the server!*** Make sure you use the 'save' button at the bottom of the page to save the file on your computer (one per Conversational Questionnaire).
                """)

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")
    st.page_link("pages/Grammatical_Description.py", label="Generate Grammars", icon=":material/menu_book:")

    st.write("**Expert features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")
    st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

if not st.session_state["loaded_existing"]:
    with st.expander("Load an existing DIG4EL transcription"):
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
else:
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
    interviewer = st.text_input("Interviewer", value=default_interviewer, key="interviewer")
    st.session_state["recording"]["interviewer"] = interviewer

    interviewee = st.text_input("Interviewee", value=default_interviewee, key="interviewee")
    st.session_state["recording"]["interviewee"] = interviewee

    tl = st.selectbox("Choose a target language", ["not in the list"] + st.session_state["available_target_languages"],
                      index=st.session_state["available_target_languages"].index(st.session_state["target_language"])+1)
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
        st.session_state["cq_is_chosen"] = False

    st.session_state["recording"]["delimiters"] = st.multiselect("verify and edit word separators if needed", delimiters_bank, default=default_delimiters)

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

    st.title("{}".format(cq["title"]))
    st.write("Context: ", cq["context"])

    col1, col2 = st.columns(2)
    col1.subheader("Counter: {}".format(str(st.session_state.counter)))
    if "legacy index" in cq["dialog"][str(st.session_state["counter"])]:
        if cq["dialog"][str(st.session_state["counter"])]["legacy index"] != "":
            col2.subheader("Legacy index: {}".format(cq["dialog"][str(st.session_state["counter"])]["legacy index"]))
    colq, colw, cole, colr = st.columns(4)
    if colq.button("Previous"):
        if st.session_state["counter"] > 1:
            st.session_state["counter"] = st.session_state["counter"] - 1
            st.rerun()
    if colw.button("Next"):
        if st.session_state["counter"] < number_of_sentences - 1:
            st.session_state["counter"] = st.session_state["counter"] + 1
            st.rerun()
    jump_to = colq.slider("jump to", 1, number_of_sentences, value=st.session_state["counter"])
    if jump_to != st.session_state["counter"]:
        st.session_state["counter"] = jump_to
        st.rerun()


    st.subheader(cq["dialog"][str(st.session_state["counter"])]["speaker"] + " : " + cq["dialog"][str(st.session_state["counter"])]["text"])

    #a recording exists at this index
    if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
        translation_default = st.session_state["recording"]["data"][str(st.session_state["counter"])]["translation"]
        if "alternate_pivot" in st.session_state["recording"]["data"][str(st.session_state["counter"])].keys():
            alternate_pivot_default = st.session_state["recording"]["data"][str(st.session_state["counter"])][
                "alternate_pivot"]
        if "comment" in st.session_state["recording"]["data"][str(st.session_state["counter"])].keys():
            default_comment = st.session_state["recording"]["data"][str(st.session_state["counter"])]["comment"]
        else:
            st.session_state["recording"]["data"][str(st.session_state["counter"])]["alternate_pivot"] = ""
            alternate_pivot_default = ""
            default_comment = ""
    else:
        translation_default = ""
        alternate_pivot_default = ""
        default_comment = ""

    # if pivot language is not english, store the pivot form
    if st.session_state["pivot_language"] != "English":
        alternate_pivot = st.text_input(
            "Enter here the expression you used in {}".format(st.session_state["pivot_language"], value=alternate_pivot_default),
            value=alternate_pivot_default)
    else:
        alternate_pivot = ""

    translation_raw = st.text_input("Equivalent in {}".format(st.session_state["target_language"]),
                                value=translation_default, key=str(st.session_state["counter"]))
    translation = utils.normalize_sentence(translation_raw)
    segmented_target_sentence = stats.custom_split(translation, st.session_state["delimiters"])

    # for each base concept, display a multiselect tool to select the word(s) that express (part of) this concept in the target language
    # the word(s) are stored as strings in the json, separated by "...", but must be a list for the multiselect tool to work.
    concept_words = {}
    st.write(
        "In this sentence, would you know which word(s) would contribute to the expression the following concepts?")
    for concept in cq["dialog"][str(st.session_state["counter"])]["concept"]:
        concept_default = []
        if concept in concepts_kson.keys():
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
    st.write("Default comment: ",default_comment)
    comment = st.text_input("Comments/Notes", value=default_comment)

    if st.button("Validate sentence"):
        st.session_state["recording"]["data"][str(st.session_state["counter"])] = {
            "legacy index": cq["dialog"][str(st.session_state["counter"])]["legacy index"],
            "cq": cq["dialog"][str(st.session_state["counter"])]["text"],
            "alternate_pivot": alternate_pivot,
            "translation": translation,
            "concept_words": concept_words,
            "comment": comment
        }
        if st.session_state["counter"] < number_of_sentences:
            st.session_state["counter"] = st.session_state["counter"] + 1
        st.rerun()

    #st.write(st.session_state["recording"])
    filename = ("recording_"
                + st.session_state["current_cq"].replace(".json", "") + "_"
                + st.session_state["target_language"] + "_"
                + st.session_state["recording"]["interviewer"] + "_"
                + st.session_state["recording"]["interviewee"] + "_"
                + str(int(time.time())) + ".json")
    colf, colg = st.columns(2)
    colf.download_button(label="**download your recording**", data=json.dumps(st.session_state["recording"], indent=4), file_name=filename)
    colg.markdown("""
                Nothing is stored on the server -> **Save your work!**
                DIG4EL creates one file per questionnaire, that you can then re-load to continue working on it, or share with anyone you want.  
                  """)



