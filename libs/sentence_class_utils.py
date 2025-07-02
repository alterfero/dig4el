import os
import openai
from typing import List, Literal
from pydantic import BaseModel, Field, Extra
import json
api_key = os.getenv("OPEN_AI_KEY")

"""
From pivot sentence, generate a descriptive JSON with constrained format and content.
"""

class TypeOfPredicate(BaseModel):
    type_of_predicate: Literal["none", "existential", "locative", "processive", "inclusive", "attributive",
    "numeral", "presentative"]

    class Config:
        extra = "forbid"

class ConceptOntology(BaseModel):
    hyperonyms: list[str] = Field(...,
                                  description="ordered list of hyperonyms starting from the concept "
                                              "to the most general and abstract one.")

class Mood(BaseModel):
    core_mood: Literal["none", "indicative", "imperative", "subjunctive", "emphatic"]
    realis_mood: Literal["realis", "irrealis"]
    volitive_mood: Literal["none", "optative (wish, hope)", "jussive (mild command, exhortation", "hortative (let's)", "precative (plea, prayer"]
    conditional_mood: Literal["none", "conditional (if-then)", "potential (possibility, ability)", "desiderative (desire, wanting)"]
    prohibitive_mood: Literal["none", "prohibitive", "permissive"]
    epistemic_mood: Literal["none", "known", "inferential", "reportative (heard from someone)", "mirative (surprise)", "dubitative (uncertainty)", "presumptive (presumed)"]

    class Config:
        extra = "forbid"

class InternalParticularization(BaseModel):
    pos: Literal["none", "noun", "verb", "adjective", "adverb", "pronoun", "determiner", "preposition",
    "conjunction", "particle", "numerals", "interjections"]
    number: Literal["none", "singular", "dual", "trial", "paucal", "plural"]
    definiteness: Literal["none", "definite", "indefinite"]
    polarity: Literal["none", "positive", "negative"]
    tense: Literal["none", "past", "present", "future"]
    aspect: Literal["none", "gnomic", "perfective", "imperfective", "habitual", "neutral"]
    voice: Literal["active", "passive"]
    class Config:
        extra = "forbid"


class RelationalParticularization(BaseModel):
    semantic_role: Literal["none", "agent", "patient", "experiencer", "instrument", "beneficiary", "goal", "destination",
    "source", "location", "recipient", "possessor", "possessee", "stimulus", "other"]
    class Config:
        extra = "forbid"


class ReferenceOf(BaseModel):
    reference_type: Literal["self", "known entity", "partially known entity", "unknown entity"]
    reference: str = Field(..., description="what the concept is a reference to (e.g. self, known entity/entities, unknown entity/entities)")

    class Config:
        extra = "forbid"

class Concept(BaseModel):
    name: str = Field(..., description="A universal description of the concept.")
    ontology: ConceptOntology
    reference: ReferenceOf
    mood: Mood
    internal_particularization: InternalParticularization
    relational_particularization: RelationalParticularization

    class Config:
        extra = "forbid"


class EnrichedSentence(BaseModel):
    sentence: str = Field(..., description="sentence")
    intent: str = Field(..., description="The intent of the speaker.")
    type_of_predicate: str = TypeOfPredicate
    concepts: list[Concept]

    class Config:
        extra = "forbid"
        title = "properties_schema"
        str_strip_whitespace = True
        strict = True


def describe_sentence(sentence, model="gpt-4o-2024-08-06"):
    client = openai.OpenAI(api_key=api_key)
    system_message = (
        """You are an expert in linguistic annotation. Given a sentence pair, extract:
        1. the Intent of the sentence: what does the speaker want to achieve with this sentence.
            (e.g. greet, thank, part, assert, ask, order, express condition, express wish)
        2. the type of predicate. 
        3. the list of concepts, each associated with specifc information (label "none" when not applicable): 
            2.1 the concept's description: a word or sentence to label it.
            2.2 the concept's ontology: the hyperonym and up to the most general term. 
            2.3 the concept's moods: core mood, volitive mood, conditional mood, prohibitive mood, epistemic mood. 
            2.4 the concept's internal particularization: as applicable: part of speech (pos), number, definiteness, polarity, tense, aspect, voice.
            2.5 the concept's relational particularization: semantic role.
        """
    )
    user_prompt = (
        f"Sentence: {sentence}\n"
    )
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system",  "content": system_message},
            {"role": "user",    "content": user_prompt}
        ],
        # 3) Pass your explicit JSON‐Schema here
        response_format=EnrichedSentence
    )
    output = completion.choices[0].message
    return output


