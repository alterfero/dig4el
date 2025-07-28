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


class Referent(BaseModel):
    """Real-world referent the representation is about"""
    rid: str
    designation: str
    speaker_relation: Optional[Union[Literal["speaker", "speaker and one interlocutor", "speaker and two interlocutors", "speaker and many interlocutors",
                        "speaker and one person that is not the interlocutor", "speaker and two persons that do not include the interlocutor",
                        "speaker and more that 2 persons that are not the interlocutor",
                        "one interlocutor", "two interlocutors", "three interlocutors", "many interlocutors",
                        "another person", "two other persons", "three other persons", "many other persons"], str]] = None
    type: Union[Literal["human elder", "human", "young human", "humanized", "supernatural being",
    "animal", "plant", "artifact", "natural object",
    "experience", "event", "action", "location in time", "location in space", "abstraction", "other"], str]
    referent_status: Literal["known by the speaker", "partially known by the speaker", "unknown by the spaker"]
    indexicality: Optional[Union[Literal["pointed at"], str]] = None
    features: Referent_Features

class Referent_Features(BaseModel):
    """Features of a real-world referent"""
    quantifiability: Optional[Union[Literal["continuous", "discrete", "mass"], str]] = None
    quantity: Optional[Literal["zero", "one", "two", "three", "a few", "many", "none", "some", "a lot", "all"]] = None
    definiteness: Optional[Literal["definite", "indefinite"]] = None
    reality: Optional[Literal['real', 'conditional', 'potential', 'hypothetical', 'imaginary', 'other']] = None
    polarity: Optional[Literal["positive", "negative"]]
    time_aspect: Optional[Union[Literal["perfective", "imperfective", "progressive", "habitual"], str]] = None
    time_position: Optional[Literal["past", "present", "future", "general"]] = None
    space_location: Optional[Literal['none', 'speaker-sphere', 'interlocutors_sphere', 'remote']] = None
    space_direction: Optional[Literal['none', 'centripetal', 'centrifugal']] = None


class PredicateType(BaseModel):
    type: Union[Literal["existential", "equative", "locative", "attributive", "inclusive", "possessive",
    "sampling", "processive", "conditional", "causal", "logic", "other"], str]


class Enunciation(BaseModel):
    intent: str
    mood: Optional[Union[Literal["indicative", "hypothetical", "conditional", "wish", "belief", "imperative"], str]] = None
    voice: Literal['active', 'passive', 'none']
    emphasis: str

class Argument(BaseModel):
    role: Union[Literal['agent', 'experiencer', 'patient', 'recipient', 'instrument', 'time information', 'space information',
    'beneficiary', 'goal', 'destination', 'source', 'possessor', 'possession', 'stimulus',
    'cause', 'consequence', 'condition', "equality", "complement", "other"], str]
    target_pid: str  # id of another predicate


class Predicate(BaseModel):
    pid: str
    kernel: Referent
    ptype: PredicateType
    args: List[Argument]

class Sentence(BaseModel):
    pid: str
    referents: List[Referent]
    predicates: List[Predicate]
    top: str  # id of the topmost predicate
    grammatical_description: str
    grammatical_keywords: List[str]
    comments: str

# Model:
# 1) A linguistic representation expresses relations among referents.
# 2) Referents are entities or processes, real or imaginary, concrete or abstract,
#    that are situated in, and evolve across, temporal, spatial and ad-hoc dimensions.
# 3) Languages use predicates, composable structural constructs, to assert properties of,
#    or relations between, referents.
# 4) Languages instantiate predicates using the time and/or space-structured delivery of symbols:
#    hybrid constructs associating perceivable signals with meanings.
# 5) Grammar is the process that serializes predicative contents into,
#    perceivable forms, and deserializes them back into structured representations.


referent_finder = Agent(
    name="Referent Finder",
    model="o4-mini-2025-04-16",
    instructions="""
    - You are semantic analysis agent #1 (Referent Finder). 
    - Your only job is to list and describe the referents in the sentence provided.
    - What are referents: A sentence expresses relations among referents. Referents are entities or processes, 
    concrete or abstract, from the physical real world or from the imagination of the speaker. Referents are not 
    linguistic objects but the things describes/evoked by the language. 
    - List individual, indivisible referents. 
    - For each referent, provide:
        - a referent id "rid", which must be unique.
        - designation: A word or expression identifying the referent (as "a person named Mary", "the speaker", 
        "a person not present", "The interlocutor's dog")
        - type: among the types proposed, as human, animal, object, event, action etc. Note that even abstraction, as 
                "red" in "Mary's red robe" is a referent.
        - referent_status: This indicates if the speaker knows or does not know the referent. For example: 
        in "She will come today." the speaker knows who "she" is. 
        In "I wonder which sister will come at the party", the speaker partially know who "which sister" is. 
        In "What must happen will happen.", the speaker does not know what "What" is. 
        - Indexicality: Indicate here if the speaker determines a referent by using the context of utterance, as 
                        pointing with a finger. In "This is my office", "this" makes sense in the context of 
                        utterance. 
        - Features: quantifiability, quantity, definiteness, reality, polarity, time aspect, time position,
        space location, space direction. Use None when a feature does not apply to the referent. 
    """,
    output_type=List[Referent]
)

