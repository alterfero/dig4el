import json
from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np
import pickle
import torch

"""
Implementing Retrieval-Augmented Generation (RAG) to add relevant pairs of sentences from a parallel corpus
to a user LLM prompt.
Functions below allow to:
- generate an embedding for each sentence pair. 
- index these embeddings 
- save and load indexes. 
- use user prompt embedding to select the N most relevant sentences to add to the prompt. 

Uses SentenceTransformers
Sentence Transformers (a.k.a. SBERT) is the go-to Python module for accessing, using, 
and training state-of-the-art embedding and reranker models. 
It can be used to compute embeddings using Sentence Transformer models (quickstart) 
or to calculate similarity scores using Cross-Encoder (a.k.a. reranker) models (quickstart). 
This unlocks a wide range of applications, including semantic search, semantic textual similarity, 
and paraphrase mining.
https://www.sbert.net/
"""

def build_embeddings(sentences, model_name='all-MiniLM-L6-v2', normalize=True):
    """
    Build and return a FAISS index and the embeddings-to-sentence mapping.
    A FAISS index is simply the core data structure Facebook AI’s FAISS library uses to store
    high-dimensional vectors and perform (approximate) nearest-neighbor searches over them.
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(sentences, convert_to_tensor=True)

    return embeddings

def save_embeddings(embeddings, path='embeddings.pkl'):
    with open(path, 'wb') as f:
        pickle.dump(embeddings, f)

def load_embeddings(path='embeddings.pkl'):
    with open(path, 'rb') as f:
        embeddings = pickle.load(f)
    return embeddings

def query_similarity(embeddings, query, model_name='all-MiniLM-L6-v2', top_k=10):
    model = SentenceTransformer(model_name)
    query_embedding = model.encode([query], convert_to_tensor=True)

    # We use cosine-similarity and torch.topk to find the highest 5 scores
    similarity_scores = model.similarity(query_embedding, embeddings)[0]
    scores, indices = torch.topk(similarity_scores, k=top_k)

    return scores, indices

def semantic_search(embeddings, query, model_name='all-MiniLM-L6-v2', top_k=10):
    model = SentenceTransformer(model_name)
    query_embedding = model.encode([query], convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, embeddings, top_k=top_k)
    return hits




