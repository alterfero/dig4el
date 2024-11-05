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

from collections import defaultdict
import json
from libs import knowledge_graph_utils as kgu, stats, wals_utils as wu
import copy

def observer_order_of_subject_and_verb(knowledge_graph, language, delimiters, canonical=False):
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

    key_data = [
        {"pivot_sentence": "They died before I was born.",
         "agent": "PP3DU",
         "event": "dying"},
        {"pivot_sentence": "They were born a long time ago.",
         "agent": "PP3DU",
         "event": "being born"},
        {"pivot_sentence": "I guess she was coming back from school",
         "agent": "PP3SG",
         "event": "coming"},
        {"pivot_sentence": "He lives far away from here.",
         "agent": "PP3SG",
         "event": "residing"},
        {"pivot_sentence": "But I’m not a child any more, I’ve grown up.",
         "agent": "PP1SG",
         "event": "growing up"},
        {"pivot_sentence": "I can’t sleep well at night.",
         "agent": "PP1SG",
         "event": "sleeping"},
        {"pivot_sentence": "I sweat",
         "agent": "PP1SG",
         "event": "sweating"},
        {"pivot_sentence": "and then I wake up in the middle of the night.",
         "agent": "PP1SG",
         "event": "waking up"},
        {"pivot_sentence": "Do you cough?",
         "agent": "PP2SG",
         "event": "coughing"},
        {"pivot_sentence": "No, I don’t cough.",
         "agent": "PP1SG",
         "event": "coughing"},
        {"pivot_sentence": "But every time I wake up, I’m very thirsty.",
         "agent": "PP1SG",
         "event": "waking up"},
        {"pivot_sentence": "Doctor, I’m a bit worried.",
         "agent": "PP1SG",
         "event": "experiencing in the body"},
        {"pivot_sentence": "Last week, my child came back from the forest with some strange fruit I had never seen.",
         "agent": "children",
         "event": "coming"},
        {"pivot_sentence": "Well, we’re walking down to the river, over there.",
         "agent": "PP1EXCDU",
         "event": "walking"},
        {"pivot_sentence": "Are you going to be bathing?",
         "agent": "PP2DU",
         "event": "bathing"},
        {"pivot_sentence": "No, no! We won’t be bathing.",
         "agent": "PP1EXCDU",
         "event": "bathing"},
        {"pivot_sentence": "This time, the people from village X will all be coming to our community.",
         "agent": "people",
         "event": "coming"},
        {"pivot_sentence": "Then, people will play in the morning.",
         "agent": "people",
         "event": "play"},
        {"pivot_sentence": "And then, in the late afternoon, our two communities will part again.",
         "agent": "communities",
         "event": "parting"}
    ]

    for item in key_data:
        # build a list of the target words for position reference
        target_words = stats.custom_split(item["pivot_sentence"], delimiters)
        kg_data = kgu.get_kg_entry_from_pivot_sentence(knowledge_graph, item["pivot_sentence"])
        if kg_data != {}:
            concept_words_pos = kgu.get_concept_word_pos(knowledge_graph, kg_data["entry_index"], delimiters)
            if item["agent"] in concept_words_pos and item["event"] in concept_words_pos:
                positions = {
                    'V': concept_words_pos[item["event"]]["pos"],
                    'S': concept_words_pos[item["agent"]]["pos"],
                }
                # Sort the positions
                sorted_order = sorted(positions.items(), key=lambda x: x[1])
                # Create the acronym
                order = ''.join([item[0] for item in sorted_order])

                output_dict["observations"][order]["details"][kg_data["entry_index"]] = kgu.get_kg_entry_signature(knowledge_graph,
                                                                                                        kg_data["entry_index"])

    # add counts
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
                if "ASSERT" not in d["intent"] or d["polarity"] is False:
                    del (canonical_output["observations"][de]["details"][k])
        for order in canonical_output["observations"].keys():
            depk = canonical_output["observations"][order]["depk"]
            count = len(canonical_output["observations"][order]["details"])
            canonical_output["agent-ready observation"][depk] = count
            canonical_output["observations"][order]["count"] = count
        output_dict = canonical_output

    return output_dict

