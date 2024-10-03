from collections import defaultdict
import json
from libs import knowledge_graph_utils as kgu, stats, wals_utils as wu

delimiters = {
    "french": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "english": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "marquesan (Nuku Hiva)": [" ", ".", ",", ";", ":", "!", "?", "…"]
}

def observer_order_of_subject_object_verb(transcriptions, language, delimiters):
    output_dict = {
        "ppk": "81",
        "agent-ready observation": {},
        "observations":{
            "SVO":{
                "depk": "384",
                "count":0,
                "details":{}
            },
            "SOV": {
                "depk": "383",
                "count": 0,
                "details": {}
            },
            "VSO": {
                "depk": "385",
                "count": 0,
                "details": {}
            },
            "VOS": {
                "depk": "386",
                "count": 0,
                "details": {}
            },
            "OVS": {
                "depk": "387",
                "count": 0,
                "details": {}
            },
            "OSV": {
                "depk": "388",
                "count": 0,
                "details": {}
            },
            "No dominant order": {
                "depk": "389",
                "count": 0,
                "details": {}
            }
        }
    }

    for entry_index, entry_data in transcriptions.items():
        sentence_data = entry_data.get('sentence_data', {})
        graph = sentence_data.get('graph', {})
        # build a list of the target words for position reference
        target_words = stats.custom_split(transcriptions[entry_index]["recording_data"]["translation"], delimiters)
        for concept in graph:
            is_event = False
            is_agent_required = False
            is_active_agent = False
            is_patient_required = False
            is_active_patient = False
            agent_position = -1
            event_position = -1
            patient_position = -1
            # is the entry an event with required agent? if event, get info
            for option in graph[concept]["requires"]:
                # is this concept an event? If yes it accepts an agent
                if option[-5:] == "AGENT":
                    is_event = True
                    is_agent_required = True
                    print("{} is an event".format(concept))

                    # is there a target word associated with this event?
                    try:
                        event_target = transcriptions[entry_index]["recording_data"]["concept_words"][concept]
                        if event_target != "":
                            # targets are words separated by "..." in case of multi-word concepts.
                            # when that happens, we recover the list and take the lowest index in the sentence as the position.
                            # TODO: implement smarter word order logic
                            event_target_list = event_target.split("...")
                            event_target_pos_word = event_target_list[0]
                            print("event_target_pos_word ",event_target_pos_word)
                            if event_target_pos_word in target_words:
                                print("{} in target words {} ".format(event_target_pos_word, target_words))
                                event_position = target_words.index(event_target_pos_word)
                            else:
                                print("Simple Inference TARGET POS WORD NOT IN TARGET WORDS: entry: {}, event_target_pos_word {} not in target_words {}".format(entry_index, event_target_pos_word,target_words))
                    except KeyError:
                        print("problem with concept {} in entry {}, not in concept_words {}".format(concept, entry_index, knowledge_graph[entry_index]["recording_data"]["concept_words"]))

            if is_event:
                # search for an active agent and potential target word(s)
                agent_key = concept + " AGENT"
                print("agent_key ",agent_key)
                # retrieving the agent requires to pass through the AGENT REFERENCE TO CONCEPT node.
                # TODO: make that more failproof
                try:
                    agent_value = graph[graph[agent_key]["requires"][0]]["value"]
                except:
                    agent_value = ""
                    print("exception caught in determining agent_value in analyze_word_order in entry {}".format(entry_index))
                #print("agent value ",agent_value)
                if agent_value != "":
                    is_active_agent = True
                    # is this active agent associated with a word in target language?
                    try:
                        agent_target =  transcriptions[entry_index]["recording_data"]["concept_words"][agent_value]
                    except:
                        #print("problem retrieving agent target for concept {}, kg entry {}".format(concept, entry_index))
                        agent_target = ""
                    agent_target_list = agent_target.split("...")
                    agent_target_pos_word = agent_target_list[0]
                    #print("agent_target_pos_word ",agent_target_pos_word)

                    if agent_target_pos_word != "":
                        if agent_target_pos_word in target_words:
                            agent_position = target_words.index(agent_target_pos_word)
                            #print("agent_position ",agent_position)
                        else:
                            print("AGENT_TARGET NOT IN TARGET_WORDS: agent_target {} not in target_words {}".format(agent_target_pos_word, target_words))

                # checking now if this event has a patient
                for option in graph[concept]["requires"]:
                    if option[-7:] == "PATIENT":
                        is_patient_required = True

                if is_patient_required:
                    # is there an active patient in this sentence?
                    patient_key = concept + " PATIENT"
                    #print("patient_key ",patient_key)
                    try:
                        patient_value = graph[graph[patient_key]["requires"][0]]["value"]
                        #print("patient_value ",patient_value)
                    except:
                        print("exception caught in determining patient_value in analyze_word_order, entry {}".format(entry_index))
                    if patient_value != "":
                        is_active_patient = True
                        # is this active agent associated with a word in target language?
                        if patient_value in transcriptions[entry_index]["recording_data"]["concept_words"] :
                            patient_target = transcriptions[entry_index]["recording_data"]["concept_words"][patient_value]
                            patient_target_list = patient_target.split("...")
                            patient_target_pos_word = patient_target_list[0]

                            if patient_target_pos_word != "":
                                if patient_target_pos_word in target_words:
                                    patient_position = target_words.index(patient_target_pos_word)
                                else:
                                    print("PATIENT TARGET NOT IN TARGET WORDS: patient_target {} not in target_words {}".format(
                                        patient_target_pos_word, target_words))
                        else:
                            print("CQ SVO ORDER OBSERVER WARNING: patient_value {} not found".format(patient_value))

            if is_event:
                # intransitive event with known positions
                # if event_position != -1 and agent_position != -1 and not is_patient_required:
                #     if event_position < agent_position:
                #         ord = "ea_"
                #         info_dict["index_lists_by_order"]["ea_"].append(entry_index)
                #         info_dict["signature_list_by_order"]["ea_"].append(kgu.get_kg_entry_signature(knowledge_graph, entry_index))
                #     else:
                #         ord = "ae_"
                #         info_dict["index_lists_by_order"]["ae_"].append(entry_index)
                #         info_dict["signature_list_by_order"]["ae_"].append(kgu.get_kg_entry_signature(knowledge_graph, entry_index))
                #     info_dict["intransitive"].append(
                #         {"entry": entry_index,
                #          "event_position": event_position,
                #          "agent_position": agent_position,
                #          "order": ord
                #         }
                #     )

                # transitive event with known positions
                if event_position != -1 and agent_position != -1 and patient_position != -1:
                    positions = {
                        'V': event_position,
                        'S': agent_position,
                        'O': patient_position
                    }
                    # Sort the positions
                    sorted_order = sorted(positions.items(), key=lambda x: x[1])
                    # Create the acronym
                    order = ''.join([item[0] for item in sorted_order])

                    output_dict["observations"][order]["details"][entry_index] = kgu.get_kg_entry_signature(transcriptions, entry_index)

    for order in output_dict["observations"].keys():
        output_dict["observations"][order]["count"] = len(output_dict["observations"][order]["details"].keys())
    # creating agent-ready observation
    agent_obs = {}
    for order in output_dict["observations"].keys():
        agent_obs[output_dict["observations"][order]["depk"]] = output_dict["observations"][order]["count"]
    output_dict["agent-ready observation"] = agent_obs

    return output_dict


