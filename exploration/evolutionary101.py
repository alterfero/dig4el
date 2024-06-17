""" agent01 is an intelligent agent specialized in inferring grammatical rules based on conversation questionnaires.
these exploration are used in evolutionary algorithms. each agent has beliefs, which are confronted to any source of insight.
A belief is:  X is expressed as Y in context C.
For example: PP1SG is a word does not vary agent01 knows about usual grammatical expressions of concepts
test on bijection, injection etc."""

from libs import utils as u, graphs_utils as gu, knowledge_graph_utils as kgu

# Typological data ================================================

syntactic_elements = {
    "single specific invariable word" : {
        "paramaters": {
            "concept": "",
            "word": ""
        },
        "test": "test_single_specific_invariable_word"
    }
}

typological_knowledge = {
    "personal pronouns": {
        "can be searched individually": True,
        "can vary with": ["SEMANTIC ROLE", "NUMBER", "GENDER"]
    }

}

# CLASSES ======================
class Belief:
    def __init__(self, concept, expression):
        self.concept = concept
        self.expression = expression

class Agent01:
    def __init__(self, beliefs):
        self.beliefs = []
    def show_beliefs(self):
        return self.beliefs



# TESTS ========================
def test_single_specific_invariable_word(knowledge_graph, concept, word):
    """a single_specific_invariable_word expression assumes that the word is
    always present in sentences where this concept occurs, and absent from sentences
    where the concept does not occur."""
    positive_score = 0
    negative_score = 0
    sentences_with_concept_as_value, sentences_without_concept_as_value = (
        kgu.get_sentences_with_and_without_value(knowledge_graph, concept))

    for sentence in sentences_with_concept_as_value:
        if word in sentence:
            positive_score += 1
        else:
            negative_score += 1

    for sentence in sentences_without_concept_as_value:
        if word in sentence:
            negative_score += 1
        else:
            positive_score += 1

    return ((positive_score - negative_score)/(positive_score + negative_score) + 1)/2