def observer_order_of_subject_object_verb(knowledge_graph, language, delimiters, canonical=False):
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

    key_data = [
        {"pivot_sentence": "Have you ever seen pictures of my family?",
         "agent": "PP2SG",
         "event": "seeing",
         "patient": "picture"},
        {"pivot_sentence": "Well, I’ve met some of your relatives, but I’ve never seen your pictures.",
         "agent": "PP1SG",
         "event": "meeting",
         "patient": "relatives"},
        {"pivot_sentence": "Here is an old photo album I just found in my parents’ room.",
         "agent": "PP1SG",
         "event": "finding",
         "patient": "photo album"},
        {"pivot_sentence": "Oh, show it to me please!",
         "agent": "PP2SG",
         "event": "showing",
         "patient": "Ref_1_object"},
        {"pivot_sentence": "People would wear beautiful clothes.",
         "agent": "people",
         "event": "wearing",
         "patient": "clothes"},
        {"pivot_sentence": "Have you met them?",
         "agent": "PP2SG",
         "event": "meeting",
         "patient": "PP3DU"},
        {"pivot_sentence": "You’ve never met him.",
         "agent": "PP2SG",
         "event": "meeting",
         "patient": "PP3SG"},
        {"pivot_sentence": "And what school did they attend then?",
         "agent": "PP3DU",
         "event": "attending",
         "patient": "school"},
        {"pivot_sentence": "Oh, I think I know who this child is.",
         "agent": "PP1SG",
         "event": "thinking",
         "patient": "knowing"},
        {"pivot_sentence": "How did you recognize me?",
         "agent": "PP2SG",
         "event": "recognizing",
         "patient": "PP1SG"},
        {"pivot_sentence": "but I recognize your eyes and your smile.",
         "agent": "PP1SG",
         "event": "recognizing",
         "patient": "eyes"},
        {"pivot_sentence": "I have nightmares.",
         "agent": "PP1SG",
         "event": "experiencing in the body",
         "patient": "nightmare"},
        {"pivot_sentence": "Sometimes I feel hot",
         "agent": "PP1SG",
         "event": "experiencing in the body",
         "patient": "hot"},
        {"pivot_sentence": "sometimes I feel cold",
         "agent": "PP1SG",
         "event": "experiencing in the body",
         "patient": "cold"},
        {"pivot_sentence": "I feel I need to drink.",
         "agent": "PP1SG",
         "event": "experiencing in the body",
         "patient": "needing"},
        {"pivot_sentence": "I don't know why.",
         "agent": "PP1SG",
         "event": "knowing",
         "patient": "causality wildcard"},
        {"pivot_sentence": "Have you eaten something particular lately?",
         "agent": "PP2SG",
         "event": "eating",
         "patient": "object wildcard"},
        {"pivot_sentence": "He gave me the fruits to try.",
         "agent": "PP3SG",
         "event": "giving",
         "patient": "fruit"},
        {"pivot_sentence": "Actually I liked them.",
         "agent": "PP1SG",
         "event": "liking",
         "patient": "Ref_many_objects"},
        {"pivot_sentence": "I ate many of them.",
         "agent": "PP1SG",
         "event": "eating",
         "patient": "Ref_many_objects"},
        {"pivot_sentence": "I’ll give you some medicine to drink.",
         "agent": "PP1SG",
         "event": "giving",
         "patient": "medicine"},
        {"pivot_sentence": "You need to sleep.",
         "agent": "PP2SG",
         "event": "needing",
         "patient": "sleeping"},
        {"pivot_sentence": "We’ll try to catch some river fish for dinner.",
         "agent": "PP1EXCDU",
         "event": "trying",
         "patient": "fish"},
        {"pivot_sentence": "We just need food for our family.",
         "agent": "PP1EXCDU",
         "event": "needing",
         "patient": "food"},
        {"pivot_sentence": "My wife had bought a chicken at the market the other day",
         "agent": "wife",
         "event": "buying",
         "patient": "chicken"},
        {"pivot_sentence": "but our children ate it all already",
         "agent": "children",
         "event": "eating",
         "patient": "Ref_1_object"},
        {"pivot_sentence": "now we have nothing left at home!",
         "agent": "PP1EXCDU",
         "event": "possessing",
         "patient": "nothing left"},
        {"pivot_sentence": "Besides, we don’t have enough money anymore.",
         "agent": "PP1EXCDU",
         "event": "possessing",
         "patient": "money"},
        {"pivot_sentence": "I’m sorry that you have no food left.",
         "agent": "PP2PLU",
         "event": "possessing",
         "patient": "food"},
        {"pivot_sentence": "My husband and I, we have lots of vegetables from our garden.",
         "agent": "PP1EXCDU",
         "event": "possessing",
         "patient": "vegetables"},
        {"pivot_sentence": "If you want, we can give you some.",
         "agent": "PP1EXCDU",
         "event": "giving",
         "patient": "Ref_many_objects"},
        {"pivot_sentence": "You’ll give us some vegetables",
         "agent": "PP2DU",
         "event": "giving",
         "patient": "vegetables"},
        {"pivot_sentence": "and we’ll give you some fish.",
         "agent": "PP1EXCDU",
         "event": "giving",
         "patient": "fish"},
        {"pivot_sentence": "After that, we’ll all share lunch together.",
         "agent": "PP1PLU",
         "event": "sharing",
         "patient": "lunch"},
        {"pivot_sentence": "In the afternoon, I hope we can have songs and dances.",
         "agent": "PP1SG",
         "event": "hoping",
         "patient": "songs"},
        {"pivot_sentence": "The people of X will sing their songs, dance their dances;",
         "agent": "people",
         "event": "singing",
         "patient": "songs"},
        {"pivot_sentence": "we too, we shall sing our own songs, and do our own dances…",
         "agent": "PP1PLU",
         "event": "singing",
         "patient": "songs"},
        {"pivot_sentence": "Everyone loves music and dance.",
         "agent": "everyone",
         "event": "loving",
         "patient": "music"},
        {"pivot_sentence": "Then our elders will tell stories from the olden times, for the young to hear.",
         "agent": "elders",
         "event": "telling",
         "patient": "stories"},
        {"pivot_sentence": "They know so many stories.",
         "agent": "PP3PLU",
         "event": "knowing",
         "patient": "stories"},
        {"pivot_sentence": "We should organize a meeting tomorrow morning in the community to tell our people what they should do",
         "agent": "PP1INCDU",
         "event": "organizing",
         "patient": "meeting"},
        {"pivot_sentence": "Some of us will clean the village",
         "agent": "PP1PLU",
         "event": "cleaning",
         "patient": "village"},
        {"pivot_sentence": "Other people will make the costumes for the dances.",
         "agent": "people",
         "event": "making",
         "patient": "costume"},
        {"pivot_sentence": "We must choose dances to showcase",
         "agent": "PP1PLU",
         "event": "choosing",
         "patient": "dances"},
        {"pivot_sentence": "and we must rehearse them",
         "agent": "PP1PLU",
         "event": "rehearsing",
         "patient": "Ref_many_objects"},
        {"pivot_sentence": "we’ll have to prepare enough food for two hundred people.",
         "agent": "PP1PLU",
         "event": "preparing",
         "patient": "food"},
        {"pivot_sentence": "Brother, have you seen my notebook?",
         "agent": "PP2SG",
         "event": "seeing",
         "patient": "notebook"},
        {"pivot_sentence": "I’ve been looking for it everywhere, but I can’t find it!",
         "agent": "PP1SG",
         "event": "searching",
         "patient": "Ref_1_object"},
        {"pivot_sentence": "You’ve seen it already.",
         "agent": "PP2SG",
         "event": "seeing",
         "patient": "Ref_1_object"},
        {"pivot_sentence": "I was doing my homework on it last night in the dining room.",
         "agent": "PP1SG",
         "event": "doing",
         "patient": "homework"},
        {"pivot_sentence": "I put it away in my schoolbag before I went to sleep.",
         "agent": "PP1SG",
         "event": "putting",
         "patient": "Ref_1_object"},
        {"pivot_sentence": "I can't find it.",
         "agent": "PP1SG",
         "event": "being able to",
         "patient": "finding"},
        {"pivot_sentence": "But I need it for my math class today!",
         "agent": "PP1SG",
         "event": "needing",
         "patient": "Ref_1_object"},
        {"pivot_sentence": "The teacher will be quite angry if I don’t have my notebook.",
         "agent": "PP1SG",
         "event": "possessing",
         "patient": "notebook"},
        {"pivot_sentence": "He will think I didn’t do my homework.",
         "agent": "PP3SG",
         "event": "thinking",
         "patient": "doing"},
        {"pivot_sentence": "He will think I didn’t do my homework.",
         "agent": "PP1SG",
         "event": "doing",
         "patient": "homework"},
        {"pivot_sentence": "Uh oh… I think I found it!",
         "agent": "PP1SG",
         "event": "finding",
         "patient": "Ref_1_object"},
        {"pivot_sentence": "What is he holding in his hands?",
         "agent": "PP3SG",
         "event": "holding",
         "patient": "object wildcard"},
        {"pivot_sentence": "But he has shredded it into pieces!",
         "agent": "PP3SG",
         "event": "shredding",
         "patient": "Ref_1_object"},
        {"pivot_sentence": "Now I need to buy a new notebook",
         "agent": "PP1SG",
         "event": "buying",
         "patient": "noteboook"},
        {"pivot_sentence": "and I need to start my work all over again.",
         "agent": "PP1SG",
         "event": "starting",
         "patient": "homework"}
    ]

    for item in key_data:
        # build a list of the target words for position reference
        target_words = stats.custom_split(item["pivot_sentence"], delimiters)
        kg_data = kgu.get_kg_entry_from_pivot_sentence(knowledge_graph, item["pivot_sentence"])
        if kg_data != {}:
            concept_words_pos = kgu.get_concept_word_pos(knowledge_graph, kg_data["entry_index"], delimiters)
            if item["agent"] in concept_words_pos and item["event"] in concept_words_pos and item["patient"] in concept_words_pos:
                positions = {
                    'V': concept_words_pos[item["event"]]["pos"],
                    'S': concept_words_pos[item["agent"]]["pos"],
                    'O': concept_words_pos[item["patient"]]["pos"]
                }
                # Sort the positions
                sorted_order = sorted(positions.items(), key=lambda x: x[1])
                # Create the acronym
                order = ''.join([item[0] for item in sorted_order])

                output_dict["observations"][order]["details"][kg_data["entry_index"]] = kgu.get_kg_entry_signature(knowledge_graph,
                                                                                                        kg_data["entry_index"])

    # add counts
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
                if "ASSERT" not in d["intent"] or d["polarity"] is False:
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
                    if "ASSERT" not in d["intent"] or d["polarity"] is False:
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

