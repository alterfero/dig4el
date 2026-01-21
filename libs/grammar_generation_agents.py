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
    example: List[Example]
    description: str


class Sketch_Chunk(BaseModel):
    focus: str
    description: str
    examples: List[Example]


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


class Sketch(BaseModel):
    """Grammar sketch"""
    title: str
    introduction: str
    sections: List[Sketch_Chunk]


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
    model="gpt-5-2025-08-07",
    instructions="""
    You are an agent answering a user's query about the grammar of a target language 
    based only on the material provided.
    
    INPUT: 
    - The user's query about the grammar of the language, which can contain instructions about how to 
        think about the query and structure an answer. If there is such a part to the query: Follow these instructions. 
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
    - A detailed answer to the user's question, 
    - A list of examples helping the user understand your answer. Example must come from the provided input. 
    Each example consists in a sentence in the target language, a sentence in the source language, and a brief 
    description of what is interesting in this example. 
    - When using a target word or sequence of words within an explanation sentence, surround it with "**"; for example "**'uru**" or "**'ia ora na**".
    
    Example of query: "Does Tahitian use an inclusive/exclusive distinction in pronouns? 
                       INSTRUCTIONS: Adhere to the following framework and thought process:
                       - State if the language uses inclusive vs exclusive forms
                       - Look for the existence of a dual or trial forms. If they exist, present the 
                       interaction between inclusive/exclusive and dual/trial."

    Example of output:
    {
    "Explanation": "Yes, Tahitian uses an inclusive/exclusive distinction in all pronouns.
    In addition, Tahitian also uses a dual, which combines with inclusive and exclusive forms
    to signify, for example, the speaker and the person next to the speaker, but no the person being addressed, 
    as in the following example.",
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
    model="gpt-5-2025-08-07",
    instructions=""" 
    You are an agent specialized in creating grammar teaching material for an endangered language.
    Students are speaking the source language.  
    You are provided with the user's query with optional instructions included, and materials from different sources. 
    Your job is to compile these sources and add your own input to create a grammar lesson about the query.
    You must follow any instructions included in the query, about how to think about, and formulate an answer.
    You output the grammar lesson following the specified schema. 
    
    COMPLY WITH THE FOLLOWING:
    - Do not add information from any other source or from your own knowledge. 
    - Add ALL relevant information from all the available sources.
    - Follow any instructions part of the query.
    - Adapt your output to the type of readers: The output must be in the language and the type readers, adapted to 
    the type of readers, and insist on contrasts between the endangered language and the language of the readers 
    when describing grammar. 
    - All the content of the lesson must come from the provided material. Don't invent anything, don't retrieve
    anything from other sources or general knowledge. 
    - In all examples, translate the source sentence from English to the reader's language. 
    - Avoid metalinguistic jargon. Use everyday words and expressions and periphrases, 
    especially if the indicated audience is young. 
    
    INPUT:
    - Name of the endangered language.
    - Query and optional instructions about how to create a lesson about it. 
    - Type of readers and language fo the readers.
    - List of grammatical parameters and their values in the endangered language, some with examples. 
    - Description coming from sentence analysis.
    - Description coming from a compilation of documents.
    - List of examples, each with its description.
    - List of sentence pairs, some with explicit connections between the concepts in the sentence and words in 
        the endangered language sentence, some with comments, some with a literal English back-translation.
    
    NOTE ON INPUTS: If there are contradictions between inputs, be explicit about it and cite the diverging sources.
        
    OUTPUT: Grammar lesson in the reader's language. The grammar lesson is structured as follows:
    - A title, derived from the user query
    - An introduction paragraph which includes: A summary of language-independent general grammar knowledge about this topic. 
    Then a short description of how this grammar topic is expressed in the 
    language of readers, with examples. Finally, a hint about how the endangered language grammar expresses this topic. 
    The objective of the introduction is to help readers understand the topic, as readers may not me familiar with grammar. 
    - A list of information chunks, which are paragraphs focusing on an aspect of the grammatical topic to cover. 
    Add as many information chunks as needed to cover the topic. Each information chunk includes a title, an explanation 
    of the focus, and several examples retrieved from the corpus (if possible 5). Each example is a sentence in the target language, 
    its translation in the reader's language, and a description of the example with the lens of the grammatical 
    topic studied.
    - A conclusion, which is what the students should absolutely remember. 
    - Drills: sentence pairs that illustrate the topic and that will be used to create exercises. Translate the source
    language in the reader's language if needed. Add ALL relevant examples retrieved from the input. 
    
    NOTE ON OUTPUTS: When using a target word or sequence of words within an explanation sentence, surround it with "**"; for example "**'uru**" or "**'ia ora na**".
    
    """,
    output_type=Lesson
)

lesson_improvement_agent = Agent(
name="lesson_reviewer",
    model="gpt-5-2025-08-07",
    instructions="""
