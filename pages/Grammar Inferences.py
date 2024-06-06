import streamlit as st
import json
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import graphs_utils
from libs import utils


st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Inferential Engine")

concept_kson = json.load(open("./data/concepts.json"))

# list all conversational questionnaires
cq_folder = "./questionnaires"
cq_json_list = [f for f in listdir(cq_folder) if isfile(join(cq_folder, f)) and f.endswith(".json")]

# cq_id_dict stores cq uid: cq filename and content
cq_id_dict = {}
# {uid: {
#       "filename": cq filename,
#       "content": cq content
#       }
# }
recordings_list_dict = {}
# {recording: cq_uid}

for cq in cq_json_list:
    #load the cq json file
    cq_json = json.load(open(join(cq_folder, cq)))
    uid = cq_json["uid"]
    cq_content = json.load(open(join(cq_folder, cq)))
    cq_id_dict[uid] = {"filename": cq, "content": cq_content}

language = st.selectbox("Select a language", ["english", "french", "german", "tahitian", "mwotlap", "portuguese", "marquesan (Nuku Hiva)"])

# list all the available recordings in that language
recordings_folder = "./recordings"
# list cq folders in recordings_folder
cq_folders = listdir(recordings_folder)
if ".DS_Store" in cq_folders:
    cq_folders.remove(".DS_Store")

# in each cq folder, if the language is available, list the recordings in that language with
# associated cd uid.

for cq in cq_folders:
    if language in listdir(join(recordings_folder, cq)):
        recordings = listdir(join(recordings_folder, cq, language))
        if ".DS_Store" in recordings:
            recordings.remove(".DS_Store")
        # check if recording has an associated questionnaire using uid
        for recording in recordings:
            recording_json = json.load(open(join(recordings_folder, cq, language, recording)))
            cq_uid = recording_json["cq_uid"]
            #print("cq_uid: ", cq_uid)
            if cq_uid in cq_id_dict.keys():
                recordings_list_dict[recording] = recording_json["cq_uid"]
                #print("recording {} has a corresponding questionnaire".format(recording))
            else:
                print("recording {} has no corresponding questionnaire".format(recording))
st.write("{} available recording(s) in {}. ".format(len(recordings_list_dict), language))

#build knowledge graph
knowledge_graph = {}
index_counter = 0
for recording in recordings_list_dict.keys():
    corresponding_cq_uid = recordings_list_dict[recording]
    corresponding_cq_file = cq_id_dict[corresponding_cq_uid]["filename"]
    recording_json = json.load(open(join(recordings_folder, corresponding_cq_file[:-5], language, recording)))
    # open corresponding cq
    cq = cq_id_dict[corresponding_cq_uid]["content"]
    for item in cq["dialog"]:
        if cq["dialog"][item]["speaker"] == "A":
            speaker = "A"
            listener = "B"
        else:
            speaker = "B"
            listener = "A"
        try:
            if cq["dialog"][item]["text"] == recording_json["data"][item]["cq"]:
                knowledge_graph[index_counter] = {
                    "speaker_gender": cq["speakers"][speaker]["gender"],
                    "speaker_age": cq["speakers"][speaker]["age"],
                    "listener_gender": cq["speakers"][listener]["gender"],
                    "listener_age": cq["speakers"][listener]["age"],
                    "sentence_data": cq["dialog"][item],
                    "recording_data": recording_json["data"][item]
                }
                index_counter += 1
            else:
                print("Error: cq text and recording text do not match for sentence {}".format(cq["dialog"][item]["text"]))
                st.write("Error: cq text and recording text do not match for sentence {}".format(cq["dialog"][item]["text"]))
        except KeyError:
            print("Warning: sentence #{}:{} of cq {} not found in recording".format(item, cq["dialog"][item]["text"], recording))

#save knowledge graph
with open("./data/knowledge/knowledge_graph"+language+".json", "w") as f:
    json.dump(knowledge_graph, f)
st.success("Knowledge graph built and saved in ./data/knowledge/knowledge_graph"+language+"_"+str(int(time.time()))+".json")
st.write("Knowledge graph contains {} sentences".format(len(knowledge_graph)))

#build statistics on target language



# #focus = st.selectbox("Select a grammatical focus", ["expression of intents"])
# focus = "intent"
# # list intents
# intent_list = graphs_utils.get_leaves_from_node(concept_kson, "INTENT")








