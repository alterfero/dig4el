import copy
import json
import stat
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import utils, stats, graphs_utils as gu
from collections import OrderedDict
import pandas as pd

IPKS = ["QUANTIFIER", "ASPECT", "EVENT TENSE", "POLARITY", "DEFINITENESS"]
RPKS = ["AGENT", "PATIENT", "OBLIQUE", "POSSESSOR", "POSSESSEE"]

# delimiters = json.load(open("./data/delimiters.json"))

def consolidate_cq_transcriptions(transcriptions_list, language, delimiters):
    try:
        cq_folder = "./questionnaires"
        cq_json_list = [f for f in listdir(cq_folder) if isfile(join(cq_folder, f)) and f.endswith(".json")]
    except FileNotFoundError:
        cq_folder = "../questionnaires"
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

def get_kg_entry_polarity(kg_entry):
    for concept_name, data in kg_entry["sentence_data"]["graph"].items():
        if "POLARITY" in concept_name and data["value"]=="NEGATIVE":
            return "NEGATIVE"
    return "POSITIVE"

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

def get_sentences_with_word(knowledge_graph, word, delimiters):
    sentences_with_word = []
    for entry in knowledge_graph:
        words = stats.custom_split(knowledge_graph[entry]["recording_data"]["translation"], delimiters)
        if word in words:
            sentences_with_word.append(entry)
    return sentences_with_word

def build_gloss_df(knowledge_graph, entry, delimiters):
    sentence_display_ordered_dict = OrderedDict()
    w_list = stats.custom_split(knowledge_graph[entry]["recording_data"]["translation"], delimiters)
    # unpack multiple words associated with a single concept
    unpacked_tw = {}
    for concept, target_words in knowledge_graph[entry]["recording_data"]["concept_words"].items():
        words = target_words.split("...")
        if len(words) > 1:
            wcount = 0
            for word in words:
                wcount += 1
                unpacked_tw[concept+"_"+str(wcount)] = word
        else:
            unpacked_tw[concept] = words[0]
    # build ordered dict
    for wd in [w for w in w_list if w]:
        if wd in unpacked_tw.values():
            concept_key = utils.get_key_by_value(unpacked_tw, wd)
            sentence_display_ordered_dict[wd] = concept_key
        else:
            sentence_display_ordered_dict[wd] = ""
    # build dataframe from ordered dict
    return pd.DataFrame.from_dict(sentence_display_ordered_dict, orient="index", columns=["concept"]).T

def get_particularization_info(kg, entry, concept):
    ip = {}
    rp = {}
    cgraph = kg[entry]["sentence_data"]["graph"]
    for gkey, gdata in cgraph.items():
        if gdata["value"] != "":
            if gkey.startswith(concept):
                param = gkey[len(concept) + 1:]
                if param in IPKS:
                    ip[param] = gdata["value"]
                if param in RPKS:
                    rp[param] = gdata["value"]
            if gdata["value"] == concept:
                gkey_concept = [c for c in cgraph["sentence"]["requires"] if c in gdata["path"]][0]
                param = "undetermined"
                for rpk in RPKS:
                    if gdata["path"][-1] == "REFERENCE TO CONCEPT":
                        param = gdata["path"][-2]
                    else:
                        param = gdata["path"][-1]
                rp[param + " of"] = gkey_concept
    return ip, rp

def build_super_gloss_df(knowledge_graph, entry, delimiters, output_dict=False):
    sentence_display_list = []
    target_words_from_translation = stats.custom_split(knowledge_graph[entry]["recording_data"]["translation"], delimiters)
    unpacked_tw = {}
    concept_particularization_dict = {}
    for concept, target_words_from_concept_words in knowledge_graph[entry]["recording_data"]["concept_words"].items():
        # concept particularization
        ip, rp = get_particularization_info(knowledge_graph, entry, concept)
        concept_particularization_dict[concept] = {
            "ip": ip,
            "rp": rp
        }
        # if multiple target words for a concept (separated by ...) they're developed into multiple words
        # with concept concept_1, concept_2 etc.
        words = target_words_from_concept_words.split("...")
        words = [word.lower() for word in words]
        if len(words) > 1:
            wcount = 0
            for word in words:
                wcount += 1
                unpacked_tw[concept + "_" + str(wcount)] = word
        else:
            unpacked_tw[concept] = words[0]
    # build sentence list
    # for each non-empty word from the translation sentence
    for wd in [w for w in target_words_from_translation if w]:
        # if this word is in the unpacked target words from concept words
        if wd in unpacked_tw.values():
            # the associated concept is concept_key
            concept_key = utils.get_key_by_value(unpacked_tw, wd)
            try:
                ip_display = ", ".join([str(k)+": "+str(v) for k,v in concept_particularization_dict[concept_key.split("_")[0]]["ip"].items()])
            except KeyError:
                ip_display = ""
                print("Key Error in build super gloss on ip_display.")
                print("wd: ".format(wd))
                print("concept_key: ".format(concept_key))
                print("concept_particularization_dict: {}".format(concept_particularization_dict))
            try:
                rp_display = ", ".join([str(k)+" "+str(v) for k,v in concept_particularization_dict[concept_key.split("_")[0]]["rp"].items()])
            except KeyError:
                rp_display = ""
                print("Key Error in build super gloss on rp_display. ")
                print("wd: ".format(wd))
                print("concept_key: ".format(concept_key))
                print("concept_particularization_dict: {}".format(concept_particularization_dict))
            sentence_display_list.append({"word": wd,
                                          "concept": concept_key,
                                          "internal particularization": ip_display,
                                          "relational particularization": rp_display
                                          })
        else:
            sentence_display_list.append({"word": wd,
                                          "concept": "",
                                          "internal particularization": "",
                                          "relational particularization": ""})
    if not output_dict:
        # build dataframe from ordered dict
        output_df = pd.DataFrame(sentence_display_list)
        output_df.set_index("word", inplace=True)
        return output_df.T
    else:
        return sentence_display_list

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
        if concept.endswith("POLARITY"):
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