def observer_order_of_demonstrative_and_noun(knowledge_graph, language, delimiters, canonical=False):
    output_dict = {
        "ppk": "88",
        "agent-ready observation": {},
        "observations": {
            "Demonstrative-Noun": {
                "depk": "648",
                "count": 0,
                "details": {}
            },
            "Noun-Demonstrative": {
                "depk": "649",
                "count": 0,
                "details": {}
            },
            "Demonstrative prefix": {
                "depk": "650",
                "count": 0,
                "details": {}
            },
            "Demonstrative suffix": {
                "depk": "651",
                "count": 0,
                "details": {}
            },
            "Demonstrative before and after Noun": {
                "depk": "652",
                "count": 0,
                "details": {}
            },
            "Mixed": {
                "depk": "653",
                "count": 0,
                "details": {}
            }
        }
    }
    # retrieve KG items with demonstrative and noun
    key_data = [
        {"pivot_sentence": "Who’s this on that first photo?",
         "demonstrative_concept": "POINTED BY SPEAKER",
         "noun_concept": "photo"},
        {"pivot_sentence": "Let me see this other photo.",
         "demonstrative_concept": "POINTED BY SPEAKER",
         "noun_concept": "picture"},
        {"pivot_sentence": "This woman is surely your mother again, carrying a child on her back.",
         "demonstrative_concept": "POINTED BY SPEAKER",
         "noun_concept": "women"},
        {"pivot_sentence": "Oh, I think I know who this child is.",
         "demonstrative_concept": "POINTED BY SPEAKER",
         "noun_concept": "children"}
    ]

    for item in key_data:
        kg_data = kgu.get_kg_entry_from_pivot_sentence(knowledge_graph, item["pivot_sentence"])
        if kg_data != {}:
            concept_words_pos = kgu.get_concept_word_pos(knowledge_graph, kg_data["entry_index"], delimiters)
            if item["demonstrative_concept"] in concept_words_pos.keys() and item["noun_concept"] in concept_words_pos.keys():
                pos_dem = concept_words_pos[item["demonstrative_concept"]]["pos"]
                pos_noun = concept_words_pos[item["noun_concept"]]["pos"]
                if pos_dem < pos_noun:
                    output_dict["observations"]["Demonstrative-Noun"]["details"][kg_data["entry_index"]] = kgu.get_kg_entry_signature(knowledge_graph, kg_data["entry_index"])
                    output_dict["observations"]["Demonstrative-Noun"]["count"] +=1
                elif pos_dem > pos_noun:
                    output_dict["observations"]["Noun-Demonstrative"]["details"][kg_data["entry_index"]] = kgu.get_kg_entry_signature(knowledge_graph, kg_data["entry_index"])
                    output_dict["observations"]["Noun-Demonstrative"]["count"] += 1

    # creating agent-ready observation
    agent_obs = {}
    for order in output_dict["observations"].keys():
        agent_obs[output_dict["observations"][order]["depk"]] = output_dict["observations"][order]["count"]
    output_dict["agent-ready observation"] = agent_obs

    return output_dict