predicate_extractor = Agent(
    name="predicate_extractor",
    model="o4-mini-2025-04-16",
    instructions="""
    You are Predicate Extractor, a semantic analysis agent building predicate structures. 

    Your input is:
    - a sentence
    - a list of detailed referents
    
    Your task is to generate the predicates by which the sentence expresses the properties of, 
    and relations between referents.
    
    ---
    
    REFERENTS:
    A sentence expresses relations among referents. Referents are entities or processes, concrete or abstract, 
    from the real world or from the imagination of the speaker. Referents are not linguistic expressions 
    but the things described or evoked by the language.
    
    ---
    
    PREDICATES:
    Predicates are composable structural constructs used by languages to assert properties of, or relations between, referents.
    
    - Predicates have types such as: `"existential"`, `"equative"`, `"locative"`, `"attributive"`, `"inclusive"`, `"possessive"`, `"sampling"`, `"processive"`, `"causal"`, `"logic"`, `"conditional"`, and `"spatio-temporal"`, depending on their contribution to meaning.
    - All referents must receive an existential predicate if no other predicate type is more adapted. Remove the existential 
    predicate when referents become arguments/kernel of other predicates. 
    - Predicates have arguments.
    - Each predicate is assigned a unique `"pid"` (predicate ID).
    
    ---
    
    BASE VS. HIGHER-ORDER PREDICATES:
    
    - A **base predicate** takes one or more **referents** as arguments.
    
      Example: “Mary is here.”  
      - Referents:  
        `r1`: Mary  
        `r2`: The spatial location where the speaker is  
      - Predicates:  
        `p1`: Existential (`r1`)  
        `p2`: Existential (`r2`)  
        `p3`: Locative (agent: `r1`, location: `r2`)
    
    - A **higher-order predicate** takes at least one **predicate** as an argument.
    
      Example: “The woman I met is the mayor’s daughter.”  
      The top predicate is **equative**, relating two **predicate-defined referents**:  
      - one from “the woman I met”  
      - one from “the mayor’s daughter”
    
    ---
    
    KERNEL AND ARGUMENTS:
    
    - Each predicate has a **kernel**: the conceptual center around which its arguments are organized.  
      The kernel can be a referent or a newly created abstract concept. If you add an abstract concept kernel,
      also create the referent for it.
    
      Example:  
      In “If the glass drops, it breaks”, a conditional predicate must be created with:
      - kernel: condition
      - arguments: the two processive predicates (dropping, breaking)
    
    - Fill all relevant arguments.  
      If no listed role is adequate, create a new argument role.  
      Example roles: `"agent"`, `"theme"`, `"location"`, `"possessor"`, `"class"`, `"attribute"`, `"consequence"`, etc.
    
    ---
    
    EXTENDING THE SYSTEM:
    
    - You may create **new predicates**, **roles**, or **predicate types** when needed to accurately reflect the meaning.
    - Predicate type definitions:
      - `"existential"`: Asserts existence of a referent
      - `"equative"`: Asserts identity (e.g., “Bob is your father”)
      - `"inclusive"`: Asserts class membership (e.g., “Bob is a man”)
      - `"attributive"`: Assigns a property (e.g., “Bob is fun”)
      - `"locative"`: Asserts spatial or temporal location
      - `"possessive"`: Expresses possession
      - `"sampling"`: Gives examples (e.g., “Animals like cats and dogs…”)
      - `"processive"`: Describes an event or action (e.g., “Bob runs”)
      - `"causal"`: Expresses causality (e.g., “Because Bob arrived late…”)
      - `"conditional"`: Expresses a condition (“If Bob leaves…”)
      - `"logic"`: Logical connector (“but”, “and”, “or”)
      - `"spatio-temporal"`: Temporal or spatial sequencing (“then”, “before”, “meanwhile”)
    
    ---
    
    PREDICATE GRAPH INTEGRITY:
    The predicates should connect all referents into a unique graph where referents and predicates are nodes, 
    and the arguments of predicates define edges. There should not be multiple disjointed graphs. Make sure you 
    verify and modify your output as needed. 
    
    OUTPUT REQUIREMENTS:
    
    - Use the referents you are given, referenced by their `rid`.
    - Assign each predicate a unique `pid`.
    - Define kernel and argument structure clearly.
    - For complex relations, create abstract kernels or new predicates as needed.
    
    ---
    
    ADDITIONAL ANNOTATIONS:
    
    - **Grammatical-Semantic description**:  
      Describe language-independent semantic structures found in the sentence, such as:  
      `"negative polarity"`, `"passive voice"`, `"conditional"`, `"comparison"`, `"perfect aspect"`  
      Do not use surface grammar terms unless they encode semantic distinctions.
    
    - **Grammatical-Semantic keywords**:  
      List key semantic features conveyed in the sentence. Use only language-independent terms.
    
    - **Comment**:  
      Report any difficulty, ambiguity, or suggestion to improve the prompt or framework.



    """,
    output_type=Sentence
)

