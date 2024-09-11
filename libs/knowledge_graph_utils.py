import json
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import utils, stats, graphs_utils as gu
from collections import OrderedDict
import pandas as pd

delimiters = json.load(open("./data/delimiters.json"))
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
                        "recording_data": recording_json["data"][item],
                        "language": language
                    }
                    index_counter += 1
                    words = stats.custom_split(recording_json["data"][item]["translation"], delimiters[language])
                    total_target_word_count += len(words)
                    for word in words:
                        if word in unique_words_frequency:
                            unique_words_frequency[word] += 1000 / total_target_word_count
                        else:
                            unique_words_frequency[word] = 1000 / total_target_word_count
                            unique_words.append(word)

                else:
                    print("BUILD KNOWLEDGE GRAPH: cq {} <========> recording {} don't match".format(
                        cq["dialog"][item]["text"], recording_json["data"][item]["cq"]))
            except KeyError:
                    print("Key Error: sentence #{}:{} of cq {} not found in recording".format(item, cq["dialog"][item]["text"], recording))
    # save knowledge graph
    with open("./data/knowledge/knowledge_graph" + language + ".json", "w") as f:
        json.dump(knowledge_graph, f)
    print("Knowledge graph built and saved in ./data/knowledge/knowledge_graph" + language + "_" + str(
        int(time.time())) + ".json")
    return knowledge_graph, unique_words, unique_words_frequency, total_target_word_count


def get_value_loc_dict(knowledge_graph, concept_kson, selected_f, delimiters):
    """ value_loc_dict provide statistics on values in the full knowledge graph.
    {'INCLUSIVE PREDICATE': [6, 12, 21], 'ATTRIBUTIVE PREDICATE': [25, 33, 42]}"""

    value_loc_dict = {}
    value_count_dict = {}
    #available_f = ["INTENT", "PREDICATE", "EVENT TENSE", "POLARITY", "PERSONAL DEICTIC", "ASPECT"]
    f_values = gu.get_leaves_from_node(concept_kson, selected_f)
    value_loc_dict = {}
    # stats on values and their locations in the knowledge graph: value_loc_dict
    if selected_f in ["INTENT", "PREDICATE"]:
        f = selected_f.lower()
        for v in f_values:
            value_loc_dict[v] = []
        value_loc_dict["neutral"] = []
        for entry_key in knowledge_graph:
            if f in knowledge_graph[entry_key]["sentence_data"].keys():
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

    elif selected_f in ["PERSONAL DEICTIC"]:
        print("Selected {}".format(selected_f))
        for v in f_values:
            value_loc_dict[v + " AGENT"] = []
            value_loc_dict[v + " PATIENT"] = []
            value_loc_dict[v + " POSSESSOR"] = []
            value_loc_dict[v + " OTHER"] = []
        for entry_key in knowledge_graph:
            for graph_key in knowledge_graph[entry_key]["sentence_data"]["graph"]:
                if "value" in knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key]:
                    if knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key][
                        "value"] in f_values:
                        local_value = \
                        knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key]["value"]
                        # semantic role
                        if "AGENT" in \
                                knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key][
                                    "path"]:
                            value_loc_dict[local_value + " AGENT"].append(entry_key)
                        elif "PATIENT" in \
                                knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key][
                                    "path"]:
                            value_loc_dict[local_value + " PATIENT"].append(entry_key)
                        elif "POSSESSOR" in \
                                knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key][
                                    "path"]:
                            value_loc_dict[local_value + " POSSESSOR"].append(entry_key)
                        else:
                            value_loc_dict[local_value + " OTHER"].append(entry_key)
        for item in value_loc_dict:
            value_count_dict[item] = len(value_loc_dict[item])

    else:
        print("Selected {}".format(selected_f))
        for v in f_values:
            value_loc_dict[v] = []
        value_loc_dict["neutral"] = []
        for entry_key in knowledge_graph:
            for graph_key in knowledge_graph[entry_key]["sentence_data"]["graph"]:
                if selected_f in graph_key:
                    if "value" in knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key]:
                        if knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key][
                            "value"] in f_values:
                            (value_loc_dict[
                                 knowledge_graph[entry_key]["sentence_data"]["graph"][graph_key][
                                     "value"]]
                             .append((entry_key)))
                        else:
                            value_loc_dict["neutral"].append(entry_key)
    return value_loc_dict