def observer_order_of_relative_clause_and_noun(knowledge_graph, language, delimiters, canonical=False):
    output_dict = {
        "ppk": "90",
        "agent-ready observation": {},
        "observations": {
            "Noun-Relative clause": {
                "depk": "418",
                "count": 0,
                "details": {}
            },
            "Relative clause-Noun": {
                "depk": "419",
                "count": 0,
                "details": {}
            },
            "Internally headed": {
                "depk": "420",
                "count": 0,
                "details": {}
            },
            "Correlative": {
                "depk": "421",
                "count": 0,
                "details": {}
            },
            "Adjoined": {
                "depk": "422",
                "count": 0,
                "details": {}
            },
            "Doubly headed": {
                "depk": "423",
                "count": 0,
                "details": {}
            },
            "Mixed": {
                "depk": "424",
                "count": 0,
                "details": {}
            }
        }
    }
    # retrieve KG items with noun and relative clause
    key_data = [
        {"pivot_sentence": "That was an old school that doesn’t exist anymore.",
         "relative_marker": "Ref_1_object",
         "head": "school"},
        {"pivot_sentence": "Here is an old photo album I just found in my parents’ room.",
         "relative_marker": "PP1SG",
         "head": "photo album"},
        {"pivot_sentence": "Last week, my child came back from the forest with some strange fruit I had never seen.",
         "relative_marker": "PP1SG",
         "head": "fruit"},
        {"pivot_sentence": "It must have been these fruits that made you sick.",
         "relative_marker": "Ref_many_objects",
         "head": "fruit"}
    ]

    for item in key_data:
        kg_data = kgu.get_kg_entry_from_pivot_sentence(knowledge_graph, item["pivot_sentence"])
        if kg_data != {}:
            concept_words_pos = kgu.get_concept_word_pos(knowledge_graph, kg_data["entry_index"], delimiters)
            #print(concept_words_pos)
            if item["relative_marker"] in concept_words_pos.keys() and item["head"] in concept_words_pos.keys():
                pos_rel = concept_words_pos[item["relative_marker"]]["pos"]
                pos_head = concept_words_pos[item["head"]]["pos"]
                if pos_head < pos_rel:
                    output_dict["observations"]["Noun-Relative clause"]["details"][kg_data["entry_index"]] = kgu.get_kg_entry_signature(knowledge_graph, kg_data["entry_index"])
                    output_dict["observations"]["Noun-Relative clause"]["count"] +=1
                elif pos_rel > pos_head:
                    output_dict["observations"]["Relative clause-Noun"]["details"][kg_data["entry_index"]] = kgu.get_kg_entry_signature(knowledge_graph, kg_data["entry_index"])
                    output_dict["observations"]["Relative clause-Noun"]["count"] += 1

    # creating agent-ready observation
    agent_obs = {}
    for order in output_dict["observations"].keys():
        agent_obs[output_dict["observations"][order]["depk"]] = output_dict["observations"][order]["count"]
    output_dict["agent-ready observation"] = agent_obs

    return output_dict


# General approach, not precise enough yet
def zzz_observer_order_of_subject_object_verb(transcriptions, language, delimiters, canonical=False):
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
                        if patient_value in transcriptions[entry_index]["recording_data"]["concept_words"]:
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
                    #print("index {}, event {} ({}), agent {} ({}), patient {} ({})".format(entry_index+1, event_target, event_position,
                    #                                                                     agent_target, agent_position,
                    #                                                                       patient_target, patient_position))
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
def zzz_observer_order_of_subject_and_verb(transcriptions, language, delimiters, canonical=False):
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