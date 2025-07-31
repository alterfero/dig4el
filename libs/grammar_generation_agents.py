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


class Example(BaseModel):
    target_sentence: str
    source_sentence: str
    description: str


class Description(BaseModel):
    description: str


class Info_Chunk(BaseModel):
    focus: str
    example: Example
    description: Description


class Translation_Drill(BaseModel):
    target: str
    source: str

class Lesson(BaseModel):
    """Grammar lesson"""
    title: str
    introduction: str
    sections: List[Info_Chunk]
    conclusion: str
    translation_drills: List[Translation_Drill]


class Grammar_Parameter(BaseModel):
    parameter: str


class Grammar_Parameter_Selection(BaseModel):
    selection: list[Grammar_Parameter]


class Contribution(BaseModel):
    explanation: str
    examples: list[Example]


Info_Chunk.model_rebuild()
Grammar_Parameter_Selection.model_rebuild()
Contribution.model_rebuild()
Lesson.model_rebuild()



cq_parameter_selector_agent = Agent(
    name="grammar_beliefs_selector",
    model="o4-mini-2025-04-16",
    instructions="""
    You are a grammar expert selecting from a provided list the grammatical parameters best suited to 
    answer a user's query. 
    
    INPUT:  
    - A user query
    - A list of grammatical parameters
    
    OUTPUT: 
    Return the subset of input parameters relevant to answering the user’s query. 
    
    EXAMPLE: 
    User query: “How does Arawak express aspect?”
    Parameters list: ["Is a morphological distinction between perfective and imperfective aspect available on verbs?", 
    “voice”, "The Perfect", "The Past Tense", "Perfective/Imperfective Aspect"]
    
    Expected output: ["Is a morphological distinction between perfective and imperfective aspect available on verbs?", 
    "Perfective/Imperfective Aspect"]    
    """,
    output_type=Grammar_Parameter_Selection)

cq_alterlingua_agent = Agent(
    name="alterlingua_informant",
    model="o4-mini-2025-04-16",
    instructions="""
    You are an agent answering a user's query about the grammar of a target language 
    based only on the material provided.
    
    INPUT: 
    - The user's query about the grammar of the language. 
    - A list of annotated sentences: Each item of the list includes 
        - the source sentence in English, 
        - the target sentence in the target language, 
        - a partial pseudo-gloss called "alterlingua", which adds to target words known information 
        about them when available. "IP" is Internal Particularization, internal information about the concept's
         adaptation to the expression need. "RP" is Relational Particularization, or how the concept connects 
         with others. 
        - comments.
    Example of input item: 
    {
      "source_english": "Well, we\u2019re walking down to the river, over there.",
      "target_raw": "'aita, t\u0113 pou nei m\u0101ua i te pae anavai, i '\u014d",
      "alterlingua": "'aita<> t\u0113<> pou<walking & PROCESSIVE PREDICATE> nei m\u0101ua<Ref_speaker_plus_person_excluding_addressee(IP: | RP:AGENT of walking)> i<river(IP: | RP:OBLIQUE ROLE DESTINATION of walking)> te<> pae<> anavai<river(IP: | RP:OBLIQUE ROLE DESTINATION of walking)> i '\u014d",
      "comment": "pou 'descendre' est employ\u00e9 pour indiquer le mouvement vers le bas (walking down)"
    }
    
    OUTPUT: 
    - A detailed answer to the user's question. 
    - A list of examples helping the user understand your answer. Example must come from the provided input. 
    Each example consists in a sentence in the target language, a sentence in the source language, and a brief 
    description of what is interesting in this example. 
    
    Example of query: "Does Tahitian use an inclusive/exclusive distinction in pronouns?"
    Example of output:
    {
    "Explanation": "Yes, Tahitian uses an inclusive/exclusive distinction in all pronouns. This distinction 
    is associated with the fact that Tahitian also uses dual forms.",
    "Examples": [
        {
        "source_sentence": "Well, we\u2019re walking down to the river, over there."
        "target_sentence": "'aita, t\u0113 pou nei m\u0101ua i te pae anavai, i '\u014d"
        "description": "In this sentence, m\u0101ua refers to the speaker and someone else. If 
        the speaker wanted to refer to himself and his interlocutor, he would have used tāua". 
        }
    ]
    }
    """,
    output_type=Contribution
)

