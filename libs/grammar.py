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

import random
from libs import evolutionary_utils as eu

AVAILABLE_INTRINSIC_TRAITS = {
            "animacy": ["human", "animate non-human", "inanimate"],
            "gender": ["male", "female", "neutral"]
        }
AVAILABLE_PARTICULARIZATION_OPTIONS = {
                "intent": {"intent": ["ASSERT", "ORDER", "ASK", "none"]},
                "context": {"speaker_gender": ["male", "female", "neutral", "none"],
                            "speaker_age": ["child", "adult", "elder", "none"],
                            "listener_gender": ["male", "female", "neutral", "none"],
                            "politeness": ["one_up", "one_down", "deferential", "neutral", "none"]},
                "internal_particularization": {
                            "DEFINITENESS": ["definite", "indefinite", "generic", "none"],
                            "NUMBER": ["singular", "dual", "trial", "plural", "none"],
                            "ASPECT": ["perfect", "progressive", "habitual", "none"],
                            "TENSE": ["past", "present", "future", "none"]
                            },
                "relational_particularization": {
                            "SEMANTIC ROLE": ["AGENT", "PATIENT", "OBLIQUE"],
                            "POSSESSION": ["None", "POSSESSOR", "POSSESSEE"]}
                }
AVAILABLE_SYNTACTIC_INTERNAL_PARTICULARIZATION_OPERATIONS = {
            # Operations that "add" something to the base form
            "add": [
                "nothing",  # No addition
                "add_single_free_morpheme_before_base",
                "add_single_free_morpheme_after_base",
                "add_bound_morpheme_initial",
                "add_bound_morpheme_final"
            ],
            # Transformations applied to the base (stem) itself
            "transform_base": [
                "nothing",
                "reduplicate_base",
                "warp_base"
            ],
            # Move the base within a larger syntactic structure
            "move_base": [
                "nothing",
                "move initial",
                "move final"
            ]
        }
AVAILABLE_SYNTACTIC_RELATIONAL_PARTICULARIZATION_OPERATIONS = {
            # Operations that "add" something to the base form
            "add": [
                "nothing",
                "add_single_free_morpheme_before_base",
                "add_single_free_morpheme_after_base",
                "add_bound_morpheme_initial",
                "add_bound_morpheme_final"
            ],
            # Transformations applied to the base (stem) itself
            "transform_base": [
                "nothing",
                "reduplicate_base",
                "warp_base"
            ],
            # Move the base
            "move_base": [
                "nothing",
                "move_initial",
                "move_final",
                "move_before_parent",
                "move_after_parent"
            ]
        }

def biased_boolean(prob_true=0.5):
    """
    Returns True with probability prob_true,
    and False with probability (1 - prob_true).
    """
    return random.random() < prob_true

class Construction:
    def __init__(self, concept, intrinsic_traits=None):
        self.type = type
        self.concept = concept
        self.corpus = []
        self.concept_type = eu.get_concept_type(concept)
        self.boolean_configuration = None
        self.configuration = None
        # TODO enable intrinsic traits in conceptual graph
        self.available_intrinsic_traits = AVAILABLE_INTRINSIC_TRAITS
        if intrinsic_traits is None:
            self.intrinsic_traits = {
                "animacy": "inanimate",
                "gender": "neutral"
            }
        else:
            self.intrinsic_traits = intrinsic_traits
        self.available_particularization_options = AVAILABLE_PARTICULARIZATION_OPTIONS
        self.available_syntactic_internal_particularization_operations = AVAILABLE_SYNTACTIC_INTERNAL_PARTICULARIZATION_OPERATIONS
        self.available_syntactic_relational_particularization_operations = AVAILABLE_SYNTACTIC_RELATIONAL_PARTICULARIZATION_OPERATIONS

    def initialize_with_random_configuration(self):
        boolean_gram_dict = {}
        param_grammaticalization_dict = {}

        # GRAMMATICALIZED PARAMETERS SELECTION
        def random_ip_op():
            op_cat = random.choice([self.available_syntactic_internal_particularization_operations.keys()])
            return random.choice(self.available_syntactic_internal_particularization_operations[op_cat])
        def random_rp_op():
            op_cat = random.choice([self.available_syntactic_relational_particularization_operations.keys()])
            return random.choice(self.available_syntactic_relational_particularization_operations[op_cat])

        # Enunciation
        boolean_gram_dict["is_speaker_gender_grammaticalized"] = biased_boolean(0.5)
        if boolean_gram_dict["is_speaker_gender_grammaticalized"]:
            for gender in self.available_particularization_options["context"]["speaker_gender"]:
                param_grammaticalization_dict[f"context_speaker_{gender}"] = random_ip_op()
        else:
            for gender in self.available_particularization_options["context"]["speaker_gender"]:
                param_grammaticalization_dict[f"context_speaker_{gender}"] = None
        boolean_gram_dict["is_listener_gender_grammaticalized"] = biased_boolean(0.2)
        if boolean_gram_dict["is_listener_gender_grammaticalized"]:
            for gender in self.available_particularization_options["context"]["listener_gender"]:
                param_grammaticalization_dict[f"context_listener_{gender}"] = random_ip_op()
        else:
            for gender in self.available_particularization_options["context"]["listener_gender"]:
                param_grammaticalization_dict[f"context_listener_{gender}"] = None
        # Intent
        is_intent_grammaticalized = biased_boolean(0.8)
        if is_intent_grammaticalized:
            for intent in self.available_particularization_options["intent"]["intent"]:
                param_grammaticalization_dict[f"intent_{intent}"] = random_ip_op()
        else:
            for intent in self.available_particularization_options["intent"]["intent"]:
                param_grammaticalization_dict[f"intent_{intent}"] = None

        # Intrinsic properties
        boolean_gram_dict["is_intrinsic_gender_grammaticalized"] = biased_boolean(0.5)
        if boolean_gram_dict["is_intrinsic_gender_grammaticalized"]:
            for gender in self.available_intrinsic_traits["gender"]:
                param_grammaticalization_dict[f"intrinsic_gender_{gender}"] = random_ip_op()
        else:
            for gender in self.available_intrinsic_traits["gender"]:
                param_grammaticalization_dict[f"intrinsic_gender_{gender}"] = None
        boolean_gram_dict["is_intrinsic_animacy_grammaticalized"] = biased_boolean(0.8)
        if boolean_gram_dict["is_intrinsic_animacy_grammaticalized"]:
            for option in self.available_intrinsic_traits["animacy"]:
                param_grammaticalization_dict[f"intrinsic_animacy_{option}"] = random_ip_op()
        else:
            for option in self.available_intrinsic_traits["animacy"]:
                param_grammaticalization_dict[f"intrinsic_animacy_{option}"] = None

        # Internal particularization
        for option in self.available_particularization_options["internal_particularization"]:
            boolean_gram_dict[option] = biased_boolean(0.5)
            if boolean_gram_dict[option]:
                for item in self.available_particularization_options["internal_particularization"][option]:
                    param_grammaticalization_dict[f"internal_particularization_{option}_{item}"] = random_ip_op()
            else:
                for item in self.available_particularization_options["internal_particularization"][option]:
                    param_grammaticalization_dict[f"internal_particularization_{option}_{item}"] = None
        # Relational particularization
        for option in self.available_particularization_options["relational_particularization"]:
            boolean_gram_dict[option] = biased_boolean(0.5)
            if boolean_gram_dict[option]:
                for item in self.available_particularization_options["relational_particularization"][option]:
                    param_grammaticalization_dict[f"relational_particularization_{option}_{item}"] = random_rp_op()
            else:
                for item in self.available_particularization_options["relational_particularization"][option]:
                    param_grammaticalization_dict[f"relational_particularization_{option}_{item}"] = None

        # COMBINATIONS
        # not encoding combinations, favoring constraints on words that seem to use combinations.
        # "her" is not PP3 with  (IP singular + intrinsic female + RP patient)
        # It's PP3SG_female with RP patient. Makes more sense and reduces complexity.

        self.boolean_configuration = boolean_gram_dict
        self.configuration = param_grammaticalization_dict

