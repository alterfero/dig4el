import streamlit as st
import json
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import graphs_utils, knowledge_graph_utils as kgu
from libs import utils
from libs import stats
import pandas as pd


st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "knowledge_graph" not in st.session_state:
    st.session_state["knowledge_graph"] = {}

st.title("Inferential Engine")

concept_kson = json.load(open("./data/concepts.json"))

delimiters = {
    "french": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "english": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "marquesan (Nuku Hiva)": [" ", ".", ",", ";", ":", "!", "?", "…"]
}

language = st.selectbox("Select a language", [ "marquesan (Nuku Hiva)", "english", "french"], index=0)
if st.button("compute knowledge graph for {}".format(language)):
    st.session_state["knowledge_graph"], unique_words, unique_words_frequency, total_target_word_count = kgu.build_knowledge_graph(language)

# # list all conversational questionnaires
# cq_folder = "./questionnaires"
# cq_json_list = [f for f in listdir(cq_folder) if isfile(join(cq_folder, f)) and f.endswith(".json")]
#
# # cq_id_dict stores cq uid: cq filename and content
# cq_id_dict = {}
# # {uid: {
# #       "filename": cq filename,
# #       "content": cq content
# #       }
# # }
# recordings_list_dict = {}
# # {recording: cq_uid}
#
# for cq in cq_json_list:
#     #load the cq json file
#     cq_json = json.load(open(join(cq_folder, cq)))
#     uid = cq_json["uid"]
#     cq_content = json.load(open(join(cq_folder, cq)))
#     cq_id_dict[uid] = {"filename": cq, "content": cq_content}
#
# language = st.selectbox("Select a language", ["english", "french", "german", "tahitian", "mwotlap", "portuguese", "marquesan (Nuku Hiva)"])
#
# # list all the available recordings in that language
# recordings_folder = "./recordings"
# # list cq folders in recordings_folder
# cq_folders = listdir(recordings_folder)
# if ".DS_Store" in cq_folders:
#     cq_folders.remove(".DS_Store")
#
# # in each cq folder, if the language is available, list the recordings in that language with
# # associated cd uid.
#
# for cq in cq_folders:
#     if language in listdir(join(recordings_folder, cq)):
#         recordings = listdir(join(recordings_folder, cq, language))
#         if ".DS_Store" in recordings:
#             recordings.remove(".DS_Store")
#         # check if recording has an associated questionnaire using uid
#         for recording in recordings:
#             recording_json = json.load(open(join(recordings_folder, cq, language, recording)))
#             cq_uid = recording_json["cq_uid"]
#             #print("cq_uid: ", cq_uid)
#             if cq_uid in cq_id_dict.keys():
#                 recordings_list_dict[recording] = recording_json["cq_uid"]
#                 #print("recording {} has a corresponding questionnaire".format(recording))
#             else:
#                 print("recording {} has no corresponding questionnaire".format(recording))
# st.write("{} available recording(s) in {}. ".format(len(recordings_list_dict), language))
#
# #build knowledge graph ======================================================================================
# knowledge_graph = {}
# knowledge_graph["language"] = language
# unique_words = []
# unique_words_frequency = {}
# total_target_word_count = 0
# index_counter = 0
# for recording in recordings_list_dict.keys():
#     corresponding_cq_uid = recordings_list_dict[recording]
#     corresponding_cq_file = cq_id_dict[corresponding_cq_uid]["filename"]
#     recording_json = json.load(open(join(recordings_folder, corresponding_cq_file[:-5], language, recording)))
#     # open corresponding cq
#     cq = cq_id_dict[corresponding_cq_uid]["content"]
#     for item in cq["dialog"]:
#         if cq["dialog"][item]["speaker"] == "A":
#             speaker = "A"
#             listener = "B"
#         else:
#             speaker = "B"
#             listener = "A"
#         try:
#             if cq["dialog"][item]["text"] == recording_json["data"][item]["cq"]:
#                 knowledge_graph[index_counter] = {
#                     "speaker_gender": cq["speakers"][speaker]["gender"],
#                     "speaker_age": cq["speakers"][speaker]["age"],
#                     "listener_gender": cq["speakers"][listener]["gender"],
#                     "listener_age": cq["speakers"][listener]["age"],
#                     "sentence_data": cq["dialog"][item],
#                     "recording_data": recording_json["data"][item]
#                 }
#                 index_counter += 1
#                 total_target_word_count += len(recording_json["data"][item]["translation"].split())
#                 for word in recording_json["data"][item]["translation"].split():
#                     if word in unique_words_frequency:
#                         unique_words_frequency[word] += 1000/total_target_word_count
#                     else:
#                         unique_words_frequency[word] = 1000/total_target_word_count
#                         unique_words.append(word)
#
#             else:
#                 print("BUILD KNOWLEDGE GRAPH: cq {} <========> recording {} don't match".format(cq["dialog"][item]["text"], recording_json["data"][item]["cq"]))
#                 #st.write("Error: cq {} <========> recording {} don't match".format(cq["dialog"][item]["text"], recording_json["data"][item]["cq"]))
#         except KeyError:
#             print("Warning: sentence #{}:{} of cq {} not found in recording".format(item, cq["dialog"][item]["text"], recording))
#
# #save knowledge graph
# with open("./data/knowledge/knowledge_graph"+language+".json", "w") as f:
#     json.dump(knowledge_graph, f)
# st.success("Knowledge graph built and saved in ./data/knowledge/knowledge_graph"+language+"_"+str(int(time.time()))+".json")