def get_concepts_associated_to_word_by_human(knowledge_graph, word, language):
    """ build a dict with all the concepts connected to a word in the target language
    the dict is word: {'concept':"", 'count':n}"""
    word_concept_connection_dict = {}
    entries_with_word = get_sentences_with_word(knowledge_graph, word, language)
    #print("{} entries with word {}".format(len(entries_with_word), word))
    for entry in entries_with_word:
        found_one = False
        for c in knowledge_graph[entry]["recording_data"]["concept_words"]:
            if knowledge_graph[entry]["recording_data"]["concept_words"][c] == word:
                found_one = True
                if c in word_concept_connection_dict:
                    word_concept_connection_dict[c]["count"] += 1
                    word_concept_connection_dict[c]["entry_list"].append(entry)
                else:
                    word_concept_connection_dict[c] = {"concept": c, "count": 1, "entry_list": [entry]}
        if not found_one:
            if "none" in word_concept_connection_dict:
                word_concept_connection_dict["none"]["count"] +=1
                word_concept_connection_dict["none"]["entry_list"].append(entry)
            else:
                word_concept_connection_dict["none"] = {"concept": "none", "count": 1, "entry_list": [entry]}
    return word_concept_connection_dict


def get_diff_word_statistics_with_value_loc_dict(knowledge_graph, value_loc_dict, v_focus, total_target_word_count, delimiters):
    v_focus_sentences = value_loc_dict[v_focus]
    v_not_focus_sentences = []
    for v in value_loc_dict:
        if v != v_focus:
            v_not_focus_sentences += value_loc_dict[v]

    v_focus_words = []
    v_not_focus_words = []
    for v_focus_sentence in v_focus_sentences:
        v_focus_words += stats.custom_split(
            knowledge_graph[v_focus_sentence]["recording_data"]["translation"],
            delimiters)
    for v_not_focus_sentence in v_not_focus_sentences:
        v_not_focus_words += stats.custom_split(
            knowledge_graph[v_not_focus_sentence]["recording_data"]["translation"],
            delimiters)
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
        v_focus_word_frequency[word] = v_focus_words_count[word] * 1000 / total_target_word_count
    v_not_focus_word_frequency = {}
    for word in v_not_focus_words_count:
        v_not_focus_word_frequency[word] = v_not_focus_words_count[word] * 1000 / total_target_word_count

    # diff frequencies between v and not v
    v_focus_word_diff_frequency_v_not_v = {}
    for word in v_focus_word_frequency:
        if word in v_not_focus_word_frequency:
            v_focus_word_diff_frequency_v_not_v[word] = v_focus_word_frequency[word] - v_not_focus_word_frequency[word]
        else:
            v_focus_word_diff_frequency_v_not_v[word] = v_focus_word_frequency[word]
    return v_focus_word_diff_frequency_v_not_v

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

def get_sentences_with_word(knowledge_graph, word, language):
    sentences_with_word = []
    for entry in knowledge_graph:
        words = stats.custom_split(knowledge_graph[entry]["recording_data"]["translation"], delimiters[language])
        if word in words:
            sentences_with_word.append(entry)
    return sentences_with_word

def build_gloss_df(knowledge_graph, entry):
    sentence_display_ordered_dict = OrderedDict()
    language = knowledge_graph[0]["language"]
    w_list = stats.custom_split(knowledge_graph[entry]["recording_data"]["translation"], delimiters[language])
    for wd in [w for w in w_list if w]:
        if wd in knowledge_graph[entry]["recording_data"]["concept_words"].values():
            concept_key = utils.get_key_by_value(knowledge_graph[entry]["recording_data"]["concept_words"], wd)
            sentence_display_ordered_dict[wd] = concept_key
            # TODO: of what is this concept a value?

        else:
            sentence_display_ordered_dict[wd] = ""


    # build dataframe from ordered dict
    return pd.DataFrame.from_dict(sentence_display_ordered_dict, orient="index", columns=["concept"]).T

def get_kg_entry_signature(knowledge_graph, entry):
    data = knowledge_graph[entry]

    is_wildcard = False
    for concept in data["sentence_data"]["concept"]:
        if "wildcard" in concept:
            is_wildcard = True

    signature = []
    # TODO: take all intents into account if multiple
    if data["sentence_data"]["intent"] != []:
        signature.append(data["sentence_data"]["intent"][0])
    else:
        signature.append("")
    if data["sentence_data"]["predicate"] != []:
        signature.append(data["sentence_data"]["predicate"][0])
    else:
        signature.append("")

    if is_wildcard:
        signature.append("is_wildcard")
    else:
        signature.append("no_wildcard")

    return signature

