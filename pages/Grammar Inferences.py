import streamlit as st
import json
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import graphs_utils, gram_utils

if "target_language" not in st.session_state:
    st.session_state["target_language"] = "english"

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

concepts_kson = json.load(open("./data/concepts.json"))
cq_folder = "./questionnaires"
cq_list = [f for f in listdir(cq_folder) if isfile(join(cq_folder, f)) and f.endswith(".json")]
rec_folder = "./recordings"

available_languages = ["english", "french", "marquesan", "mangarevan", "mwotlap", "portuguese", "rapa", "tahitian"]

st.title("Grammar Inferences")

selected_language = st.selectbox("Choose a language", available_languages)
if selected_language != st.session_state["target_language"]:
    st.session_state["target_language"] = selected_language

st.subheader("Statistics on language")
file_list = gram_utils.get_all_recordings_filenames_for_language(st.session_state["target_language"])
st.write(file_list)

st.subheader("Pronouns")

