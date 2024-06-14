import json
from os import listdir, mkdir
from os.path import isfile, join
import time

delimiters = {
    "french": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "english": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "marquesan (Nuku Hiva)": [" ", ".", ",", ";", ":", "!", "?", "…"]
}
def build_knowledge_graph(language):
    # list all conversational questionnaires
    cq_folder = "./questionnaires"
    cq_json_list = [f for f in listdir(cq_folder) if isfile(join(cq_folder, f)) and f.endswith(".json")]
    cq_id_dict = {}
    # {uid: {
    #       "filename": cq filename,
    #       "content": cq content
    #       }
    # }
    recordings_list_dict = {}

    for cq in cq_json_list:
        # load the cq json file
        cq_json = json.load(open(join(cq_folder, cq)))
        uid = cq_json["uid"]
        cq_content = json.load(open(join(cq_folder, cq)))
        cq_id_dict[uid] = {"filename": cq, "content": cq_content}

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
                # print("cq_uid: ", cq_uid)
                if cq_uid in cq_id_dict.keys():
                    recordings_list_dict[recording] = recording_json["cq_uid"]
                    # print("recording {} has a corresponding questionnaire".format(recording))
                else:
                    print("recording {} has no corresponding questionnaire".format(recording))

    # build and save knowledge graph ======================================================================================
    knowledge_graph = {}
    knowledge_graph["language"] = language
    unique_words = []
    unique_words_frequency = {}
    total_target_word_count = 0
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
                    total_target_word_count += len(recording_json["data"][item]["translation"].split())
                    for word in recording_json["data"][item]["translation"].split():
                        if word in unique_words_frequency:
                            unique_words_frequency[word] += 1000 / total_target_word_count
                        else:
                            unique_words_frequency[word] = 1000 / total_target_word_count
                            unique_words.append(word)

                else:
                    print("BUILD KNOWLEDGE GRAPH: cq {} <========> recording {} don't match".format(
                        cq["dialog"][item]["text"], recording_json["data"][item]["cq"]))
                print(
                    "Warning: sentence #{}:{} of cq {} not found in recording".format(item, cq["dialog"][item]["text"],recording))
            except KeyError:
                    print("Warning: sentence #{}:{} of cq {} not found in recording".format(item, cq["dialog"][item]["text"], recording))
    # save knowledge graph
    with open("./data/knowledge/knowledge_graph" + language + ".json", "w") as f:
        json.dump(knowledge_graph, f)
    print("Knowledge graph built and saved in ./data/knowledge/knowledge_graph" + language + "_" + str(
        int(time.time())) + ".json")
    return knowledge_graph, unique_words, unique_words_frequency, total_target_word_count

def get_sentences_with_and_without_value(knowledge_graph, concept):
    sentences_with_value = []
    sentences_without_value = []
    for entry in knowledge_graph:
        for item in knowledge_graph[entry]["sentence_data"]["graph"]:
            if knowledge_graph[entry]["sentence_data"]["graph"][item]["value"] == concept:
                sentences_with_value.append(knowledge_graph[entry]["recording_data"]["translation"])
            else:
                sentences_without_value.append(knowledge_graph[entry]["recording_data"]["translation"])
    return sentences_with_value, sentences_without_value