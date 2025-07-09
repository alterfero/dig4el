from __future__ import annotations

import os
import openai
from agents import Agent, ModelSettings, function_tool, Runner
from typing import List, Literal, Tuple, Union, Optional
from pydantic import BaseModel, Field, Extra

api_key = os.getenv("OPEN_AI_KEY")
openai.api_key = api_key

class PredicateType(BaseModel):
    type: Literal["existential", "equative", "locative", "attributive", "inclusive", "possessive",
                  "sampling", "processive", "causal", "logic", "other"]

class Features(BaseModel):
    number: Optional[Literal["singular", "dual", "trial", "paucal", "plural"]] = None
    definiteness: Optional[Literal["definite", "indefinite"]] = None
    polarity: Optional[Literal["positive", "negative"]]
    tense: Optional[Literal["past", "present", "future", "general"]] = None
    aspect: Optional[Literal["perfect", "progressive", "habitual", "other"]] = None
    mood: Optional[Literal["indicative", "hypothetical", "conditional", "wish", "belief", "imperative"]] = None
    voice: Optional[Literal['active', 'passive', 'none']] = None
    reality: Optional[Literal['real', 'conditional', 'potential', 'hypothetical', 'imaginary', 'other']] = None
    space: Optional[Literal['none', 'speaker-sphere', 'addressee_sphere', 'remote']] = None
    direction: Optional[Literal['none', 'centripetal', 'centrifugal']] = None


class Argument(BaseModel):
    role: Literal['agent', 'experiencer', 'patient', 'recipient', 'instrument', 'time information', 'space information',
                  'beneficiary', 'goal', 'destination', 'source', 'possessor', 'possession', 'stimulus',
                  'cause', 'consequence', 'condition', "equality", "complement", "other"]
    target_pid: str            # id of another predicate


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
    comments: str

existential_extractor = Agent(
    name="existential_extractor",
    model="o4-mini-2025-04-16",
    instructions="""
    - You are Predicate-Agent #1 (Existential extractor). 
    - Your only job is to list the elementary predicates required for the sentence to make sense.
    - These predicates are units of meaning. They can be a single word, or a jointed or disjointed group of words.
    English verbs as "to be" or "to have" are usually not an existential predicate but indicate relations between predicates. 
    Every open-class token (noun, proper noun, adjective, lexical verb, participle, numeral, etc.) gets exactly 
    one predicate.
    - Reference with unknown antecedents for the reader are existential predicates.
    - References with unknown antecedents for the speaker are existential predicates, as question words and "wildcards" 
    as "who", "where", "when", "that" etc. when used as a reference to an unknown antecedent (as in "I don't know who came").
    - Pronouns referring to the speaker, the people he/she is talking to, are existential predicates. 
    - Deictics are existential predicates ("That", "this", "here", "up there", anything pointed in space and time).  
    - Possessive words (my, yours etc.) create a predicate that describes the actual being (I, you). 
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
    - Fill all relevant arguments of all predicates. 
    - Coordination, logic ("and", "or" etc.), causal ("because", "if...then" etc.) 
        or temporal coordinations ("then" etc.) in complex sentences are also predicates that must be created. 
    - Add to the "comment" field any issue you had doing your job, including suggestions on how to make the prompt 
    and framework better. 
    
    For example, in "Mary, who is the sister of Helen, has a dog who bites neighbors because he thinks they are geese.", 
    the existential predicates' heads 
    are [Mary, Helen, sister, dog, neighbors, thinking, geese]. 
    Higher-level predicates are 
    - a possessive predicate hp1 (Helen has a sister)
    - an equative predicate hp2 (Mary is the sister of Helen)
    - a possessive predicate hp3 (Mary has a dog)
    - a processive predicate hp4 (Mary's dog bites neighbors)
    - an equative predicate with a "belief" mood (neighbors are geese)
    - an overall causal predicate (Mary's dog bites BECAUSE he believes...)
    """,
    output_type=Sentence
)

def extract_existential_predicates(sentence: str) -> List[str]:
    result = Runner.run_sync(existential_extractor, sentence)
    return result.final_output


def describe_sentence(sentence: str, predicates: list[str]) -> dict:
    data = f"Sentence: {sentence} --- Predicates: {predicates}"
    result = Runner.run_sync(higher_order_predicate_extractor, data)
    return result.final_output.dict()

