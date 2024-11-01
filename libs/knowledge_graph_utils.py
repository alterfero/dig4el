# Copyright (C) 2024 Sebastien CHRISTIAN, University of French Polynesia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import copy
import json
import stat
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import utils, stats, graphs_utils as gu
from collections import OrderedDict
import pandas as pd

# delimiters = json.load(open("./data/delimiters.json"))

def consolidate_cq_transcriptions(transcriptions_list, language, delimiters):
    cq_folder = "./questionnaires"
    cq_json_list = [f for f in listdir(cq_folder) if isfile(join(cq_folder, f)) and f.endswith(".json")]
    cq_id_dict = {}
    # preparing the list of available cqs
    for cq in cq_json_list:
        # load the cq json file
        cq_json = json.load(open(join(cq_folder, cq)))
        uid = cq_json["uid"]
        cq_content = json.load(open(join(cq_folder, cq)))
        cq_id_dict[uid] = {"filename": cq, "content": cq_content}
    # filtering out transcriptions that don't have a known cq_uid
    filtered_recordings = {}

    for r in transcriptions_list:
        cq_uid = r["cq_uid"]
        #print("cq_uid: ", cq_uid)
        if cq_uid in cq_id_dict.keys():
            filtered_recordings[cq_uid] = copy.deepcopy(r)
            #print("transcription {} has a corresponding questionnaire".format(cq_uid))
        else:
            print("transcription {} has no corresponding questionnaire".format(cq_uid))

    # build and save knowledge graph ======================================================================================
    knowledge_graph = {}
    unique_words = []
    unique_words_frequency = {}
    total_target_word_count = 0
    index_counter = 0
    for recording_cq_uid, recording in filtered_recordings.items():
        # open corresponding cq
        cq = cq_id_dict[recording_cq_uid]["content"]
        for item in cq["dialog"]:
            if cq["dialog"][item]["speaker"] == "A":
                speaker = "A"
                listener = "B"
            else:
                speaker = "B"
                listener = "A"

            try:
                if cq["dialog"][item]["text"] == recording["data"][item]["cq"]:
                    knowledge_graph[index_counter] = {
                        "speaker_gender": cq["speakers"][speaker]["gender"],
                        "speaker_age": cq["speakers"][speaker]["age"],
                        "listener_gender": cq["speakers"][listener]["gender"],
                        "listener_age": cq["speakers"][listener]["age"],
                        "sentence_data": cq["dialog"][item],
                        "recording_data": recording["data"][item],
                        "language": language
                    }
                    index_counter += 1
                    words = stats.custom_split(recording["data"][item]["translation"], delimiters)
                    total_target_word_count += len(words)
                    for word in words:
                        if word in unique_words_frequency:
                            unique_words_frequency[word] += 1000 / total_target_word_count
                        else:
                            unique_words_frequency[word] = 1000 / total_target_word_count
                            unique_words.append(word)

                else:
                    print("BUILD KNOWLEDGE GRAPH: cq {} <========> recording {} don't match".format(
                        cq["dialog"][item]["text"], recording["data"][item]["cq"]))
            except KeyError:
                    print("Key Error: sentence #{}:{} not found in recording".format(item, cq["dialog"][item]["text"]))

    return knowledge_graph, unique_words, unique_words_frequency, total_target_word_count

def get_value_loc_dict(knowledge_graph, concept_kson, selected_f, delimiters):
    """ value_loc_dict provide statistics on values in the full knowledge graph.
    {'INCLUSIVE PREDICATE': [6, 12, 21], 'ATTRIBUTIVE PREDICATE': [25, 33, 42]}"""

    value_loc_dict = {}
    value_count_dict = {}
    #available_f = ["INTENT", "PREDICATE", "EVENT TENSE", "POLARITY", "PERSONAL DEICTIC", "ASPECT"]
    f_values = gu.get_leaves_from_node(concept_kson, selected_f)
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

def get_sentences_with_word(knowledge_graph, word, language, delimiters):
    sentences_with_word = []
    for entry in knowledge_graph:
        words = stats.custom_split(knowledge_graph[entry]["recording_data"]["translation"], delimiters)
        if word in words:
            sentences_with_word.append(entry)
    return sentences_with_word

def build_gloss_df(knowledge_graph, entry, delimiters):
    sentence_display_ordered_dict = OrderedDict()
    language = knowledge_graph[0]["language"]
    w_list = stats.custom_split(knowledge_graph[entry]["recording_data"]["translation"], delimiters)
    for wd in [w for w in w_list if w]:
        if wd in knowledge_graph[entry]["recording_data"]["concept_words"].values():
            concept_key = utils.get_key_by_value(knowledge_graph[entry]["recording_data"]["concept_words"], wd)
            sentence_display_ordered_dict[wd] = concept_key
            # TODO: of what is this concept a value?

        else:
            sentence_display_ordered_dict[wd] = ""


    # build dataframe from ordered dict
    return pd.DataFrame.from_dict(sentence_display_ordered_dict, orient="index", columns=["concept"]).T

def get_kg_entry_signature(knowledge_graph, entry_index):
    is_positive_polarity = True
    is_wildcard = False
    is_ref = False
    for concept in knowledge_graph[entry_index]["sentence_data"]["concept"]:
        if "wildcard" in concept:
            is_wildcard = True
        if concept[:3] == "Ref" or concept[:2] == "PP":
            is_ref = True
    for concept in knowledge_graph[entry_index]["sentence_data"]["graph"].keys():
        if concept[:-8] == "POLARITY":
            if knowledge_graph[entry_index]["sentence_data"]["graph"][concept]["value"] == "NEGATIVE":
                is_positive_polarity = False

    signature = {}
    signature["intent"] = knowledge_graph[entry_index]["sentence_data"]["intent"]
    signature["predicate"] =  knowledge_graph[entry_index]["sentence_data"]["predicate"]
    signature["polarity"] = is_positive_polarity
    signature["is_wildcard"] = is_wildcard
    signature["is_ref"] = is_ref

    return signature

def get_concept_word_pos(kg, entry_index, delimiters):
    target_words = stats.custom_split(kg[entry_index]["recording_data"]["translation"], delimiters)
    concept_words_dict = kg[entry_index]["recording_data"]["concept_words"]
    concept_word_pos = {}
    for concept, target_expression in concept_words_dict.items():
        word_list = target_expression.split("...")
        # if multiple words contribute to the concept, the position of the first word is used
        target_word = word_list[0]
        if target_word in target_words:
            concept_word_pos[concept] = {
                "concept": concept,
                "target_word": target_word,
                "pos": target_words.index(target_word)
            }
        else:
            if target_word != "":
                print("target word {} not in {}".format(target_word, target_words))
    return concept_word_pos

def get_kg_entry_from_pivot_sentence(kg, pivot_sentence):
    output = {}
    for entry_index, data in kg.items():
        if data["sentence_data"]["text"] == pivot_sentence:
            output = {
                "entry_index": entry_index,
                "data": data
            }
    return output

