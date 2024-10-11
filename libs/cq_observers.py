from collections import defaultdict
import json
from libs import knowledge_graph_utils as kgu, stats, wals_utils as wu
import copy

def observer_order_of_subject_and_verb(transcriptions, language, delimiters, canonical=False):
    output_dict = {
        "ppk": "82",
        "agent-ready observation": {},
        "observations": {
            "SV": {
                "depk": "390",
                "count": 0,
                "details": {}
            },
            "VS": {
                "depk": "391",
                "count": 0,
                "details": {}
            },
            "No dominant order": {
                "depk": "392",
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
            is_patient_required = False
            agent_position = -1
            event_position = -1
            # is the entry an event with required agent? if event, get info
            for option in graph[concept]["requires"]:
                # is this concept an event? If yes it accepts an agent
                if option[-5:] == "AGENT":
                    is_event = True

                    # is there a target word associated with this event?
                    try:
                        event_target = transcriptions[entry_index]["recording_data"]["concept_words"][concept]
                        if event_target != "":
                            # targets are words separated by "..." in case of multi-word concepts.
                            # when that happens, we recover the list and take the lowest index in the sentence as the position.
                            # TODO: implement smarter word order logic
                            event_target_list = event_target.split("...")
                            event_target_pos_word = event_target_list[0]
                            # print("event_target_pos_word ",event_target_pos_word)
                            if event_target_pos_word in target_words:
                                # print("{} in target words {} ".format(event_target_pos_word, target_words))
                                event_position = target_words.index(event_target_pos_word)
                            else:
                                print(
                                    "Simple Inference TARGET POS WORD NOT IN TARGET WORDS: entry: {}, event_target_pos_word {} not in target_words {}".format(
                                        entry_index, event_target_pos_word, target_words))
                    except KeyError:
                        print(
                            "problem with concept {} in entry {}, not in concept_words {}".format(concept, entry_index,
                                                                                                  transcriptions[
                                                                                                      entry_index][
                                                                                                      "recording_data"][
                                                                                                      "concept_words"]))

            if is_event:
                # search for an active agent and potential target word(s)
                agent_key = concept + " AGENT"
                # retrieving the agent requires to pass through the AGENT REFERENCE TO CONCEPT node.
                # TODO: make that more failproof
                try:
                    agent_value = graph[graph[agent_key]["requires"][0]]["value"]
                except:
                    agent_value = ""
                    print("exception caught in determining agent_value in analyze_word_order in entry {}".format(
                        entry_index))
                if agent_value != "":
                    # is this active agent associated with a word in target language?
                    try:
                        agent_target = transcriptions[entry_index]["recording_data"]["concept_words"][agent_value]
                    except:
                        # print("problem retrieving agent target for concept {}, kg entry {}".format(concept, entry_index))
                        agent_target = ""
                    agent_target_list = agent_target.split("...")
                    agent_target_pos_word = agent_target_list[0]

                    if agent_target_pos_word != "":
                        if agent_target_pos_word in target_words:
                            agent_position = target_words.index(agent_target_pos_word)
                        else:
                            print("AGENT_TARGET NOT IN TARGET_WORDS: agent_target {} not in target_words {}".format(
                                agent_target_pos_word, target_words))

                # checking now if this event has a patient
                for option in graph[concept]["requires"]:
                    if option[-7:] == "PATIENT":
                        is_patient_required = True

                # looking for intransitive events with known positions
                if event_position != -1 and agent_position != -1 and not is_patient_required:
                    if event_position < agent_position:
                        order = "VS"
                        output_dict["observations"]["VS"]["details"][entry_index] = kgu.get_kg_entry_signature(transcriptions, entry_index)
                    else:
                        order = "SV"
                        output_dict["observations"]["SV"]["details"][entry_index] = kgu.get_kg_entry_signature(transcriptions, entry_index)

    for order in output_dict["observations"].keys():
        output_dict["observations"][order]["count"] = len(output_dict["observations"][order]["details"].keys())
    # creating agent-ready observation
    agent_obs = {}
    for order in output_dict["observations"].keys():
        agent_obs[output_dict["observations"][order]["depk"]] = output_dict["observations"][order]["count"]
    output_dict["agent-ready observation"] = agent_obs

    if canonical:
        # Keep only canonical sentences
        canonical_output = copy.deepcopy(output_dict)
        for de in output_dict["observations"].keys():
            for k, d in output_dict["observations"][de]["details"].items():
                if "ASSERT" not in d["intent"]:
                    del (canonical_output["observations"][de]["details"][k])
        for order in canonical_output["observations"].keys():
            depk = canonical_output["observations"][order]["depk"]
            count = len(canonical_output["observations"][order]["details"])
            canonical_output["agent-ready observation"][depk] = count
        output_dict = canonical_output

    return output_dict



def observer_order_of_subject_object_verb(transcriptions, language, delimiters, canonical=False):
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
                    # is there a target word associated with this event?
                    try:
                        event_target = transcriptions[entry_index]["recording_data"]["concept_words"][concept]
                        if event_target != "":
                            # targets are words separated by "..." in case of multi-word concepts.
                            # when that happens, we recover the list and take the lowest index in the sentence as the position.
                            # TODO: implement smarter word order logic
                            event_target_list = event_target.split("...")
                            event_target_pos_word = event_target_list[0]
                            if event_target_pos_word in target_words:
                                event_position = target_words.index(event_target_pos_word)
                            else:
                                print("Simple Inference TARGET POS WORD NOT IN TARGET WORDS: entry: {}, event_target_pos_word {} not in target_words {}".format(entry_index, event_target_pos_word,target_words))
                    except KeyError:
                        print("problem with concept {} in entry {}, not in concept_words {}".format(concept, entry_index, transcriptions[entry_index]["recording_data"]["concept_words"]))

            if is_event:
                # search for an active agent and potential target word(s)
                agent_key = concept + " AGENT"
                # retrieving the agent requires to pass through the AGENT REFERENCE TO CONCEPT node.
                # TODO: make that more failproof
                try:
                    agent_value = graph[graph[agent_key]["requires"][0]]["value"]
                except:
                    agent_value = ""
                    print("exception caught in determining agent_value in analyze_word_order in entry {}".format(entry_index))
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

                    if agent_target_pos_word != "":
                        if agent_target_pos_word in target_words:
                            agent_position = target_words.index(agent_target_pos_word)
                        else:
                            print("AGENT_TARGET NOT IN TARGET_WORDS: agent_target {} not in target_words {}".format(agent_target_pos_word, target_words))

                # checking now if this event has a patient
                for option in graph[concept]["requires"]:
                    if option[-7:] == "PATIENT":
                        is_patient_required = True

                if is_patient_required:
                    # is there an active patient in this sentence?
                    patient_key = concept + " PATIENT"
                    try:
                        patient_value = graph[graph[patient_key]["requires"][0]]["value"]
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

    if canonical:
        # Keep only canonical sentences
        canonical_output = copy.deepcopy(output_dict)
        for de in output_dict["observations"].keys():
            for k, d in output_dict["observations"][de]["details"].items():
                if "ASSERT" not in d["intent"]:
                    del (canonical_output["observations"][de]["details"][k])
        for order in canonical_output["observations"].keys():
            depk = canonical_output["observations"][order]["depk"]
            count = len(canonical_output["observations"][order]["details"])
            canonical_output["agent-ready observation"][depk] = count
            canonical_output["observations"][order]["count"] = count
        output_dict = canonical_output

    return output_dict



def observer_order_of_adjective_and_noun(knowledge_graph, language, delimiters, canonical=False):
    output_dict = {
        "ppk": "87",
        "agent-ready observation": {},
        "observations": {
            "Adjective-Noun": {
                "depk": "410",
                "count": 0,
                "details": {}
            },
            "Noun-Adjective": {
                "depk": "411",
                "count": 0,
                "details": {}
            },
            "No dominant order": {
                "depk": "412",
                "count": 0,
                "details": {}
            },
            "Only internally-headed relative clauses": {
                "depk": "413",
                "count": 0,
                "details": {}
            }
        }
    }
    for entry_index, entry_data in knowledge_graph.items():
        sentence_data = entry_data.get('sentence_data', {})
        sentence_graph = sentence_data.get('graph', {})
        # build a list of the target words for position reference
        target_words = stats.custom_split(knowledge_graph[entry_index]["recording_data"]["translation"], delimiters)

        for concept in sentence_graph:
            if concept + " DEFINITENESS" in sentence_graph[concept]["requires"]:
                # this concept is a noun
                try:
                    if sentence_graph[concept + " QUALIFIER REFERENCE TO CONCEPT"]["value"] != "":
                        # this noun has a non-empty qualifier, are there target words linked?
                        noun_pos = -1
                        adj_pos = -1
                        concept_word_pos = kgu.get_concept_word_pos(knowledge_graph, entry_index, delimiters)
                        if concept in concept_word_pos.keys():
                            noun_pos = concept_word_pos[concept]["pos"]
                        if sentence_graph[concept + " QUALIFIER REFERENCE TO CONCEPT"]["value"] in concept_word_pos.keys():
                            adj_pos = concept_word_pos[sentence_graph[concept + " QUALIFIER REFERENCE TO CONCEPT"]["value"]]["pos"]
                        if noun_pos != -1 and adj_pos != -1:
                            if adj_pos < noun_pos:
                                output_dict["observations"]["Adjective-Noun"]["details"][entry_index] = kgu.get_kg_entry_signature(
                                knowledge_graph, entry_index)
                            if noun_pos < adj_pos:
                                output_dict["observations"]["Noun-Adjective"]["details"][
                                    entry_index] = kgu.get_kg_entry_signature(
                                    knowledge_graph, entry_index)
                except KeyError:
                    print("Key Error, {} not in sentence graph for concept {}".format(concept + " QUALIFIER REFERENCE TO CONCEPT", concept))

        for order in output_dict["observations"].keys():
            output_dict["observations"][order]["count"] = len(output_dict["observations"][order]["details"].keys())
        # creating agent-ready observation
        agent_obs = {}
        for order in output_dict["observations"].keys():
            agent_obs[output_dict["observations"][order]["depk"]] = output_dict["observations"][order]["count"]
        output_dict["agent-ready observation"] = agent_obs

        if canonical:
            # Keep only canonical sentences
            canonical_output = copy.deepcopy(output_dict)
            for de in output_dict["observations"].keys():
                for k, d in output_dict["observations"][de]["details"].items():
                    if "ASSERT" not in d["intent"]:
                        del (canonical_output["observations"][de]["details"][k])
            for order in canonical_output["observations"].keys():
                depk = canonical_output["observations"][order]["depk"]
                count = len(canonical_output["observations"][order]["details"])
                canonical_output["agent-ready observation"][depk] = count
            output_dict = canonical_output

    if canonical:
        # Keep only canonical sentences
        canonical_output = copy.deepcopy(output_dict)
        for de in output_dict["observations"].keys():
            for k, d in output_dict["observations"][de]["details"].items():
                if "ASSERT" not in d["intent"]:
                    del (canonical_output["observations"][de]["details"][k])
        for order in canonical_output["observations"].keys():
            depk = canonical_output["observations"][order]["depk"]
            count = len(canonical_output["observations"][order]["details"])
            canonical_output["agent-ready observation"][depk] = count
        output_dict = canonical_output

    return output_dict