You are given:
- A grammar lesson about an endangered language, formatted as JSON.
- The target audience (e.g., children, beginner adult learners, linguists, teachers).
- The language of the readers, which matches the language used in the provided lesson.

The lesson includes:
- An introduction.
- Several sections, each focusing on a specific grammatical feature.
- A conclusion, which contains the key elements to remember.
- A list of examples.

Your task:
Adapt the content of the lesson EXCEPT EXAMPLES for the specified audience by:
1. Simplifying the language:
   - Replace or rephrase any technical linguistic terms or complex explanations that the audience would not understand.
   - Add explanations and analogies as needed for the audience to understand the lesson.
2. Preserving accuracy:
   - Ensure that all grammatical facts remain correct and faithful to the original.
   - Don't modify examples. 
   - Don't modify any content in the target, taught, language. 
   - Maintain the original structure and JSON format of the lesson.
   - Keep all examples exactly as they are provided. Do not change anything to examples.
NOTE ON OUTPUTS: When using a target word or sequence of words within an explanation sentence, surround it with "**"; for example "**'uru**" or "**'ia ora na**".
Output format:
Return the adapted lesson in the same JSON structure.
    """,
    output_type=Lesson
)

sketch_agent = Agent(
    name="grammar_sketcher",
    model="gpt-5-2025-08-07",
    instructions="""
    You are an agent specialized in creating detailed grammar descriptions to document endangered languages.
    You are provided with a user query with optional instructions, and materials from different sources.
    Your job is to compile these sources to create a grammar sketch that will be used by linguists.

    COMPLY WITH THE FOLLOWING:
    - Do not add information from any other source or from your own knowledge, but use all the reasoning you can to
    perform deductions and inferences based on the sources.
    - If the query contains instruction about how to think about and formulate an answer, follow these instructions.
    - Add ALL relevant information from all the available sources. Be as detailed as possible.
    - The output must be in the language of the readers.
    - In all examples, translate the source sentence from English to the reader's language.

    INPUT:
    - Name of the endangered language.
    - User's query and optional instructions.
    - List of grammatical parameters and their values in the endangered language, some with examples.
    - Description coming from sentence analysis.
    - Description coming from a compilation of documents.
    - List of examples, each with its description.
    - List of sentence pairs, some with explicit connections between the concepts in the sentence and words in
        the endangered language sentence, and explanatory comments.

    NOTE ON INPUTS: If there are contradictions between inputs, be explicit about it and cite the diverging sources.

    OUTPUT: Grammar sketch in the reader's language. The grammar sketch is structured as follows:
    - A title, derived from the user query
    - An introduction paragraph that introduces the grammatical topic provides a robust and detailed overview of
     the behavior of the target language with regard to the grammatical topic at hand.
    - A list of sktech chunks: Each chunk is a focus on an aspect of the grammar topic provided. For example, if the grammar topic is
    "expressing tense", the chunks may focus on "past", "present", "future" and "general" for example. Each chunk is a
    section with information and examples. The list can be as long or as short as needed to describe the grammatical topic.
    Each sketch chunk can include up to 5 examples to illustrate how the target language expresses the grammar topic.
    Each example displays with the sentence in the target language, in the the source language, and an explanation of how this example illustrate the focus.
    - A conclusion, which is what the students should absolutely remember.
    
    NOTE ON OUTPUTS: When using target word(s) within an explanation sentence, surround them with "**"; for example "**'uru**" or "**'ia ora na**".
    
    """,
    output_type=Sketch
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

async def file_search_request(indi_language: str, vsids: list[str], query: str):
    prompt = f"""
    You are an agent specialized in retrieving grammatical information about {indi_language} in the provided documents.
    to answer a user's query. Retrieve all relevant information from the documents and compile them into a detailed 
    answer to the user's query, with examples taken from the documents. 
    - Use only information from the documents. Do not invent any additional information or examples. If there are no relevant 
    information in the documents, just output "no relevant information about the query in the documents". 
    - If the query comes with instructions about how to formulate an answer, follow these instructions. 
    USER QUERY: {query}
    """
    client = openai.OpenAI(api_key=api_key)
    # get vector store
    vs_list = client.vector_stores.list()
    active_vs = [vs for vs in vs_list if vs.id in vsids]
    if active_vs == []:
        print("No vector store with this id")
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


async def create_lesson(indi_language,
                        source_language,
                        query,
                        readers_type,
                        grammatical_params,
                        alterlingua_explanation,
                        alterlingua_examples,
                        doc_contribution,
                        sentence_pairs):
    data = f"""
    ENDANGERED LANGUAGE: {indi_language},
    
    
    READERS: {readers_type} speaking {source_language} language,
    
    
    QUERY: {query}
    
    
    GRAMMATICAL PARAMETERS: {grammatical_params},
    
    
    DESCRIPTION FROM SENTENCE ANALYSIS: {alterlingua_explanation}
    
    
    EXAMPLES FROM SENTENCE ANALYSIS: {alterlingua_examples},
    
    
    DESCRIPTION FROM DOCUMENTS: {doc_contribution},
    
    
    SENTENCE PAIRS: {sentence_pairs}
    """
    result = await Runner.run(lesson_agent, data)
    return result.final_output.dict()

async def review_lesson(lesson, source_language, readers_type):
    data = f"""
    LESSON LANGUAGE = {source_language},
    READERS_TYPE = {readers_type},
    LESSON: {lesson}
    """
    result = await Runner.run(lesson_improvement_agent, data)
    return result.final_output.dict()

async def create_sketch(indi_language, source_language, query, readers_type,
                        grammatical_params,
                        alterlingua_explanation, alterlingua_examples,
                        doc_contribution, sentence_pairs):
    data = f"""
    ENDANGERED LANGUAGE: {indi_language},


    READERS: Linguists speaking {source_language} language,
    
    
    QUERY: {query},


    GRAMMATICAL PARAMETERS: {grammatical_params},


    DESCRIPTION FROM SENTENCE ANALYSIS: {alterlingua_explanation}


    EXAMPLES FROM SENTENCE ANALYSIS: {alterlingua_examples},


    DESCRIPTION FROM DOCUMENTS: {doc_contribution},


    SENTENCE PAIRS: {sentence_pairs}
    """
    result = await Runner.run(sketch_agent, data)
    return result.final_output.dict()
# ===================================== SYNC CALLS ==============================================

def select_parameters_sync(query: str, parameters: list[str]) -> dict:
    return asyncio.run(select_parameters(query, parameters))


def contribute_from_alterlingua_sync(query: str, sentences: list[dict]) -> dict:
    return asyncio.run(contribute_from_alterlingua(query, sentences))


def file_search_request_sync(indi_language: str, vsids: list[str], query: str):
    return asyncio.run(file_search_request(indi_language, vsids, query))

def create_lesson_sync(indi_language,
                       source_language,
                       query,
                       readers_type,
                       grammatical_params,
                       alterlingua_explanation,
                       alterlingua_examples,
                       doc_contribution,
                       sentence_pairs):
    return asyncio.run(create_lesson(indi_language,
                                     source_language,
                                     query,
                                     readers_type,
                                     grammatical_params,
                                     alterlingua_explanation,
                                     alterlingua_examples,
                                     doc_contribution,
                                     sentence_pairs))

def review_lesson_sync(lesson, source_language, readers_type):
    return asyncio.run(review_lesson(lesson, source_language, readers_type))

def create_sketch_sync(indi_language, source_language, query, readers_type,
                       grammatical_params,
                        alterlingua_explanation, alterlingua_examples,
                        doc_contribution, sentence_pairs):
    return asyncio.run(create_sketch(indi_language, source_language, query, readers_type,
                                     grammatical_params,
                                     alterlingua_explanation, alterlingua_examples,
                                     doc_contribution, sentence_pairs))