def build_categorical_kg(kg, delimiters, cg,
                         replace_target_words=True,
                         concept_ancestor_level=0,
                         keep_target_words=False,
                         include_particularization=False,
                         show_example=True):
    def is_sublist(smaller_list, bigger_list):
        for i in range(len(bigger_list) - len(smaller_list) + 1):
            if bigger_list[i:i + len(smaller_list)] == smaller_list:
                return True
        return False

    def replace_word_in_dict(input_dict, old_word, new_word):
        """
        Replace a word in a dictionary, whether it's a key or appears in values.

        Args:
            input_dict: Dictionary to modify
            old_word: Word to replace
            new_word: Replacement word

        Returns:
            Modified dictionary with replacements
        """
        result_dict = {}

        # Process each key-value pair
        for key, value in input_dict.items():
            # Check if the key contains the word (assuming string keys)
            if isinstance(key, str) and old_word in key:
                new_key = key.replace(old_word, new_word)
            else:
                new_key = key

            # Process the value based on its type
            if isinstance(value, str):
                # Replace word in string values
                new_value = value.replace(old_word, new_word)
            elif isinstance(value, list):
                # Process list values
                new_value = []
                for item in value:
                    if isinstance(item, str):
                        new_value.append(item.replace(old_word, new_word))
                    elif isinstance(item, dict):
                        # Recursively process nested dictionaries
                        new_value.append(replace_word_in_dict(item, old_word, new_word))
                    else:
                        new_value.append(item)
            elif isinstance(value, dict):
                # Recursively process nested dictionaries
                new_value = replace_word_in_dict(value, old_word, new_word)
            else:
                # Other value types remain unchanged
                new_value = value

            # Add the processed key-value pair to the result
            result_dict[new_key] = new_value

        return result_dict

    example_counter = 0
    n_examples = 24
    if show_example and example_counter < n_examples:
        print("===================================================")
        print("XXX           ALTERLINGUAL KG                    XXX")
        print("===================================================")

    output_kg = {}
    cat_mapping = {
        "CONCEPT CORE": "CONCEPT_CORE",
        "IN FUTURE DIRECTION": "IN_FUTURE_DIRECTION",
        "EXPERIENCEABLE OBJECT": "THING",
        "ACTION": "PROCESS",
        "EXPERIENCE": "PROCESS",
        "OBJECT": "OBJECT",
        "ABSTRACT OBJECT": "ABSTRACT_OBJECT",
        "NON-GRAMMATICAL QUALIFIER": "QUALIFIER",
        "TIME LOGIC": "TIME_LOGIC",
        "RELATIVE TIME REFERENCE": "RELATIVE_TIME_REFERENCE",
        "ABSOLUTE TIME REFERENCES": "ABOLUTE_TIME_REFERENCE",
        "TIME CHUNKS": "TIME_CHUNK",
        "SPACE LOGIC": "SPACE_LOGIC",
        "QUANTIFIER": "QUANTIFIER",
        "QUALIFIER": "QUALIFIER",
        "PERSONAL DEICTIC": "PERSONAL_PRONOUN",
        "EVENT DEICTIC": "EVENT_DEICTIC",
        "NON-HUMAN DEICTIC": "REF_OBJECT(S)"
    }
    for index, entry in kg.items():
        concept_mapping = {}
        output_kg[index] = copy.deepcopy(entry)
        translation_items = stats.custom_split(entry["recording_data"]["translation"], delimiters)
        concepts = entry["sentence_data"]["concept"]
        if show_example and example_counter < n_examples:
            print("EXAMPLE")
            print("Entry {}, concepts: {}".format(index, concepts))
            example_counter += 1

        # LOOPING OVER ENTRY CONCEPTS IN THE KG TO CREATE CONCEPT MAPPING AND NEW ["sentence_data"]["concept"]
        concept_log = {}
        for concept in concepts:
            concept_log[concept] = {"new": "", "ip": {}, "rp": {}}

            # creating concept_mapping
            concept_mapping[concept] = concept
            ancestors = gu.get_genealogy(cg, concept)
            if concept_ancestor_level == 0:
                exp = concept
            else:
                if len(ancestors) >= concept_ancestor_level:
                    ancestor_index = concept_ancestor_level - 1
                else:
                    ancestor_index = len(ancestors) - 1
                if ancestors[ancestor_index] in cat_mapping.keys():
                    exp = cat_mapping[ancestors[ancestor_index]]
                else:
                    exp = ancestors[ancestor_index]
            concept_mapping[concept] = exp.replace(" ", "_")
            concept_log[concept]["new"] = exp.replace(" ", "_")
        if show_example and example_counter < n_examples:
            print("Concept mapping: {}".format(concept_mapping))

        # change concepts in the concept list using concept_mapping
        output_kg[index]["sentence_data"]["concept"] = [concept_mapping[concept]
                                                        for concept in entry["sentence_data"]["concept"]]
        if show_example and example_counter < n_examples:
            print("New concept_list: {}".format(output_kg[index]["sentence_data"]["concept"]))
            print("Entry concept_words: {}".format(entry["recording_data"]["concept_words"]))

        # change concepts in concept_words + target words and target sentence if replace_target_words=True
        output_kg[index]["recording_data"]["concept_words"] = {}

        # LOOPING OVER CONCEPTS AGAIN TO PERFORM UPDATES OF ["recording_data"]["concept_words"] and ["recording_data"]["translation"]
        for concept, tw in entry["recording_data"]["concept_words"].items():
            if concept in entry["sentence_data"]["concept"]:
                concept_particularization_dict = {}

                # retrieve concept particularization
                ip, rp = get_particularization_info(kg, index, concept)
                concept_particularization_dict[concept] = {
                    "ip": ip,
                    "rp": rp
                }
                ip_display = "&".join([str(k) + "=" + str(v) for k, v in concept_particularization_dict[concept]["ip"].items()])
                rp_display = "&".join([str(k) + "_" + str(v) for k, v in concept_particularization_dict[concept]["rp"].items()])
                ip_and_rp_display = ""
                if ip_display or rp_display:
                    ip_and_rp_display += "("
                if ip_display:
                    ip_and_rp_display += "" + ip_display
                if rp_display:
                    if ip_display:
                        ip_and_rp_display += "_"
                    ip_and_rp_display += rp_display
                if ip_display or rp_display:
                    ip_and_rp_display += ")"

                if show_example and example_counter < n_examples:
                    print("concept {}, tw: {}".format(concept, tw))
                    print("ip_display: {}".format(ip_display))
                    print("rp_display: {}".format(rp_display))
                    print("translation items: {}".format(translation_items))

                if tw != "":  # if there are target word(s) associated with concept
                    # KEEP TARGET WORDS if keep_target_words is True, otherwise just keep concepts
                    # whem multiple words for a concept, + them if they're contiguous, considering them as a unique superword. If they're not: repeat the concept.
                    # add IP and RP if include_particularization

                    if replace_target_words:
                        # individual target words connected to concept
                        twl = tw.split("...")
                        # are they contiguous in the translation?
                        is_contiguous = is_sublist(twl, translation_items)
                        if show_example and example_counter < n_examples:
                            print("{} is_contiguous {} in {}".format(tw, is_contiguous, entry["recording_data"]["translation"]))

                        if is_contiguous:
                            tw_index = 0
                            while tw_index <= len(twl) - 1:
                                translation_items_index = translation_items.index(twl[tw_index])
                                if tw_index == 0:  # first word, erased if multiple contiguous words
                                    if len(twl) > 1 and not keep_target_words:
                                        translation_items[translation_items_index] = ""
                                if tw_index > 0:  # non-first w gets a "+" at the beginning when keeping target words
                                    if keep_target_words:
                                        translation_items[translation_items_index] = "+" + translation_items[translation_items_index]
                                    else:  # otherwise erased
                                        translation_items[translation_items_index] = ""
                                if len(twl) == tw_index + 1:  # last w gets the concept mapping added and particularization if option
                                    if keep_target_words:
                                        translation_items[translation_items_index] = translation_items[translation_items_index] + "_" + concept_mapping[concept]
                                    else:
                                        translation_items[translation_items_index] = concept_mapping[concept]
                                    if include_particularization:
                                        translation_items[translation_items_index] += ip_and_rp_display
                                tw_index += 1


                        else:  #non-contiguous: add concept and counter if multiple
                            c = 0
                            for w in twl:
                                if w in translation_items:
                                    tii = translation_items.index(w)
                                    if keep_target_words:
                                        translation_items[tii] = w + "_" + concept_mapping[concept]
                                        if len(twl) > 1:
                                            translation_items[tii] += "_" + str(c)
                                            c += 1
                                    else:
                                        translation_items[tii] = concept_mapping[concept]
                                        if len(twl) > 1:
                                            translation_items[tii] += "_" + str(c)
                                            c += 1
                                    if include_particularization:
                                        translation_items[tii] += ip_and_rp_display

                        if show_example and example_counter < n_examples:
                            print("modified translation items: {}".format(translation_items))

                        # Reconstruct target sentence from modified translation_items
                        new_ts = ""
                        for item in translation_items:
                            if item != "":
                                if item[0] == "+":
                                    new_ts += item
                                else:
                                    new_ts += " " + item
                        output_kg[index]["recording_data"]["translation"] = new_ts

                        if show_example and example_counter < n_examples:
                            print("New target sentence: {}".format(output_kg[index]["recording_data"]["translation"]))
                            print("New concept words: {}".format(output_kg[index]["recording_data"]["concept_words"]))
                            example_counter += 1
                            print("New target sentence: {}".format(output_kg[index]["recording_data"]["translation"]))

                        # replace in concept_words
                        owl = [item+"_"+concept_mapping[concept] for item in twl]
                        swl = "...".join(owl)
                        output_kg[index]["recording_data"]["concept_words"][concept_mapping[concept]] = swl

                    else:
                        output_kg[index]["recording_data"]["concept_words"][concept_mapping[concept]] = entry["recording_data"]["concept_words"][concept]



        # change concepts in graph and trimmed graph
        for concept in concept_mapping.keys():
            output_kg[index]["sentence_data"]["graph"] = replace_word_in_dict(entry["sentence_data"]["graph"],
                                                                              concept,
                                                                              concept_mapping[concept])
            output_kg[index]["sentence_data"]["trimmed_graph"] = replace_word_in_dict(entry["sentence_data"]["trimmed_graph"],
                                                                                      concept,
                                                                                      concept_mapping[concept])
        else:
            example_counter += 1
    return output_kg


