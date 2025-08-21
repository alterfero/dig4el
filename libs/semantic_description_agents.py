from __future__ import annotations

import os
import openai
import asyncio
from agents import Agent, ModelSettings, function_tool, Runner
from typing import List, Literal, Tuple, Union, Optional
from pydantic import BaseModel, Field, Extra
import nest_asyncio

nest_asyncio.apply()

api_key = os.getenv("OPEN_AI_KEY")
openai.api_key = api_key

class Sentence(BaseModel):
    original_sentence: str
    dense_input: str
    key_translation_concepts: List[str]
    keywords: List[str]
    comment: str


grammatical_descriptor = Agent(
    name="Grammatical Descriptor",
    model="o4-mini-2025-04-16",
    instructions="""
You produce language-independent semantic, structural, and grammatical analyses appended to the provided English sentence
for a retrieval pipeline supporting language teachers. Teachers enter semantic/grammatical queries (e.g., "expression of aspects",
"pronominal system", "how to express the past tense", "how to express quantities", "the possession").

You must return only the fields required for vectorization and keyword ranking.

TASK — Given an input sentence, output a single JSON object with:
1) original_sentence: the original sentence (preserve original casing and punctuation).
2) dense_input: a deterministic, delexicalized, single-line string expressed as **short, well-formed micro-sentences**, containing the semantic and grammatical analysis.
  Requirements:
  • all values lowercase; tokens separated by "; " (semicolon + space); end each section with a semicolon.
  • no parameter names.
  • no extra punctuation beyond semicolons and colons as specified.
  • fields MUST appear in this exact order:
      1) intent
      2) enunciation
      3) type_of_predicate
      4) main_predicate
      5) participants (roles in fixed order)
  • Each section must be phrased as a compact micro-sentence or clause, separated by " | " (pipe with spaces).  
  • field formats (STRICT):
      - intent=<assert|order|ask|wish|belief|express_potential|express_condition|...>;
      - enunciation: voice <active|passive|unspecified>; emphasis <agent|patient|process|complement|unspecified>;
      - type_of_predicate <existential|equative|locative|inclusive|processive|...>;
      - expression of time
      - expression of space
      - main_predicate: lemma <lemma>; type <lexical|copular|light|auxiliary|unspecified>; valency <intransitive|transitive|ditransitive|other>; tense <past|present|future|nonpast|unspecified>; aspect <habitual|progressive|perfective|imperfective|iterative|none|unspecified>; mood <realis|irrealis|deontic|epistemic|none|unspecified>; polarity <affirmative|negative|unspecified>;
      - participants: for each role in this fixed order
          {agent, recipient, theme, patient, experiencer, stimulus, location, source, goal, beneficiary, possessor, possessee}
        if present, emit exactly:
          <role> known_by_the_speaker <known|partially_known|unknown|unspecified>; person <1|2|3|unspecified>; quantity <zero|singular|dual|trial|paucal|plural|all|some|many|none|unspecified>; definiteness <definite|indefinite|generic|unspecified>;
        If a role is absent, omit it entirely. Do not reorder roles.
3) key_translation_concepts: list of concise, language-agnostic alignment anchors for cross-lingual analysis, expressed in simple terms for non-experts.
  • List the main words/ideas in the sentence (subjects, objects, complements).
  • Add basic grammar concepts that shape meaning (tense, mood, polarity, possession, definiteness, plurality, etc.).
  • Each concept should be a short noun phrase or phrase in plain English.
  • No typological or formal-linguistic jargon.
  • Keep to 6–14 items; order from most to least structurally informative.
  for example, the sentence "I wish I had received a horse for my birthday" would yield the key_translation_concepts:
  ["I", "expression of a wish", "receiving", "past tense", "a horse", "my birthday"]
4) keywords: a list of unique tokens drawn ONLY from the values you emitted in dense_input
  (cover intent, enunciation, predicate type/features, roles, definiteness, quantity, tense/aspect/mood/polarity). 
  No synonyms, no expansions, no repeats.

5) comment: briefly note any analysis difficulties or prompt/structure improvements. Lowercase.

NOTES:
- If any value is unknown, output "unspecified". Do not invent details.
- Output ONLY the JSON object. No prose or markdown.
- Everything except original_sentence MUST be lowercase.

EXAMPLE
input sentence: "Mary used to give her children a candy."
expected output:
{
  "original_sentence": "Mary used to give her children a candy.",
  "dense_input": "the intent is assert. | the voice is active with unspecified emphasis. | the predicate type is processive. | the predicate is give, lexical, ditransitive, tense past, aspect habitual, mood realis, polarity affirmative. | agent is known, person 3, quantity singular, definiteness definite. | recipient is known, person 3, quantity plural, definiteness definite. | theme is known, person unspecified, quantity singular, definiteness indefinite.",
  "keywords": ["assert","active","processive","give","lexical","ditransitive","past","habitual","realis","affirmative","agent","recipient","theme","known","definite","indefinite","singular","plural"],
  "comment": "gender and emphasis may be underdetermined; predicate type taxonomy could be refined."
}
""",
    output_type=Sentence
)


async def describe_sentence(sentence: str) -> Sentence:
    print("async describe sentence")
    result = await Runner.run(grammatical_descriptor, sentence)
    return result.final_output

def describe_sentence_sync(sentence: str) -> Sentence:
    return asyncio.run(describe_sentence(sentence))

# print(describe_sentence_sync("I wish I had a horse for my birthday."))