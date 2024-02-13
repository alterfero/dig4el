import streamlit as st
from os.path import isfile, join
from os import listdir
from libs import graphs_utils
import json
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

st.header("DIG4EL")
st.write("Digital Inferential Grammars for Endangered Languages")

# create a list of all available CQs - list all the json files in the CQs folder
#cq_json_list = [f for f in listdir(questionnaires_folder) if isfile(join(questionnaires_folder, f)) and f.endswith(".json")]
cq_json_list = ["cq_going_fishing", "cq_preparing_for_the_new_year"]

st.subheader("Available Conversational Questionnaires")
# for each CQ, show how may recordings are available
for cq in cq_json_list:
    # determine if there is a folder with the same name as the CQ in ./recordings
    if cq in listdir(recordings_folder):
        st.write("- Conversational Questionnaire **{}** has recordings".format(cq))
        available_languages = listdir(recordings_folder + "/" + cq)
        if ".DS_Store" in available_languages:
            available_languages.remove(".DS_Store")
        if available_languages is not None:
            for language in available_languages:
                # determine how many recordings are available for each language
                recordings = listdir(join(recordings_folder, cq, language))
                if ".DS_Store" in recordings:
                    recordings.remove(".DS_Store")
                st.write("{} recording(s) in {}".format(len(recordings), language))
    else:
        st.write("- Conversational Questionnaire **{}** has no recordings".format(cq))

st.subheader("Statistics on features")
feature_list = graphs_utils.get_leaves_from_node(concepts_kson, "GRAMMAR")
st.write("The grammar graph exposes {} features.".format(len(feature_list)))

st.subheader("Statistics on features elicited in each questionnaire")
elicited_features_dict = {}
for cq in cq_json_list:
    if cq + ".json" in listdir(questionnaires_folder):
        cq_json = json.load(open(join(questionnaires_folder, cq + ".json")))
        cq_feature_dict = {}
        for f in feature_list:
            cq_feature_dict[f] = 0
        for sentence in cq_json["dialog"]:
            for item in cq_json["dialog"][sentence]["graph"]:
                if cq_json["dialog"][sentence]["graph"][item]["value"] != "":
                    if cq_json["dialog"][sentence]["graph"][item]["value"] in feature_list:
                        if cq_json["dialog"][sentence]["graph"][item]["value"] in cq_feature_dict.keys():
                            cq_feature_dict[cq_json["dialog"][sentence]["graph"][item]["value"]] += 1
                        else:
                            cq_feature_dict[cq_json["dialog"][sentence]["graph"][item]["value"]] = 1

        elicited_features_dict[cq] = cq_feature_dict


elicited_features_df = pd.DataFrame.from_dict(elicited_features_dict)
# adding a total column summing each feature across all CQs
elicited_features_df["total"] = elicited_features_df.sum(axis=1)
# ordering the dataframe by the total column
elicited_features_df = elicited_features_df.sort_values(by="total", ascending=False)
st.write(elicited_features_df)