class GrammarIndividual:
    def __init__(self, concepts, training_data):
        self.general_parameters = {
            "Order of Subject, Object and Verb": "VSO"
        }
        self.concepts = concepts
        self.default_intrinsic_traits = {
            "animacy": random.choice(AVAILABLE_INTRINSIC_TRAITS["animacy"]),
            "gender": random.choice(AVAILABLE_INTRINSIC_TRAITS["gender"])
        }
        self.default_particularization_options = {
            "intent": "ASSERT",
            "context": {"speaker_gender": "male",
                        "speaker_age":  "adult",
                        "listener_gender": "male",
                        "politeness": "neutral"},
            "internal_particularization": {
                "DEFINITENESS": random.choice(AVAILABLE_PARTICULARIZATION_OPTIONS["internal_particularization"]["DEFINITENESS"]),
                "NUMBER": "singular",
            },
            "relational_particularization": {
                "SEMANTIC ROLE": "AGENT",
                "POSSESSION": "none"}
        }
        self.training_data = training_data
        self.fitness = None
        self.constructions = None

    def initialize(self):
        #TODO: Initialize general parameters with General Agent
        self.constructions = {}
        c_list = [Construction(c) for c in self.concepts]
        for c in c_list:
            self.constructions[c.concept] = c
        for concept in self.constructions.keys():
            self.constructions[concept].initialize_with_random_configuration()
    def serialize_sentence(self, sentence_data):
        """
        serialize applies constructions behavior to the data graph to generate a written form.
        sentence_data is an entry of training_data
        """
        print("Sentence data: {}".format(sentence_data))
        sentence_items = []
        for concept in sentence_data["concepts"]:
            form = concept[0]
            if concept[0] not in self.concepts:
                form += f"_{concept[1]}_unknown"
            else:
                form += f"_I_{concept[1]}_{'_'.join([self.constructions[concept[0]].intrinsic_traits[i] for i in self.constructions[concept[0]].intrinsic_traits.keys()])}"
                for item in sentence_data["super_concept_graph"]["internal_particularization"]:
                    if item["concept"] == concept:
                        form += f"_IP_{item['feature']}_{item['value']}_TARGET_{item['expression']}"
                for item in sentence_data["super_concept_graph"]["relational_particularization"]:
                    if item["concept"] == concept:
                        form += f"_RP_{item['relation']}_{item['to'][0]}_TARGET_{item['expression']}"
                    elif item["to"] == concept:
                        form += f"_RP_has_{item['relation']}_{item['concept'][0]}"
            sentence_items.append(form)
        # now add syntactic operations





        return sentence_items

class EA:
    def __init__(self, concepts, training_data, n_pop = 10):
        self.concepts = concepts
        self.training_data = training_data
        self.grammar_individuals = []
        self.n_pop = n_pop

    def initialize_population(self):
        print("EA: Initializing population")
        pop = []
        for i in range(self.n_pop):
            self.grammar_individuals.append(GrammarIndividual(self.concepts, self.training_data))
        for gi in self.grammar_individuals:
            gi.initialize()