#build statistics on target language
if st.button("compute statistics on {}".format(language)):
    if st.session_state["knowledge_graph"] != {}:
        st.subheader("Blind word statistics")
        blind_word_stats = stats.build_blind_word_stats_from_knowledge_graph(st.session_state["knowledge_graph"], delimiters[language])
        st.write("Knowledge graph contains {} sentences, {} words with {} unique words"
                 .format(len(st.session_state["knowledge_graph"]), total_target_word_count, len(unique_words)))
        colo, colp = st.columns(2)
        colo.metric("Type-Token Ratio (TTR)", str(round(len(unique_words)*100/total_target_word_count))+"%", "Percentage of unique words in the target language")
        with colo.popover("i"):
            st.markdown("TTR is the percentage of unique words in the target language. "
                        "Low TTR indicates a high repetition of words in the language, potentially indicating an isolating language."
                        "High TTR ratio indicates a low repetition of words, potentially indicating an inflective language")
        blind_entropy = stats.compute_average_blind_entropy(blind_word_stats)
        colp.metric("Average blind entropy", str(round(blind_entropy*100))+"%", "Overall unpredictability of word sequences")
        with colp.popover("i"):
            st.markdown("The average language entropy gives us an estimate of the overall unpredictability of word sequences in a given language. "
                        "It reflects how much information is needed, on average, to predict the next word in a sentence "
                        "based on the preceding and following words."
                        "Blind entropy does not use information from the knowledge graph, only the target language data.")
            st.markdown("Higher entropy indicates more unpredictability, meaning each word could be followed or preceded by a larger variety of words.")


        st.subheader("Grammar exploration")
        # let the user choose a grammaricalized concept to examine
        value_loc_dict = {}
        value_count_dict = {}
        available_f = ["INTENT", "PREDICATE", "EVENT TENSE", "POLARITY", "PERSONAL DEICTIC", "ASPECT"]
        selected_f = st.selectbox("Choose a concept to explore", available_f)
        f_values = graphs_utils.get_leaves_from_node(concept_kson, selected_f)
        st.write("Values: {}".format(f_values))

        # stats on values and their locations in the knowledge graph: value_loc_dict
        if selected_f in ["INTENT", "PREDICATE"]:
            print("Selected {}".format(selected_f))
            f = selected_f.lower()
            for v in f_values:
                value_loc_dict[v] = []
            value_loc_dict["neutral"] = []
            for entry_key in st.session_state["knowledge_graph"]:
                if f in st.session_state["knowledge_graph"][entry_key]["sentence_data"].keys():
                    local_value_list = knowledge_graph[entry_key]["sentence_data"][f]
                    for local_value in local_value_list:
                        if local_value in value_loc_dict:
                            value_loc_dict[local_value].append(entry_key)
                        else:
                            print("Stats on values: Unknown value {} in entry {}".format(local_value, entry_key))
                else:
                    print("{} absent of entry {} in knowledge graph".format(f, entry_key))
            for item in value_loc_dict:
                value_count_dict[item] = len(value_loc_dict[item])
            # build sorted df
            value_count_df = pd.DataFrame.from_dict(value_count_dict, orient="index", columns=["count"]).sort_values(by="count", ascending=False)
            st.write(value_count_df)

        elif selected_f in ["PERSONAL DEICTIC"]:
            print("Selected {}".format(selected_f))
            for v in f_values:
                value_loc_dict[v + " AGENT"] = []
                value_loc_dict[v + " PATIENT"] = []
                value_loc_dict[v + " POSSESSOR"] = []
                value_loc_dict[v + " OTHER"] = []
            for entry_key in st.session_state["knowledge_graph"]:
                for graph_key in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"]:
                    if "value" in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]:
                        if st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["value"] in f_values:
                            local_value = knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key]["value"]
                            # semantic role
                            if "AGENT" in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["path"]:
                                value_loc_dict[local_value + " AGENT"].append(entry_key)
                            elif "PATIENT" in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["path"]:
                                value_loc_dict[local_value + " PATIENT"].append(entry_key)
                            elif "POSSESSOR" in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["path"]:
                                value_loc_dict[local_value + " POSSESSOR"].append(entry_key)
                            else:
                                value_loc_dict[local_value + " OTHER"].append(entry_key)
            for item in value_loc_dict:
                value_count_dict[item] = len(value_loc_dict[item])
            # build sorted df
            value_count_df = pd.DataFrame.from_dict(value_count_dict, orient="index", columns=["count"]).sort_values(by="count",
                                                                                                                     ascending=False)
            st.write(value_count_df)
        else:
            print("Selected {}".format(selected_f))
            for v in f_values:
                value_loc_dict[v] = []
            value_loc_dict["neutral"] = []
            for entry_key in st.session_state["knowledge_graph"]:
                for graph_key in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"]:
                    if selected_f in graph_key:
                        if "value" in  st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]:
                            if st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["value"] in f_values:
                                (value_loc_dict[st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["value"]]
                                 .append((entry_key)))
                            else:
                                value_loc_dict["neutral"].append(entry_key)
            for item in value_loc_dict:
                value_count_dict[item] = len(value_loc_dict[item])
            # build sorted df
            value_count_df = pd.DataFrame.from_dict(value_count_dict, orient="index", columns=["count"]).sort_values(by="count",
                                                                                                                     ascending=False)
            st.write(value_count_df)

        # statistical inferences on the way the target language expresses the selected value
        # assumption for now: A value is expressed by one or several words in the sentence.
        # first method is to compare the frequency of each word in sentences where the value is present versus those where it is not.
        for v_focus in value_loc_dict:
            v_focus_sentences = value_loc_dict[v_focus]
            v_not_focus_sentences = []
            for v in value_loc_dict:
                if v != v_focus:
                    v_not_focus_sentences += value_loc_dict[v]
            v_focus_words = []
            v_not_focus_words = []
            for v_focus_sentence in v_focus_sentences:
                v_focus_words += stats.custom_split(st.session_state["knowledge_graph"][v_focus_sentence]["recording_data"]["translation"], delimiters[language])
            for v_not_focus_sentence in v_not_focus_sentences:
                v_not_focus_words += stats.custom_split(st.session_state["knowledge_graph"][v_not_focus_sentence]["recording_data"]["translation"], delimiters[language])
            v_focus_words_count = {}
            for word in v_focus_words:
                if word in v_focus_words_count:
                    v_focus_words_count[word] += 1
                else:
                    v_focus_words_count[word] = 1
            v_not_focus_words_count = {}
            for word in v_not_focus_words:
                if word in v_not_focus_words_count:
                    v_not_focus_words_count[word] += 1
                else:
                    v_not_focus_words_count[word] = 1

            v_focus_word_frequency = {}
            for word in v_focus_words_count:
                v_focus_word_frequency[word] = v_focus_words_count[word]*1000/total_target_word_count
            v_not_focus_word_frequency = {}
            for word in v_not_focus_words_count:
                v_not_focus_word_frequency[word] = v_not_focus_words_count[word]*1000/total_target_word_count

            # diff frequencies between v and not v
            v_focus_word_diff_frequency_v_not_v = {}
            for word in v_focus_word_frequency:
                if word in v_not_focus_word_frequency:
                    v_focus_word_diff_frequency_v_not_v[word] = v_focus_word_frequency[word] - v_not_focus_word_frequency[word]
                else:
                    v_focus_word_diff_frequency_v_not_v[word] = v_focus_word_frequency[word]


            v_focus_word_diff_frequency_v_not_v_df = pd.DataFrame.from_dict(v_focus_word_diff_frequency_v_not_v, orient="index", columns=["frequency"]).sort_values(by="frequency", ascending=False)
            st.write("Diff frequency between v and not v in sentences where {} is present".format(v_focus))
            st.write(v_focus_word_diff_frequency_v_not_v_df)

        # the value expresses itself with words and word position
    else:
        st.write("knowledge graph not computed")