def description_dict_to_text(desc: dict) -> str:
    """
    Convert a sentence description JSON into a single text string for embedding.
    """
    out_string = ""
    out_string += "Sentence: " + desc.get("sentence", "").strip() + "."
    out_string += " Intent: {}".format(desc.get("intent", "none")) + "."
    out_string += " Type of predicate: {}".format(desc.get("type_of_predicate", "none")) + "."

    for concept in desc.get("concepts", []):
        # 1. Ontology hyperonyms
        # for hyper in concept.get("ontology", {}).get("hyperonyms", []):
        #     phrases.append(f"related to {hyper}")
        out_string += " Concept {} (".format(concept["name"])
        # 2. Internal particularization
        ip = concept.get("internal_particularization", {})
        for field in ("pos", "number", "definiteness", "polarity", "tense", "aspect", "voice"):
            val = ip.get(field)
            if val and val.lower() != "none":
                # e.g. "present tense", "active voice"
                if field in ("tense", "aspect", "voice"):
                    out_string += f", {val} {field}"
                else:
                    out_string += f", {val}"

        # 3. Mood features
        mood = concept.get("mood", {})
        # map keys to friendly names
        mood_map = {
            "core_mood": "mood",
            "realis_mood": "realis mood",
            "volitive_mood": "volitive mood",
            "conditional_mood": "conditional mood",
            "prohibitive_mood": "prohibitive mood",
            "epistemic_mood": "epistemic mood",
        }
        for key, label in mood_map.items():
            val = mood.get(key)
            if val and val.lower() != "none":
                out_string += f", {val} {label}"

        # 4. Semantic role
        role = concept.get("relational_particularization", {}).get("semantic_role")
        if role and role.lower() != "none":
            out_string += f", {role} role"

        # 5. Interrogative pronoun construction
        ref = concept.get("reference", {}).get("reference_type", "")
        out_string += f", reference: {ref}."

        out_string += ")"

    out_string = out_string.replace("..", ".")
    out_string = out_string.replace("( ,", "(")
    out_string = out_string.replace("(,", "(")
    out_string = out_string.replace("( ", "(")
    out_string = out_string.replace("realis realis", "realis")
    out_string = out_string.replace("realis irrealis", "irrealis")

    return out_string

def add_description_to_sentence_pairs(sentence_pairs : list) -> list:
    print("Describing {} sentences".format(len(sentence_pairs)))
    out_list = []
    i = 0
    for item in sentence_pairs:
        i += 1
        print("Sentence {}, {}".format(i, item["source"]))
        source_sentence = item["source"]
        description = describe_sentence(source_sentence)
        description_dict = json.loads(description.content)
        description_text = description_dict_to_text(description_dict)
        out_list.append(
            {
                "source": item["source"],
                "target": item["target"],
                "description_dict": description_dict,
                "description_text": description_text
            }
        )
    return out_list

# =========================== HARD INDEXING AND QUERY PARSING ==========================

def build_enriched_pairs_index(enriched_pairs):
    """
    Build an inverted index for a list of enriched sentence‐pairs.
    Each enriched_pair is expected to have a "description_dict" key.

    Returns:
        index: dict mapping (path_tuple, value) → set of indices into enriched_pairs
    """
    from libs import utils

    index = {}
    for i, enriched_pair in enumerate(enriched_pairs):
        info_dict = enriched_pair["description_dict"]
        flat_info = utils.flatten(info_dict)  # { path_tuple: leaf_value, ... }

        # for each flattened key/value, record that pair i has it
        for path, val in flat_info.items():
            index.setdefault((path, val), set()).add(i)

    return index


import re
from typing import Dict, Tuple

# 1) Schema: user terms → actual key-paths in your flattened dict
FEATURE_ALIASES: Dict[str, Tuple[str, ...]] = {
    "tense": ("tense",),
    "voice": ("voice",),
    "mood": ("mood",),
    # add more: aspect, person, number, etc.
}

# 2) Value normalization: user wording → actual values
VALUE_ALIASES: Dict[str, str] = {
    "past": "past",
    "present": "present",
    "future": "future",
    "active": "active",
    "passive": "passive",
    "indicative": "indicative",
    "subjunctive": "subjunctive",
    # etc.
}

def parse_query(question: str) -> Dict[Tuple[str, ...], str]:
    """
    Turn a natural-language question into a query dict
    mapping key-path tuples to the desired value.
    E.g. "show me sentences where tense is past and voice=passive"
    → {("tense",): "past", ("voice",): "passive"}.
    """
    q = question.lower()
    query = {}

    for term, path in FEATURE_ALIASES.items():
        # look for "term is VALUE" or "term = VALUE"
        pattern = rf"{term}\s*(?:is|=)\s*(\w+)"
        m = re.search(pattern, q)
        if not m:
            continue
        raw_val = m.group(1)
        norm_val = VALUE_ALIASES.get(raw_val)
        if norm_val:
            query[path] = norm_val

    return query

def query_enriched_pairs_with_index(index, enriched_pairs, query):
    """
    Query the inverted index for enriched_pairs matching ALL key→value constraints.

    Args:
        index:         inverted index from build_enriched_pairs_index
        enriched_pairs: original list of pairs
        query:         dict mapping path tuples to desired values,
                       e.g. {("tense",): "past", ("mood",): "indicative"}

    Returns:
        List of enriched_pairs whose description_dict contains all those key:values.
    """
    if not query:
        # no constraints → return everything
        return list(enriched_pairs)

    # retrieve the set of matching indices for each constraint
    posting_lists = [
        index.get((path, val), set())
        for path, val in query.items()
    ]

    # fast-fail: if any constraint has zero matches, intersection is empty
    if any(len(pl) == 0 for pl in posting_lists):
        return []

    # intersect all posting‐lists
    hits = set.intersection(*posting_lists)
    return [enriched_pairs[i] for i in hits]