def observe_epa_order(knowledge_graph):
    language = knowledge_graph[0]["language"]
    word_order_stats = defaultdict(list)
    info_dict = {
        "transitive": [],
        "intransitive": [],
        "index_lists_by_order":{
            "ea_": [],
            "ae_": [],
            "eap": [],
            "epa": [],
            "pae": [],
            "pea": [],
            "ape": [],
            "aep": []
        },
        "signature_list_by_order":{
            "ea_": [],
            "ae_": [],
            "eap": [],
            "epa": [],
            "pae": [],
            "pea": [],
            "ape": [],
            "aep": []
        },
        "stats": {}
    }
    for entry_index, entry_data in knowledge_graph.items():
        sentence_data = entry_data.get('sentence_data', {})
        graph = sentence_data.get('graph', {})
        # build a list of the target words for position reference
        target_words = stats.custom_split(knowledge_graph[entry_index]["recording_data"]["translation"], delimiters[language])
        for concept in graph:
            is_event = False
            is_agent_required = False
            is_active_agent = False
            is_patient_required = False
            is_active_patient = False
            agent_position = -1
            event_position = -1
            patient_position = -1
            # is the entry an event with required agent? if event, get info
            for option in graph[concept]["requires"]:
                # is this concept an event? If yes it accepts an agent
                if option[-5:] == "AGENT":
                    is_event = True
                    is_agent_required = True
                    #print("{} is an event".format(concept))

                    # is there a target word associated with this event?
                    try:
                        event_target = knowledge_graph[entry_index]["recording_data"]["concept_words"][concept]
                        if event_target != "":
                            # targets are words separated by "..." in case of multi-word concepts.
                            # when that happens, we recover the list and take the lowest index in the sentence as the position.
                            # TODO: implement smarter word order logic
                            event_target_list = event_target.split("...")
                            event_target_pos_word = event_target_list[0]
                            #print("event_target_pos_word ",event_target_pos_word)
                            if event_target_pos_word in target_words:
                                #print("{} in target words {} ".format(event_target_pos_word, target_words))
                                event_position = target_words.index(event_target_pos_word)
                            else:
                                print("Simple Inference TARGET POS WORD NOT IN TARGET WORDS: entry: {}, event_target_pos_word {} not in target_words {}".format(entry_index, event_target_pos_word,target_words))
                    except KeyError:
                        print("problem with concept {} in entry {}, not in concept_words {}".format(concept, entry_index, knowledge_graph[entry_index]["recording_data"]["concept_words"]))

            if is_event:
                # search for an active agent and potential target word(s)
                agent_key = concept + " AGENT"
                #print("agent_key ",agent_key)
                # retrieving the agent requires to pass through the AGENT REFERENCE TO CONCEPT node.
                # TODO: make that more failproof
                try:
                    agent_value = graph[graph[agent_key]["requires"][0]]["value"]
                except:
                    agent_value = ""
                    print("exception caught in determining agent_value in analyze_word_order in entry {}".format(entry_index))
                #print("agent value ",agent_value)
                if agent_value != "":
                    is_active_agent = True
                    # is this active agent associated with a word in target language?
                    try:
                        agent_target =  knowledge_graph[entry_index]["recording_data"]["concept_words"][agent_value]
                    except:
                        print("problem retrieving agent target for concept {}, kg entry {}".format(concept, entry_index))
                        agent_target = ""
                    agent_target_list = agent_target.split("...")
                    agent_target_pos_word = agent_target_list[0]
                    #print("agent_target_pos_word ",agent_target_pos_word)

                    if agent_target_pos_word != "":
                        if agent_target_pos_word in target_words:
                            agent_position = target_words.index(agent_target_pos_word)
                            #print("agent_position ",agent_position)
                        else:
                            print("Simple Inference AGENT_TARGET NOT IN TARGET_WORDS: agent_target {} not in target_words {}".format(agent_target_pos_word, target_words))

                # checking now if this event has a patient
                for option in graph[concept]["requires"]:
                    if option[-7:] == "PATIENT":
                        is_patient_required = True

                if is_patient_required:
                    # is there an active patient in this sentence?
                    patient_key = concept + " PATIENT"
                    #print("patient_key ",patient_key)
                    try:
                        patient_value = graph[graph[patient_key]["requires"][0]]["value"]
                        #print("patient_value ",patient_value)
                    except:
                        print("exception caught in determining patient_value in analyze_word_order, entry {}".format(entry_index))
                    if patient_value != "":
                        is_active_patient = True
                        # is this active agent associated with a word in target language?
                        if patient_value in knowledge_graph[entry_index]["recording_data"]["concept_words"] :
                            patient_target = knowledge_graph[entry_index]["recording_data"]["concept_words"][patient_value]
                            patient_target_list = patient_target.split("...")
                            patient_target_pos_word = patient_target_list[0]

                            if patient_target_pos_word != "":
                                if patient_target_pos_word in target_words:
                                    patient_position = target_words.index(patient_target_pos_word)
                                else:
                                    print("Simple Inference PATIENT TARGET NOT IN TARGET WORDS: patient_target {} not in target_words {}".format(
                                        patient_target_pos_word, target_words))
                        else:
                            print("CQ EPA order Observer WARNING: patient_value {} not found in {}".format(patient_value, knowledge_graph[entry_index]["recording_data"]["concept_words"]))


            if is_event:
                # intransitive event with known positions
                if event_position != -1 and agent_position != -1 and not is_patient_required:
                    if event_position < agent_position:
                        ord = "ea_"
                        info_dict["index_lists_by_order"]["ea_"].append(entry_index)
                        info_dict["signature_list_by_order"]["ea_"].append(kgu.get_kg_entry_signature(knowledge_graph, entry_index))
                    else:
                        ord = "ae_"
                        info_dict["index_lists_by_order"]["ae_"].append(entry_index)
                        info_dict["signature_list_by_order"]["ae_"].append(kgu.get_kg_entry_signature(knowledge_graph, entry_index))
                    info_dict["intransitive"].append(
                        {"entry": entry_index,
                         "event_position": event_position,
                         "agent_position": agent_position,
                         "order": ord
                        }
                    )
                # transitive event with known positions
                if event_position != -1 and agent_position != -1 and patient_position != -1:
                    positions = {
                        'e': event_position,
                        'a': agent_position,
                        'p': patient_position
                    }
                    # Sort the positions
                    sorted_order = sorted(positions.items(), key=lambda x: x[1])
                    # Create the acronym
                    order = ''.join([item[0] for item in sorted_order])
                    info_dict["index_lists_by_order"][order].append(entry_index)
                    info_dict["signature_list_by_order"][order].append(kgu.get_kg_entry_signature(knowledge_graph, entry_index))

                    info_dict["transitive"].append(
                        {"entry": entry_index,
                         "event_position": event_position,
                         "agent_position": agent_position,
                         "patient_position": patient_position,
                         "order": order
                         }
                    )
    # now we add statistics
    ea = 0
    ae = 0
    for item in info_dict["intransitive"]:
        if item["order"] == "ea_":
            ea += 1
        else:
            ae += 1
    if len(info_dict["intransitive"]) != 0:
        info_dict["stats"]["intransitive_word_order"] = {
            "ea_": ea,
            "ae_": ae
        }
    else:
        info_dict["stats"]["intransitive_word_order"] = {
            "ea_": None,
            "ae_": None
        }
    count_dict = {
    "epa": 0,
    "eap": 0,
    "aep": 0,
    "ape": 0,
    "pea": 0,
    "pae": 0
    }
    for item in info_dict["transitive"]:
        count_dict[item["order"]] += 1

    info_dict["stats"]["transitive_word_order"] = count_dict

    return info_dict