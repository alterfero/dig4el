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

st.subheader("Statistics on Conversational Questionnaires")
# per focus: expression of...

#personal pronouns, time, intents, type of predicate, agent-patient relations, oblique relations
# browse CQs and extract general and focused statistics


cq_statistics = {}
if st.button("Compute statistics"):
    total_number_of_sentences = 0
    #initialize intent
    available_intents = graphs_utils.get_leaves_from_node(concepts_kson, "INTENT" )
    intent_statistics = {}
    for intent in available_intents:
        intent_statistics[intent] = 0
    #print("intent_statistics init ",intent_statistics)
    #initialize predicate
    available_predicates = graphs_utils.get_leaves_from_node(concepts_kson, "PREDICATE")
    predicate_statistics = {}
    for predicate in available_predicates:
        predicate_statistics[predicate] = 0
    #initialize tense
    available_tense = ["PRESENT", "PAST EVENT", "FUTURE EVENT", "NEUTRAL"]
    tense_statistics = {}
    for tense in available_tense:
        tense_statistics[tense] = 0

    for cq in cq_json_list:
        #load cq
        cq_json = json.load(open(join(questionnaires_folder, cq)))
        total_number_of_sentences += len(cq_json["dialog"])
        for sentence_key in cq_json["dialog"].keys():
            sentence_data = cq_json["dialog"][sentence_key]

            try:
                if sentence_data["intent"] != []:
                    for intent in sentence_data["intent"]:
                        if intent in available_intents:
                            intent_statistics[intent] += 1
            except KeyError:
                print("No intent field in sentence {} of cq {}".format(sentence_key, cq))

            try:
                if sentence_data["predicate"] != []:
                    for predicate in sentence_data["predicate"]:
                        if predicate in available_predicates:
                            predicate_statistics[predicate] += 1
            except KeyError:
                print("No predicate field in sentence {} of cq {}".format(sentence_key, cq))

            for node_key in sentence_data["graph"]:
                node_data = sentence_data["graph"][node_key]
                if node_data["path"] != []:
                    if node_data["path"][-1] == "EVENT TENSE":
                        if node_data["value"] == "":
                            tense_statistics["NEUTRAL"] += 1
                        else:
                            try:
                                ppf = concepts_kson[node_data["value"]]["ontological parent"]
                                tense_statistics[ppf] += 1
                            except:
                                print("ppf statistics issue: ",ppf)

    st.write("Total number of sentences: {}".format(total_number_of_sentences))

    colz, colx, colc = st.columns(3)

    #display intent df
    colz.write("Intents")
    intent_stat_df = pd.DataFrame(intent_statistics.items(), columns=["Intent", "Count"]).sort_values(by="Count", ascending=False)
    colz.write(intent_stat_df)

    #display predicate df
    colx.write("Predicates")
    predicate_stat_df = pd.DataFrame(predicate_statistics.items(), columns=["Predicate", "Count"]).sort_values(by="Count", ascending=False)
    colx.write(predicate_stat_df)

    #display tense df
    colc.write("Tenses")
    tense_stat_df = pd.DataFrame(tense_statistics.items(), columns=["Tense", "Count"]).sort_values(by="Count", ascending=False)
    colc.write(tense_stat_df)