lesson_agent = Agent(
    name="lesson_creator",
    model="o4-mini-2025-04-16",
    instructions=""" 
    You are an agent specialized in creating grammar teaching material for an endangered language.
    Students are speaking the source language.  
    You are provided with materials from different sources. 
    Your job is to compile these sources, and add your own input, to create a grammar lesson following the specified schema. 
    
    COMPLY WITH THE FOLLOWING:
    - Do not add information from any other source or from your own knowledge. 
    - Adapt your output to the type of readers: The output must be in the language and the type readers, adapted to 
    the type of readers, and insist on contrasts between the endangered language and the language of the readers 
    when describing grammar. 
    - All the content of the lesson must come from the provided material. Don't invent anything, don't retrieve
    anything from other sources or general knowledge. 
    - In all examples, translate the source sentence from English to the reader's language. 
    
    INPUT:
    - Name of the endangered language.
    - Type of readers and language fo the readers.
    - List of grammatical parameters and their values in the endangered language, some with examples. 
    - Description coming from sentence analysis.
    - Description coming from a compilation of documents.
    - List of examples, each with its description.
    - List of sentence pairs, some with explicit connections between the concepts in the sentence and words in 
        the endangered language sentence. 
    
    NOTE ON INPUTS: If there are contradictions between inputs, the description coming from the compilation of 
    documents is always considered as the most trustworthy. 
        
    OUTPUT: Grammar lesson in the reader's language. The grammar lesson is structured as follows:
    - A title, derived from the user query
    - An introduction paragraph that introduce the grammatical topic, with a brief summary of language-independent 
    general grammar knowledge about this topic, with examples in the source language and a hint about how the endangered
     language grammar expresses this topic. The objective of the introduction is to help readers understand the 
     topic, as readers may not me familiar with grammar. 
    - A list of information chunks, paragraphs with information and examples. The list can be as long or as short 
    as needed to describe the grammatical topic. Translate the source of example in the reader's language if needed.
    - A conclusion, which is what the students should absolutely remember. 
    - Drills: sentence pairs that illustrate the topic and that will be used to create exercises. Translate the source
    language in the reader's language if needed. 
    
    """,
    output_type=Lesson
)

# ==================================== ASYNC CALLS ================================================


async def select_parameters(query: str, parameters: list[str]) -> dict:
    data = f"Query: {query} --- Parameters: {parameters}"
    result = await Runner.run(cq_parameter_selector_agent, data)
    return result.final_output.dict()


async def contribute_from_alterlingua(query: str, sentences: list[dict]) -> dict:
    data = f"Query: {query} --- Sentences: {sentences}"
    result = await Runner.run(cq_alterlingua_agent, data)
    return result.final_output.dict()

async def file_search_request(indi_language: str, vector_store_names: list[str], query: str):
    prompt = f"""
    You are an agent specialized in retrieving grammatical information about {indi_language} in provided documents.
    to answer a user's query. Retrieve all relevant information from the documents and compile them into a detailed 
    answer to the user's query, with examples taken from the documents. 
    Use only information from the documents. Do not invent any additional information or examples. If there are no relevant 
    information in the documents, just output "no relevant information about the query in the documents". 
    USER QUERY: {query}
    """
    client = openai.OpenAI(api_key=api_key)
    # get vector store
    vs_list = client.vector_stores.list()
    active_vs = [vs for vs in vs_list if vs.name in vector_store_names]
    if active_vs == []:
        print("No vector store with any of these name")
        print(vs_list)
        return None
    else:
        response = client.responses.create(
            model="gpt-4.1",
            input=prompt,
            tools=[{
                "type": "file_search",
                "vector_store_ids": [vector_store.id for vector_store in active_vs]
            }],
            include=["file_search_call.results"]
        )
        return response

async def create_lesson(indi_language, source_language, readers_type,
                        grammatical_params,
                        alterlingua_explanation, alterlingua_examples,
                        doc_contribution, sentence_pairs):
    data = f"""
    ENDANGERED LANGUAGE: {indi_language},
    
    
    READERS: {readers_type} speaking {source_language} language,
    
    
    GRAMMATICAL PARAMETERS: {grammatical_params},
    
    
    DESCRIPTION FROM SENTENCE ANALYSIS: {alterlingua_explanation}
    
    
    EXAMPLES FROM SENTENCE ANALYSIS: {alterlingua_examples},
    
    
    DESCRIPTION FROM DOCUMENTS: {doc_contribution},
    
    
    AUGMENTED SENTENCE PAIRS: {sentence_pairs}
    """
    result = await Runner.run(lesson_agent, data)
    return result.final_output.dict()


# ===================================== SYNC CALLS ==============================================

def select_parameters_sync(query: str, parameters: list[str]) -> dict:
    return asyncio.run(select_parameters(query, parameters))


def contribute_from_alterlingua_sync(query: str, sentences: list[dict]) -> dict:
    return asyncio.run(contribute_from_alterlingua(query, sentences))


def file_search_request_sync(indi_language: str, vector_store_names: list[str], query: str):
    return asyncio.run(file_search_request(indi_language, vector_store_names, query))

def create_lesson_sync(indi_language, source_language, readers_type,
                       grammatical_params,
                        alterlingua_explanation, alterlingua_examples,
                        doc_contribution, sentence_pairs):
    return asyncio.run(create_lesson(indi_language, source_language, readers_type,
                                     grammatical_params,
                                     alterlingua_explanation, alterlingua_examples,
                                     doc_contribution, sentence_pairs))