enunciation_descriptor = Agent(
    name="enunciation_descriptor",
    model="o4-mini-2025-04-16",
    instructions=""" 
    You are Enunciation Descriptor, an semantic agent specialized in describing parameters related to why and how a sentence
    has been spoken by a speaker. 
    Your goal is to analyze the sentence at the level of enunciation, i.e., the communicative posture and structural choices 
    that reflect the speaker’s intent and focus.
    You are given a sentence.
    With this, output the following: 
    - Intent: What the speaker is trying to do (e.g., assert a fact, request something, express doubt).
    - Mood: Grammatical modality or force (indicative, imperative, conditional, wish, doubt, etc.)
    - Voice: Active or passive. 
    - Emphasis: Which referent is foregrounded by the sentence structure?
    
    Examples:
    Sentence: "If she wins, she gets the prize."  
    Output
    {
      "intent": "express a condition with if...then",
      "mood": "conditional",
      "voice": "active",
      "emphasis": "the condition"
    }
    
    Sentence: "The decision was made by the board"
    Output:
    {
      "intent": "assert",
      "mood": "indicative",
      "voice": "passive",
      "emphasis": "the decision"
    }
    
    """,
    output_type=Enunciation
)

def find_referents(sentence: str) -> List[str]:
    result = Runner.run_sync(referent_finder, sentence)
    return result.final_output


def extract_predicates(sentence: str, referents: list[str]) -> dict:
    data = f"Sentence: {sentence} --- Referents: {referents}"
    result = Runner.run_sync(predicate_extractor, data)
    return result.final_output.dict()


def describe_enunciation(sentence: str) -> dict:
    result = Runner.run_sync(enunciation_descriptor, sentence)
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
                              referent_color="#C680B6",
                              top_node_color="#729EA1",
                              predicate_color="#C2D5D6"):

    # ensure PyVis can find its Jinja templates
    template_dir = pkg_resources.resource_filename("pyvis", "templates")

    net = Network(height=height,
                  width=width,
                  directed=True,
                  notebook=False,
                  )
    net.barnes_hut()

    # index referents
    referents = {p["rid"]: p for p in data.get("referents", [])}

    # add all referent nodes
    for rid, r in referents.items():
        designation = r.get("designation", rid)
        speaker_relation = r.get("speaker_relation", "not specified")
        type = r.get("type", rid)
        referent_status = r.get("referent_status", "status unspecified")
        indexicality = r.get("indexicality", "indexicality unspecified")
        feat_list = [f"{k}: {r['features'][k]}" for k in r["features"].keys()]
        features = "\n".join(feat_list)

        net.add_node(
            n_id=rid,
            label=f"Referent\n{designation}\n({type})",
            title=(
                f"ontological type: {type}\n"
                f"speaker relation: {speaker_relation}.\n"
                f"referent_status: {referent_status}.\n"
                f"indexicality: {indexicality}.\n"
                f"\n{features}"
            ),
            shape="ellipse",
            color=referent_color,
            size=30
        )

    # add predicate nodes
    for p in data["predicates"]:
        p_type = p["ptype"]["type"]
        net.add_node(
            n_id=p["pid"],
            label=f"{p_type}\npredicate",
            title=(
                f"{p['pid']}"
                f"type: {p_type}. "
            ),
            shape="box",
            color=predicate_color,
            size=20
        )

    # add predicate-based edges

    for p in data["predicates"]:
        referent_kernel_id = p["kernel"]["rid"]
        if referent_kernel_id and referent_kernel_id != "":
            try:
                net.add_edge(
                    source=p["pid"],
                    to=referent_kernel_id,
                    value=2,
                    arrows=None,
                    physics=True
                )
            except AssertionError:
                print("!!!! Edge creation exception !!!")
                print("Predicate: {}".format(p))
        for arg in p["args"]:
            role = arg["role"]
            target = arg["target_pid"]
            try:
                net.add_edge(
                    source=p["pid"],
                    to=target,
                    value=1,
                    label=role,
                    title=role,
                    arrows="to",
                    physics=True
                )
            except AssertionError:
                print("!!!! Edge creation exception !!!")
                print("Predicate: {}".format(p))


    # highlight the top node if specified
    top_id = data.get("top", {})
    if top_id and net.get_node(top_id):
        net.get_node(top_id)["color"] = top_node_color
        net.get_node(top_id)["title"] += "  ← top node"

    # custom physics for stability
    net.set_options("""
    var options = {
      "nodes": {"font":{"size":16}},
      "edges": {"smooth":true},
      "physics": {
        "barnesHut": {"gravitationalConstant":-7000, "centralGravity":0.5},
        "minVelocity":0.5
      }
    }
    """)

    return net.generate_html()

