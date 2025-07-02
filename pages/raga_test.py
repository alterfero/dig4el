import streamlit as st
import json
from libs import sentence_class_utils as scu
from libs import retrieval_augmented_generation_utils as ragu

import os

if "sentence_pairs" not in st.session_state:
    st.session_state.sentence_pairs = []
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "result" not in st.session_state:
    st.session_state.result = None
if "description_response" not in st.session_state:
    st.session_state.description_response = None
if "description_dict" not in st.session_state:
    st.session_state.description_dict = None
if "description_text" not in st.session_state:
    st.session_state.description_text = None
if "enriched_pairs" not in st.session_state:
    st.session_state.enriched_pairs = None
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "index" not in st.session_state:
    st.session_state.index = None
if "hard_query_result" not in st.session_state:
    st.session_state.hard_query_result = None

def generate_and_save_embeddings_of_source_sentence_list(sentences, embedding_file_path="/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence pairs/embeddings.pkl"):
    embeddings = ragu.build_embeddings(sentences)
    ragu.save_embeddings(embeddings, path=embedding_file_path)
    return embeddings

def load_embeddings(embedding_file_path="/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence pairs/embeddings.pkl"):
    embeddings = ragu.load_embeddings(embedding_file_path)
    return embeddings

def get_similar_entries_with_torch_topk(sentence_pairs, embeddings, query):
    scores, indices = ragu.query_similarity(embeddings, "Future tense")
    print("Similarity")
    for score, idx in zip(scores, indices):
            print(sentence_pairs[idx], f"(Score: {score:.4f})")

def get_similar_entries_with_semantic_search(sentence_pairs, embeddings, query):
    hits = ragu.semantic_search(embeddings, "How to express negation")
    hits = hits[0]      #Get the hits for the first query
    for hit in hits:
        print(sentence_pairs[hit['corpus_id']], "(Score: {:.4f})".format(hit['score']))

# Global variables =============================
BASE_PATH = "/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence_pairs/"

# ========= interface ===========================

st.header("Semantic Retrieval Test")

source_sentence = st.text_input("Sentence description test")
if st.button("Describe"):
    st.session_state.description_response = scu.describe_sentence(source_sentence)
    st.session_state.description_dict = json.loads(st.session_state.description_response.content)
    st.session_state.description_text = scu.description_dict_to_text(st.session_state.description_dict)

if st.session_state.description_dict is not None:
    st.write(st.session_state.description_dict)
if st.session_state.description_text is not None:
    st.write(st.session_state.description_text)
