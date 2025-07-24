from __future__ import annotations

import os
import openai
from agents import Agent, ModelSettings, function_tool, Runner
from typing import List, Literal, Tuple, Union, Optional
from pydantic import BaseModel, Field, Extra
from collections import defaultdict
import pkg_resources
from pyvis.network import Network

api_key = os.getenv("OPEN_AI_KEY")
openai.api_key = api_key


class PredicateType(BaseModel):
    type: Union[Literal["existential", "equative", "locative", "attributive", "inclusive", "possessive",
    "sampling", "processive", "causal", "logic", "other"], str]


class Features(BaseModel):
    number: Optional[Literal["singular", "dual", "trial", "paucal", "plural"]] = None
    definiteness: Optional[Literal["definite", "indefinite"]] = None
    polarity: Optional[Literal["positive", "negative"]]
    tense: Optional[Literal["past", "present", "future", "general"]] = None
    aspect: Optional[Union[Literal["perfective", "imperfective", "progressive", "habitual"], str]] = None
    mood: Optional[Union[Literal["indicative", "hypothetical", "conditional", "wish", "belief", "imperative"], str]] = None
    voice: Optional[Literal['active', 'passive', 'none']] = None
    reality: Optional[Literal['real', 'conditional', 'potential', 'hypothetical', 'imaginary', 'other']] = None
    space: Optional[Literal['none', 'speaker-sphere', 'addressee_sphere', 'remote']] = None
    direction: Optional[Literal['none', 'centripetal', 'centrifugal']] = None


class Argument(BaseModel):
    role: Union[Literal['agent', 'experiencer', 'patient', 'recipient', 'instrument', 'time information', 'space information',
    'beneficiary', 'goal', 'destination', 'source', 'possessor', 'possession', 'stimulus',
    'cause', 'consequence', 'condition', "equality", "complement", "other"], str]
    target_pid: str  # id of another predicate


class Predicate(BaseModel):
    pid: str
    head: str
    ptype: PredicateType
    feats: Features
    args: List[Argument]


class Sentence(BaseModel):
    pid: str
    intent: str  # the intent of the speaker as assert, ask etc.
    predicates: List[Predicate]
    top: str  # id of the topmost predicate
    grammatical_description: str
    grammatical_keywords: List[str]
    comments: str


existential_extractor = Agent(
    name="existential_extractor",
    model="o4-mini-2025-04-16",
    instructions="""
    - You are Predicate-Agent #1 (Existential extractor). 
    - Your only job is to list the elementary predicates required for the sentence to make sense.
    - These predicates are indivisible units of meaning in the sentence carrying their internal determination. 
        They can be a single word, or a jointed or disjointed group of words.
        Typical unitary predicates are for example determinant + noun ("the dog"), verb with modal words ("would come"), 
        adjective with modifier ("very pretty"), adverb with modifier ("so fast").
    - For the head, use the "-ing" form for verbs, singular for nouns.  
    - English verbs as "to be" or "to have" are usually not an existential predicate but indicate a verb's determination or relations between predicates. 
    - References (as pronouns or deictics) with unknown antecedents for the reader are existential predicates.
    - References with unknown antecedents for the speaker are existential predicates, as question words and "wildcards" 
    as "who", "where", "when", "that" etc. when used as a reference to an unknown antecedent (as in "I don't know who came").
    - Proper nouns and Pronouns referring to the speaker, the people he/she is talking to, are existential predicates. 
    - Deictics are existential predicates ("That", "this", "here", "up there", anything pointed in real of imaginary space and time).  
    - Possessive words (my, yours etc.) create a predicate that describes the actual being possessing something (I, you, Mary). 
        the possession is expressed in another predicate by the next agent.
    - Multiple reference to the same antecedent (Mary...she, I...me, Mary...her, or my...my) must be merged in a single predicate.  
    - Each of these predicates has type "existential".
    - Do not create any higher-order relations, arguments, or extra predicates. Those belong to later agents.
    - No additional keys, no comments, no explanatory text outside the JSON following the output schema.
    - Add all relevant Features (feats) to these predicates (as definiteness, number, tense, aspect etc.)
    Generate pid values as e1, e2, … in the order tokens appear.
    """,
    output_type=List[Predicate]
)

