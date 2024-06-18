import streamlit as st
from os.path import isfile, join
from os import listdir
from libs import graphs_utils
import json
from libs import graphs_utils
import pandas as pd

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

questionnaires_folder = "./questionnaires"
recordings_folder = "./recordings"
concepts_kson = json.load(open("./data/concepts.json"))
cq_json_list = [f for f in listdir(questionnaires_folder) if isfile(join(questionnaires_folder, f)) and f.endswith(".json")]

st.header("DIG4EL")
st.write("Digital Inferential Grammars for Endangered Languages")

# create a list of all available CQs - list all the json files in the CQs folder

with st.expander("Available Conversational Questionnaires"):
    # for each CQ, show how may recordings are available
    for cq in cq_json_list:
        # determine if there is a folder with the same name as the CQ in ./recordings
        if cq[:-5] in listdir(recordings_folder):
            st.write("- Conversational Questionnaire **{}** has recordings:".format(cq[:-5]))
            available_languages = listdir(recordings_folder + "/" + cq[:-5])
            if ".DS_Store" in available_languages:
                available_languages.remove(".DS_Store")
            if available_languages is not None:
                for language in available_languages:
                    # determine how many recordings are available for each language
                    recordings = listdir(join(recordings_folder, cq[:-5], language))
                    if ".DS_Store" in recordings:
                        recordings.remove(".DS_Store")
                    st.write("{} recording(s) in {}".format(len(recordings), language))
        else:
            st.write("- {} does not have recordings yet".format(cq[:-5]))

with st.expander("Statistics on concept graph"):
    n_nodes = len(concepts_kson.keys())
    n_leaves = len(graphs_utils.get_all_leaves(concepts_kson))
    st.write("{} nodes, among which {} leaves".format(n_nodes, n_leaves))