def build_concept_dict(kg):
    cdict = {}
    # create dict with concepts and their particularizations
    for entry, content in kg.items():
        for concept in content["sentence_data"]["concept"]:
            if concept not in cdict.keys():
                cdict[concept] = []
            details = {
                "pivot_sentence": content["sentence_data"]["text"],
                "target_sentence": content["recording_data"]["translation"],
                "target_words":
                    content.get("recording_data", "none").get("concept_words", "none").get(concept, "none").split("_")[
                        0],
                "particularization":
                    {
                "enunciation": {"speaker gender": content["speaker_gender"]},
                "intent": {"intent": "&".join(content["sentence_data"]["intent"])
                           },
                "predicate": {"predicate": content["sentence_data"]["predicate"][0]},
                "internal_particularization": {},
                "relational_particularization": {}
                },
                "kg_entry": entry,
                "signature": get_kg_entry_signature(kg, entry)
            }
            if "alternate_pivot" in content["recording_data"].keys():
                if content["recording_data"]["alternate_pivot"] != "":
                    details["alternate_pivot"] = concept["recording_data"]["alternate_pivot"]
            else:
                print("From build_concept_dict: Alternate pivot missing from recording_data in kg")
                details["alternate_pivot"] = ""
            for k, v in content["sentence_data"]["graph"].items():
                if concept in k and v["value"] != "":
                    for ipk in IPKS:
                        if ipk in k:
                            details["particularization"]["internal_particularization"][ipk] = v["value"]
                    for rpk in RPKS:
                        if rpk in k:
                            details["particularization"]["relational_particularization"][rpk] = v["value"]
                if v["value"] == concept:
                    for ipk in IPKS:
                        if ipk in k:
                            details["particularization"]["internal_particularization"][ipk] = v["value"]
                    for rpk in RPKS:
                        if rpk in k:
                            details["particularization"]["relational_particularization"][rpk] = v["value"]
            cdict[concept].append(details)
    return cdict

def target_word_to_concept_dict(knowledge_graph):
    """
    Returns a dict of target_word:[concepts] and concept:[target_words]
    """
    tw_to_concept_dict = {}
    concept_dict = build_concept_dict(knowledge_graph)
    for concept, details in concept_dict.items():
        if details["target_words"] != "":
            tw_to_concept_dict[details["target_words"]] = {
                "concept": concept,
                "particularization": details["particularization"],
                "pivot_sentence": details["pivot_sentence"],
                "target_sentence": details["target_sentence"]
            }
    return tw_to_concept_dict