higher_order_predicate_extractor = Agent(
    name="higher_order_predicate_extractor",
    model="o4-mini-2025-04-16",
    instructions="""
    You are Predicate-Agent #2 (higher order predicate extractor and argument builder). 
    Given a sentence and a list of existential Predicates, your job is to add the higher-order predicates of 
    the sentence referencing earlier pids via Arguments, and fill all Arguments' values. 
    - Use only the predicates you are provided with, referenced by their pid. 
    - When creating new predicates as needed to reflect the meaning of the sentence, create new, unique pids. 
    - Your output must contain all existential predicates, plus the higher-order predicates you have added. 
    - Intent: indicate what the speaker's intent is with a very short general expression, as "assert", "ask a question", 
    "express a whish", "deny", "express a condition with if...then", "express a contrast with but" etc.
    - Fill all relevant arguments of all predicates. You can create argument's role if none in the list is satisfactory.
    - Modify the type of predicate when needed:
        Equative predicates state the symetric identity between twho things, as in "Bob is your father" (= Your father is Bob).
        Inclusive predicates states the inclusion of something in a class, as in "Bos is a man" (= Bob is something that belongs to the man category)
        Attributive predicates associate a property with something, as in "Bob is fun."
        Locative predicates indicate where (in time or space) is something, as in "Bob is in the garage."
        Possessive predicates express a possession relation.
        Sampling predicate lists example of something.
        Logic predicates express a logical relationship between other predicates (and, or, but, however, in spite of etc.)
        Causal predicates express causality between two predicates (because etc.)
        Conditional predicates express a conditional relation between two predicates (if...then etc). 
        Spatio-temporal predicates express a spatial or temporal relation between two predicates (then...)
        
        If none of the listed predicates is satisfactory, you can invent a new one. 
        
    - Create missing, higher-order predicates as need.  
    - Add to the "comment" field any issue you had doing your job, including suggestions on how to make the prompt 
    and framework better. 
    - Grammatical-Semantic description: provide a brief description of language-independent grammatical & semantic 
    forms in the sentence as "negative polarity", "passive voice", "expression of a condition", "comparison" etc. 
    "perfect aspect" etc. Use only semantic, language-independent terms. For example, a relative clause in a sentence is
    language-specific, while the attribution of properties (what the relative does foe example) is not. 
    - Grammatical-Semantic keywords: provide a list of grammar keywords that can be associated with this sentence, highlighting
    salient semantic expressions. Use only semantic, language-independent terms. 
    
    For example, in "Mary, who is the sister of Helen, has a dog who bites neighbors because he thinks they are geese.", 
    the existential predicates' heads are [Mary, Helen, sister, dog, neighbors, thinking, geese]. 
    Higher-level predicates are 
    - a possessive predicate hp1 (Helen has a sister)
    - an equative predicate hp2 (Mary is the sister of Helen)
    - a possessive predicate hp3 (Mary has a dog)
    - a processive predicate hp4 (Mary's dog bites neighbors)
    - an equative predicate with a "belief" mood (neighbors are geese)
    - an overall causal predicate (Mary's dog bites BECAUSE he believes...)
    In this example the intent is "Assert", the grammatical description is "The sentence 
    expresses a general fact about a person and a dog, with a possession relation between the two. 
    The beliefs of the dog are expressed." The grammatical keywords are ["property attribution", "possession", 
    "general fact", "expression of beliefs"]
    
    """,
    output_type=Sentence
)


def extract_existential_predicates(sentence: str) -> List[str]:
    result = Runner.run_sync(existential_extractor, sentence)
    return result.final_output


def describe_sentence_with_predicates(sentence: str, predicates: list[str]) -> dict:
    data = f"Sentence: {sentence} --- Predicates: {predicates}"
    result = Runner.run_sync(higher_order_predicate_extractor, data)
    return result.final_output.dict()

def describe_sentence(sentence: str) -> dict:
    predicates = extract_existential_predicates(sentence)
    data = f"Sentence: {sentence} --- Predicates: {predicates}"
    result = Runner.run_sync(higher_order_predicate_extractor, data)
    return result.final_output.dict()

def description_dict_to_kw(description_dict: dict) -> List[str]:
    predicate_type = []
    definiteness = []
    tense = []
    polarity = []
    aspect = []
    mood = []
    voice = []
    reality = []
    space = []
    direction = []

    kw = [description_dict.get("intent")]

    predicate_type = [p["ptype"].get("type", None) for p in description_dict["predicates"] if p["ptype"].get("type", None) is not None]

    number = [p["feats"].get("number", None) for p in description_dict["predicates"] if p["feats"].get("number", None) is not None]

    definiteness = [p["feats"].get("definiteness", None) for p in description_dict["predicates"] if p["feats"].get("definiteness", None) is not None]

    tense = [p["feats"].get("tense", None) for p in description_dict["predicates"] if p["feats"].get("tense", None) is not None]

    polarity = [p["feats"].get("polarity", None) for p in description_dict["predicates"] if p["feats"].get("polarity", None) is not None]

    aspect = [p["feats"].get("aspect", None) for p in description_dict["predicates"] if p["feats"].get("aspect", None) is not None]

    mood = [p["feats"].get("mood", None) for p in description_dict["predicates"] if p["feats"].get("mood", None) is not None]

    voice = [p["feats"].get("voice", None) for p in description_dict["predicates"] if p["feats"].get("voice", None) is not None]

    reality = [p["feats"].get("reality", None) for p in description_dict["predicates"] if p["feats"].get("reality", None) is not None]

    space = [p["feats"].get("space", None) for p in description_dict["predicates"] if p["feats"].get("space", None) is not None]

    direction = [p["feats"].get("direction", None) for p in description_dict["predicates"] if p["feats"].get("direction", None) is not None]

    kw += list(set(predicate_type))
    kw += list(set(number))
    kw += list(set(definiteness))
    kw += list(set(tense))
    kw += list(set(polarity))
    kw += list(set(aspect))
    kw += list(set(mood))
    kw += list(set(voice))
    kw += list(set(reality))
    kw += list(set(space))
    kw += list(set(direction))

    return kw


def TEST_add_description_and_keywords_to_sentence_pair(sentence_pair: dict) -> None | dict:
    source_sentence = sentence_pair.get("source", "")
    if source_sentence == "":
        print("No source in {}".format(sentence_pair))
        return None
    else:

        augmented_pair = {
                "source": sentence_pair["source"],
                "target": sentence_pair["target"],
                "description_dict": "description_dict",
                "description_text": "description_text",
                "grammatical_keywords": "keywords"
            }
        return augmented_pair


def add_description_and_keywords_to_sentence_pair(sentence_pair: dict) -> None | dict:
    source_sentence = sentence_pair.get("source", "")
    if source_sentence == "":
        print("No source in {}".format(sentence_pair))
        return None
    else:
        description = describe_sentence(source_sentence)
        # print("*************************")
        # print("*      DESCRIPTION      *")
        # print("*************************")
        # print(description)
        description_text = description.get("grammatical_description", "no description")
        keywords = description.get("grammatical_keywords", ["no keywords"])
        keywords += description_dict_to_kw(description)
        keywords = list(set(keywords))
        description["grammarical_keywords"] = keywords
        augmented_pair = {
                "source": sentence_pair["source"],
                "target": sentence_pair["target"],
                "description_dict": description,
                "description_text": description_text
            }
        return augmented_pair

def build_keyword_index(enriched_pairs: List) -> dict:
    """
    Build an inverted index from each keyword → set of sentence‐indices.
    enriched_pairs: list of dicts, each has a "keywords" key with a list of strings.
    Returns: index: dict[str, set[int]]
    """
    index = defaultdict(set)
    print("build_keyword_index")
    for i, pair in enumerate(enriched_pairs):
        print(pair)
        for kw in pair["grammatical_keywords"]:
            index[kw].add(i)
    return index

def plot_semantic_graph_pyvis(data,
                              height="600px",
                              width="100%",
                              coordination_color="#DD22AA",
                              concept_color="#AED6F1",
                              predicate_color="#A9DFBF",
                              top_node_color="#E74C3C"):

    # ensure PyVis can find its Jinja templates
    template_dir = pkg_resources.resource_filename("pyvis", "templates")

    net = Network(height=height,
                  width=width,
                  directed=True,
                  notebook=False,
                  )
    net.barnes_hut()

    # index concepts, predicates & coordinations by ID
    predicates = {p["pid"]: p for p in data.get("predicates", [])}

    # add all predicate nodes, then their edges
    for pid, p in predicates.items():
        head = p.get("head", pid)
        type = p.get("ptype", pid).get("type", pid)
        if type == "existential":
            type = ""
        if type in ["equative", "possessive"]:
            head = ""
        if head != "" and type != "":
            head += ", "

        net.add_node(
            n_id=pid,
            label=f"{head}{type}",
            title=(
                f"Aspect: {p.get('feats').get('aspect')} · "
                f"Mood: {p.get('feats').get('mood')} · "
                f"Tense: {p.get('feats').get('tense')} · "
                f"Reality: {p.get('feats').get('reality')}"
            ),
            shape="box",
            color=predicate_color,
            size=30
        )
    for pid, p in predicates.items():
        for arg in p.get("args", []):
            role = arg.get("role", "")
            target = arg.get("target_pid", None)
            net.add_edge(
                source=pid,
                to=target,
                label=role,
                title=role,
                arrows="to",
                physics=True
            )

    # highlight the top node if specified
    top_id = data.get("top", {})
    if top_id and net.get_node(top_id):
        net.get_node(top_id)["color"] = top_node_color
        net.get_node(top_id)["title"] += "  ← top node"

    # custom physics for stability
    net.set_options("""
    var options = {
      "nodes": {"font":{"size":14}},
      "edges": {"smooth":true},
      "physics": {
        "barnesHut": {"gravitationalConstant":-5000, "centralGravity":0.2},
        "minVelocity":0.5
      }
    }
    """)

    return net.generate_html()